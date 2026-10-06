# syntax=docker/dockerfile:1
# ── Stage 1: build deps ──────────────────────────────────────────
FROM python:3.11-alpine AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ─────────────────────────────────────────────
FROM python:3.11-alpine AS runtime
LABEL maintainer="javagar-devsecops"

# Non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app
COPY --from=builder /install /usr/local
COPY app.py .

# Remove unnecessary build/wheel artifacts from runtime image to keep attack surface minimal
RUN rm -rf /usr/local/lib/python3.11/site-packages/jaraco* \
           /usr/local/lib/python3.11/site-packages/wheel* \
           /usr/local/lib/python3.11/site-packages/pip* || true

USER appuser
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost:8080/health || exit 1

ENTRYPOINT ["python", "app.py"]
