FROM python:3.12-slim

# 1. Set environment flags early
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 2. Install system dependencies (postgresql-client provides psql for seeding)
RUN apt-get update && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 3. Install Python dependencies (cached layer)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --cache-dir /root/.cache/pip --retries 10 --timeout 300 -r requirements.txt

# 3. Create non-root user
RUN addgroup --system appgroup && adduser --system --group appuser

# 4. Copy app code with proper ownership
COPY --chown=appuser:appgroup . .

# Ensure runtime directories exist and are writable by appuser
RUN mkdir -p /app/tmp/media /app/media && chown -R appuser:appgroup /app

# 5. Switch to unprivileged user
USER appuser

EXPOSE 7001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7001"]
