# Quick Start

Five minutes from clone to running demo.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (optional, for containerized run)

## Installation

```bash
# Clone the repo
git clone <repo-url> openenv_scaler
cd openenv_scaler

# Install everything (backend Python deps + frontend npm deps)
make install
```

## Run the demo

```bash
make demo
```

This builds the React frontend, then starts the FastAPI backend at `http://localhost:7860`. The backend serves both the OpenEnv API and the React UI from the same port.

Open `http://localhost:7860` in your browser to see the dashboard.

## Run the tests

```bash
make test
```

Runs **69 backend tests** (calculations, grader, environment, REST API, seed data, data store) and **12 frontend tests** (Dashboard, ScoreCard, NAVBridge).

## Browse the docs

```bash
make docs
```

Serves these docs at `http://localhost:8765`.

## Other targets

```bash
make lint       # ruff lint over the backend
make typecheck  # mypy over the backend
make build      # build React frontend only
make preflight  # full quality gate (lint + typecheck + tests + build)
make clean      # remove caches and build artifacts
```

## Run with Docker

```bash
make build              # build frontend first
npm run docker:build    # build the Docker image
npm run docker:run      # run at http://localhost:27860
```

The Dockerfile is multi-stage: a Node 20 stage builds the React frontend, and a Python 3.11 stage runs uvicorn serving both the API and the built static files.

## Run the baseline agent

The baseline agent uses an OpenAI-compatible client and reads credentials from environment variables.

```bash
# Set credentials
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
export HF_TOKEN=hf_your-token-here

# Make sure the server is running first (e.g., make demo in another terminal)

# Run the agent
npm run inference
```

The script runs all three difficulty tasks and prints the reward for each.

## File layout

```
openenv_scaler/
  Makefile              quick targets (this page)
  inference.py          baseline LLM agent
  openenv.yaml          environment manifest
  Dockerfile            multi-stage build
  README.md             project README (for GitHub)
  EXPLANATION.md        plain-English summary for judges
  packages/
    backend/            Python package (fundlens)
    frontend/           React + Vite SPA
  docs/                 these docs (browse with make docs)
```
