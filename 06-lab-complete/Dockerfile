# ============================================================
# Dockerfile production (tiêu chí 1 + 3): multi-stage, non-root,
# HEALTHCHECK, CMD dùng $PORT, uvicorn là PID 1 để SIGTERM graceful.
# ============================================================
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ──
FROM python:3.12-slim

RUN groupadd -r agent && useradd -r -g agent agent

WORKDIR /app
COPY --from=builder /install /usr/local
COPY app ./app
COPY utils ./utils

RUN chown -R agent:agent /app
USER agent

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:'+__import__('os').environ.get('PORT','8000')+'/health', timeout=2).status==200 else 1)"

CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
