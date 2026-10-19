"""
FastGuard — Rate Limiting + IP Banning Middleware for Gems Ore API
===================================================================
Provides:
  • Per-IP sliding-window rate limiter (in-memory, no Redis needed)
  • Static IP ban list (loaded from environment / managed at runtime)
  • Suspicious path detector (blocks common scan patterns)
  • Admin API to view stats, ban/unban IPs at runtime

Usage in main.py:
    from api.middleware.fast_guard import FastGuard, guard_admin_router
    app.add_middleware(FastGuard)
    app.include_router(guard_admin_router)   # mounts under /api/v1 in routes/__init__.py
"""

import os
import time
import ipaddress
from collections import defaultdict, deque
from typing import Set, Dict, Deque

from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from api.utils.jwt_handler import get_current_admin

# ─── Configuration (override via env vars) ────────────────────────────────────

# How many requests a single IP may make within the window
RATE_LIMIT_REQUESTS: int = int(os.getenv("GUARD_RATE_LIMIT_REQUESTS", "120"))
# Sliding window in seconds
RATE_LIMIT_WINDOW: int = int(os.getenv("GUARD_RATE_LIMIT_WINDOW", "60"))

# More aggressive limits for write/auth endpoints
AUTH_RATE_LIMIT_REQUESTS: int = int(os.getenv("GUARD_AUTH_RATE_LIMIT", "20"))
AUTH_RATE_LIMIT_WINDOW: int = int(os.getenv("GUARD_AUTH_RATE_LIMIT_WINDOW", "60"))

UPLOAD_RATE_LIMIT_REQUESTS: int = int(os.getenv("GUARD_UPLOAD_RATE_LIMIT", "10"))
UPLOAD_RATE_LIMIT_WINDOW: int = int(os.getenv("GUARD_UPLOAD_RATE_LIMIT_WINDOW", "60"))

# Auto-ban threshold: IP is auto-banned after this many rate-limit violations
AUTO_BAN_THRESHOLD: int = int(os.getenv("GUARD_AUTO_BAN_THRESHOLD", "5"))

# Comma-separated IP CIDR list that are always whitelisted (localhost, etc.)
_WHITELIST_RAW = os.getenv("GUARD_WHITELIST", "127.0.0.1,::1,0.0.0.0")
WHITELIST_CIDRS = [n.strip() for n in _WHITELIST_RAW.split(",") if n.strip()]

# Comma-separated initial ban list
_BANLIST_RAW = os.getenv("GUARD_BANLIST", "")
INITIAL_BANNED = {ip.strip() for ip in _BANLIST_RAW.split(",") if ip.strip()}

# Suspicious path fragments that indicate scanning/probing
SUSPICIOUS_PATHS = {
    "/.env", "/wp-admin", "/wp-login", "/phpmyadmin", "/phpinfo",
    "/.git", "/admin.php", "/shell", "/xmlrpc", "/.DS_Store",
    "/etc/passwd", "/proc/self", "/../", "/cgi-bin",
}

# ─── In-memory stores ─────────────────────────────────────────────────────────

# { ip: deque([timestamp, ...]) }  — tracks request timestamps per IP per window type
_general_hits: Dict[str, Deque[float]] = defaultdict(deque)
_auth_hits: Dict[str, Deque[float]] = defaultdict(deque)
_upload_hits: Dict[str, Deque[float]] = defaultdict(deque)

# { ip: violation_count }
_violations: Dict[str, int] = defaultdict(int)

# Permanent/temporary bans
_banned_ips: Set[str] = set(INITIAL_BANNED)

# Stats
_guard_stats = {
    "total_requests": 0,
    "blocked_banned": 0,
    "blocked_rate_limit": 0,
    "blocked_suspicious": 0,
    "auto_bans": 0,
}

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _get_client_ip(request: Request) -> str:
    """Extract the real client IP, respecting common reverse-proxy headers."""
    # X-Forwarded-For: client, proxy1, proxy2
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host or "unknown"


def _is_whitelisted(ip: str) -> bool:
    """Return True if ip is in the whitelist (supports CIDR notation)."""
    try:
        addr = ipaddress.ip_address(ip)
        for cidr in WHITELIST_CIDRS:
            try:
                if addr in ipaddress.ip_network(cidr, strict=False):
                    return True
            except ValueError:
                if ip == cidr:
                    return True
    except ValueError:
        pass
    return False


def _sliding_window_check(store: Dict, ip: str, limit: int, window: int) -> bool:
    """
    Sliding-window rate check.
    Returns True if request is ALLOWED, False if rate-limit exceeded.
    """
    now = time.time()
    dq = store[ip]
    # Evict timestamps outside the window
    while dq and now - dq[0] > window:
        dq.popleft()
    if len(dq) >= limit:
        return False
    dq.append(now)
    return True


def _is_suspicious_path(path: str) -> bool:
    lp = path.lower()
    return any(s in lp for s in SUSPICIOUS_PATHS)


def _rate_limit_response(ip: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "status": False,
            "status_code": 429,
            "message": "Too many requests. Please slow down.",
        },
        headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
    )


def _banned_response(ip: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "status": False,
            "status_code": 403,
            "message": "Access denied.",
        },
    )


def _suspicious_response() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": False,
            "status_code": 400,
            "message": "Bad request.",
        },
    )


# ─── Middleware ────────────────────────────────────────────────────────────────


