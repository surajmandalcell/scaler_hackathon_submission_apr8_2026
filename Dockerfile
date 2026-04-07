# Stage 1: Build React frontend
FROM node:20-slim AS frontend-build
WORKDIR /build

# Copy frontend package files
COPY packages/frontend/package.json packages/frontend/package-lock.json* /build/packages/frontend/
COPY package.json /build/

# Install dependencies
RUN cd /build/packages/frontend && npm install --ignore-scripts

# Copy source and build
COPY packages/frontend/ /build/packages/frontend/
RUN cd /build/packages/frontend && npm run build


# Stage 2: Python runtime with backend + built frontend
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies (leverage layer cache)
COPY packages/backend/pyproject.toml /app/packages/backend/
RUN pip install --no-cache-dir \
    "openenv-core>=0.2.3" \
    "fastmcp>=3.1.1" \
    "pydantic>=2.0" \
    "fastapi" \
    "uvicorn" \
    "openai" \
    "httpx"

# Copy backend source code
COPY packages/backend/ /app/packages/backend/

# Install the fundlens package itself in editable mode
RUN pip install --no-cache-dir -e /app/packages/backend

# Copy built frontend from stage 1
COPY --from=frontend-build /build/packages/frontend/dist /app/packages/frontend/dist

# Copy root files
COPY inference.py openenv.yaml README.md /app/

EXPOSE 7860

WORKDIR /app/packages/backend

CMD ["uvicorn", "fundlens.server.app:app", "--host", "0.0.0.0", "--port", "7860"]
