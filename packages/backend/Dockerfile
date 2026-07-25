# Backend image. Build context is the repo root so the bundled reference engine
# (packages/engine) can be vendored in — see docker-compose.yml.
FROM python:3.11-slim

WORKDIR /app

# Pricing engine (imported via PHASE1_PATH, not pip-installed).
COPY packages/engine /phase1

# Backend package.
COPY packages/backend/pyproject.toml /app/pyproject.toml
COPY packages/backend/app /app/app
RUN pip install --no-cache-dir .

ENV PHASE1_PATH=/phase1
ENV OLEFLIP_DB_PATH=/data/oleflip.db
ENV CORS_ORIGINS=http://localhost:3000

# Run as a non-root user. Create /data (the SQLite volume mount) owned by appuser
# in the image so a fresh named volume inherits writable ownership.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