class FastGuard(BaseHTTPMiddleware):
    """
    FastGuard middleware — attach to FastAPI app via:
        app.add_middleware(FastGuard)

    Execution order (first-fail):
      1. Whitelist check  → bypass all guards
      2. IP ban check     → 403
      3. Suspicious path  → 400
      4. Auth rate limit  → 429 (stricter)
      5. Upload rate limit→ 429 (stricter)
      6. General rate     → 429
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        _guard_stats["total_requests"] += 1

        ip = _get_client_ip(request)
        path = request.url.path

        # 1. Whitelist
        if _is_whitelisted(ip):
            return await call_next(request)

        # 2. Banned IP
        if ip in _banned_ips:
            _guard_stats["blocked_banned"] += 1
            return _banned_response(ip)

        # 3. Suspicious path detector
        if _is_suspicious_path(path):
            _guard_stats["blocked_suspicious"] += 1
            # Auto-ban repeated scanners
            _violations[ip] += 3  # suspicious path counts triple
            if _violations[ip] >= AUTO_BAN_THRESHOLD:
                _banned_ips.add(ip)
                _guard_stats["auto_bans"] += 1
                print(f"[FastGuard] Auto-banned {ip} (suspicious path scan)")
            return _suspicious_response()

        # 4. Auth endpoints (stricter window)
        if "/auth/" in path:
            if not _sliding_window_check(_auth_hits, ip, AUTH_RATE_LIMIT_REQUESTS, AUTH_RATE_LIMIT_WINDOW):
                _guard_stats["blocked_rate_limit"] += 1
                _violations[ip] += 1
                if _violations[ip] >= AUTO_BAN_THRESHOLD:
                    _banned_ips.add(ip)
                    _guard_stats["auto_bans"] += 1
                    print(f"[FastGuard] Auto-banned {ip} (auth rate limit exceeded)")
                return _rate_limit_response(ip)

        # 5. Upload endpoints (stricter window)
        elif "/upload" in path:
            if not _sliding_window_check(_upload_hits, ip, UPLOAD_RATE_LIMIT_REQUESTS, UPLOAD_RATE_LIMIT_WINDOW):
                _guard_stats["blocked_rate_limit"] += 1
                _violations[ip] += 1
                if _violations[ip] >= AUTO_BAN_THRESHOLD:
                    _banned_ips.add(ip)
                    _guard_stats["auto_bans"] += 1
                    print(f"[FastGuard] Auto-banned {ip} (upload rate limit exceeded)")
                return _rate_limit_response(ip)

        # 6. General rate limit
        else:
            if not _sliding_window_check(_general_hits, ip, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW):
                _guard_stats["blocked_rate_limit"] += 1
                _violations[ip] += 1
                if _violations[ip] >= AUTO_BAN_THRESHOLD:
                    _banned_ips.add(ip)
                    _guard_stats["auto_bans"] += 1
                    print(f"[FastGuard] Auto-banned {ip} (general rate limit exceeded)")
                return _rate_limit_response(ip)

        response = await call_next(request)

        # Decrement violation counter on successful response (gradual forgive)
        if response.status_code < 400 and _violations[ip] > 0:
            _violations[ip] = max(0, _violations[ip] - 1)

        return response


# ─── Admin API (mount in api_version_one router) ──────────────────────────────

guard_admin_router = APIRouter(
    prefix="/guard",
    tags=["FastGuard Admin"],
    dependencies=[Depends(get_current_admin)],
)


@guard_admin_router.get("/stats")
def get_guard_stats():
    """Return FastGuard runtime statistics."""
    return {
        "status": True,
        "data": {
            **_guard_stats,
            "currently_banned_count": len(_banned_ips),
            "currently_banned": sorted(_banned_ips),
            "active_ips_tracked": len(_general_hits),
            "limits": {
                "general": f"{RATE_LIMIT_REQUESTS} req/{RATE_LIMIT_WINDOW}s",
                "auth": f"{AUTH_RATE_LIMIT_REQUESTS} req/{AUTH_RATE_LIMIT_WINDOW}s",
                "upload": f"{UPLOAD_RATE_LIMIT_REQUESTS} req/{UPLOAD_RATE_LIMIT_WINDOW}s",
            },
        },
    }


@guard_admin_router.post("/ban/{ip}")
def ban_ip(ip: str):
    """Manually ban an IP address."""
    _banned_ips.add(ip)
    print(f"[FastGuard] Manual ban: {ip}")
    return {"status": True, "message": f"IP {ip} banned", "banned": sorted(_banned_ips)}


@guard_admin_router.delete("/ban/{ip}")
def unban_ip(ip: str):
    """Remove an IP from the ban list."""
    _banned_ips.discard(ip)
    _violations.pop(ip, None)
    print(f"[FastGuard] Unban: {ip}")
    return {"status": True, "message": f"IP {ip} unbanned", "banned": sorted(_banned_ips)}


@guard_admin_router.get("/violations")
def get_violations():
    """Return current violation counts per IP."""
    return {
        "status": True,
        "data": dict(sorted(_violations.items(), key=lambda x: -x[1]))
    }


@guard_admin_router.post("/reset-stats")
def reset_stats():
    """Reset runtime statistics (not bans)."""
    for k in _guard_stats:
        _guard_stats[k] = 0
    return {"status": True, "message": "Stats reset"}
