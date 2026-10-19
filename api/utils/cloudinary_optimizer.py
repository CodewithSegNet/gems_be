"""
Cloudinary URL Optimizer for Gems Ore
======================================
Injects Cloudinary transformation parameters into image URLs at serve time.
No re-upload required — Cloudinary processes transforms on-the-fly and
CDN-caches the result globally.

Transformations applied:
  • f_auto   — serve WebP/AVIF automatically based on browser support
  • q_auto   — Cloudinary picks optimal quality (typically 60-80 for photos)
  • w_{width} — responsive width cap
  • c_limit  — only downscale, never upscale (preserves small images)
  • dpr_auto — device-pixel-ratio aware (retina screens get 2x via CDN hints)

Usage:
    from api.utils.cloudinary_optimizer import optimize_image_url, optimize_product

    # Single URL
    url = optimize_image_url(raw_url, width=800)

    # Full product dict (mutates images list in place)
    optimized_product = optimize_product(product_dict, thumb_width=400, full_width=1200)
"""

import re

# Cloudinary upload URL pattern
# https://res.cloudinary.com/<cloud>/image/upload/<optional-version>/<rest>
_CLD_UPLOAD_RE = re.compile(
    r"(https://res\.cloudinary\.com/[^/]+/image/upload/)(v\d+/)?(.+)"
)

# Default responsive widths used in the storefront
THUMB_WIDTH = 400     # grid cards, product thumbnails
FULL_WIDTH = 1200     # product detail / lightbox
BANNER_WIDTH = 1920   # hero / full-width banners


def _inject_transform(url: str, transform: str) -> str:
    """
    Insert a Cloudinary transform string into an upload URL.
    If the URL already has a transform segment (letters only before the path),
    it replaces it so we don't stack transforms on every request.

    Example input:
      https://res.cloudinary.com/dn7q2nlxt/image/upload/v1700000000/gems-ore/abc.jpg

    Example output (transform="f_auto,q_auto,w_800,c_limit"):
      https://res.cloudinary.com/dn7q2nlxt/image/upload/f_auto,q_auto,w_800,c_limit/v1700000000/gems-ore/abc.jpg
    """
    m = _CLD_UPLOAD_RE.match(url)
    if not m:
        return url  # Not a Cloudinary URL — return as-is

    base = m.group(1)         # .../image/upload/
    version = m.group(2) or ""  # v1700000000/ or ""
    rest = m.group(3)         # gems-ore/abc.jpg

    # If there's already a transform injected by us, strip it
    # (detect: segment with commas and underscores = transform params)
    first_segment = rest.split("/")[0]
    if "," in first_segment or first_segment.startswith(("f_", "q_", "w_", "c_", "dpr_")):
        rest = "/".join(rest.split("/")[1:])

    return f"{base}{transform}/{version}{rest}"


def optimize_image_url(url: str | None, width: int = THUMB_WIDTH) -> str | None:
    """
    Return an optimized Cloudinary URL for the given raw URL.
    Falls back to the original URL if it's not a Cloudinary asset.
    """
    if not url:
        return url
    transform = f"f_auto,q_auto,w_{width},c_limit,dpr_auto"
    return _inject_transform(url, transform)


def optimize_thumb(url: str | None) -> str | None:
    """Thumbnail size (grid cards) — 400px wide."""
    return optimize_image_url(url, THUMB_WIDTH)


def optimize_full(url: str | None) -> str | None:
    """Full detail size (product page) — 1200px wide."""
    return optimize_image_url(url, FULL_WIDTH)


def optimize_banner(url: str | None) -> str | None:
    """Banner / hero size — 1920px wide."""
    return optimize_image_url(url, BANNER_WIDTH)


def optimize_images_list(images: list, width: int = THUMB_WIDTH) -> list:
    """
    Optimize a list of image dicts (each has 'image_url').
    Returns a new list with optimized URLs plus an additional 'thumb_url' key.
    """
    result = []
    for img in images:
        raw_url = img.get("image_url", "")
        result.append({
            **img,
            "image_url": optimize_image_url(raw_url, width=FULL_WIDTH),
            "thumb_url": optimize_thumb(raw_url),
        })
    return result


def optimize_product(product_dict: dict) -> dict:
    """
    Return a copy of a product dict with optimized Cloudinary URLs.
    - images[].image_url  → full-res optimized (w_1200)
    - images[].thumb_url  → thumbnail (w_400)
    - image (primary)     → thumbnail size for lists
    """
    p = dict(product_dict)
    raw_images = p.get("images", [])

    p["images"] = optimize_images_list(raw_images, width=FULL_WIDTH)
    # Primary image convenience field — use thumb for listing pages
    if raw_images:
        p["image"] = optimize_thumb(raw_images[0].get("image_url"))
    return p
