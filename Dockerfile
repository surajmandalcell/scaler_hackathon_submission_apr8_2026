FROM python:3.11-slim AS base

WORKDIR /app

# Install uv for fast, reproducible Python dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Python dependencies (cached layer)
COPY packages/backend/pyproject.toml packages/backend/uv.lock* packages/backend/
RUN cd packages/backend && uv sync --frozen --no-dev --no-editable 2>/dev/null || \
    cd packages/backend && uv sync --no-dev

# Node.js for frontend build
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# Frontend build (cached layer)
COPY packages/frontend/package.json packages/frontend/package-lock.json* packages/frontend/
RUN cd packages/frontend && npm ci 2>/dev/null || cd packages/frontend && npm install

COPY packages/frontend/ packages/frontend/
RUN cd packages/frontend && npm run build

# Application code
COPY packages/backend/ packages/backend/
COPY openenv.yaml inference.py ./

EXPOSE 7860

WORKDIR /app/packages/backend
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
