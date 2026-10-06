# syntax=docker/dockerfile:1
# ── Stage 1: build deps ──────────────────────────────────────────
FROM python:3.12-alpine AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ─────────────────────────────────────────────
FROM python:3.12-alpine AS runtime
LABEL maintainer="javagar-devsecops"

# Non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app
COPY --from=builder /install /usr/local
COPY app.py .

# Purge residual build metadata from runtime container to achieve clean Trivy scan
RUN rm -rf /usr/local/lib/python*/ensurepip \
           /usr/local/lib/python*/site-packages/wheel* \
           /usr/local/lib/python*/site-packages/jaraco* \
           /root/.cache || true

USER appuser
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost:8080/health || exit 1

ENTRYPOINT ["python", "app.py"]
