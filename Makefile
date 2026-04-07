.DEFAULT_GOAL := help

# ── Paths ─────────────────────────────────────────────────────────────────
BACKEND   := packages/backend
FRONTEND  := packages/frontend
VENV      := $(BACKEND)/.venv

# Use absolute venv paths so `cd` in sub-targets still finds the venv
VENV_ABS  := $(CURDIR)/$(VENV)
PYTHON    := $(VENV_ABS)/bin/python
UVICORN   := $(VENV_ABS)/bin/uvicorn
PYTEST    := $(VENV_ABS)/bin/pytest
RUFF      := $(VENV_ABS)/bin/ruff
MYPY      := $(VENV_ABS)/bin/mypy

PORT_BACKEND ?= 7860
PORT_DOCS    ?= 8765

# ── Help ──────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  FundLens -- PE Fund NAV Bridge Environment"
	@echo "  -------------------------------------------"
	@echo ""
	@echo "  make install    Create Python venv + install backend, install frontend npm deps"
	@echo "  make dev        Run backend with auto-reload at http://localhost:$(PORT_BACKEND)"
	@echo "  make build      Build the React frontend for production"
	@echo "  make demo       Build frontend, then serve backend + SPA at :$(PORT_BACKEND)"
	@echo "  make test       Run backend pytest + frontend vitest"
	@echo "  make lint       Run ruff over packages/backend"
	@echo "  make typecheck  Run mypy over packages/backend"
	@echo "  make preflight  lint + typecheck + test + build (full quality gate)"
	@echo "  make docs       Serve project documentation at http://localhost:$(PORT_DOCS)"
	@echo "  make clean      Remove caches and build artifacts"
	@echo ""

# ── Install ───────────────────────────────────────────────────────────────
install:
	@echo "→ Creating Python venv at $(VENV)"
	@python3 -m venv $(VENV)
	@echo "→ Bootstrapping pip (venv may be uv-provisioned without pip)"
	@$(PYTHON) -m ensurepip --upgrade 2>/dev/null || true
	@echo "→ Installing backend in editable mode with dev extras"
	@$(PYTHON) -m pip install --upgrade pip setuptools wheel
	@$(PYTHON) -m pip install -e '$(BACKEND)[dev]'
	@echo "→ Installing frontend npm deps"
	@cd $(FRONTEND) && npm install

# ── Backend dev server ────────────────────────────────────────────────────
dev:
	@echo "→ Backend dev (auto-reload) at http://localhost:$(PORT_BACKEND)"
	@cd $(BACKEND) && $(UVICORN) fundlens.server.app:app --host 0.0.0.0 --port $(PORT_BACKEND) --reload

# ── Build frontend ────────────────────────────────────────────────────────
build:
	@echo "→ Building React frontend"
	@cd $(FRONTEND) && npm run build

# ── Demo (prod build served by backend) ───────────────────────────────────
demo: build
	@echo ""
	@echo "  FundLens demo running at http://localhost:$(PORT_BACKEND)"
	@echo "  Press Ctrl+C to stop."
	@echo ""
	@cd $(BACKEND) && $(UVICORN) fundlens.server.app:app --host 0.0.0.0 --port $(PORT_BACKEND)

# ── Tests ─────────────────────────────────────────────────────────────────
test: test-backend test-frontend

test-backend:
	@cd $(BACKEND) && $(PYTEST) tests/ -v

test-frontend:
	@cd $(FRONTEND) && npm test -- --run

# ── Lint / typecheck ──────────────────────────────────────────────────────
lint:
	@cd $(BACKEND) && $(RUFF) check fundlens/

lint-fix:
	@cd $(BACKEND) && $(RUFF) check --fix fundlens/
	@cd $(BACKEND) && $(RUFF) format fundlens/

typecheck:
	@cd $(BACKEND) && $(MYPY) fundlens/

preflight: lint typecheck test build
	@echo ""
	@echo "  ✓ Preflight passed. Safe to ship."
	@echo ""

# ── Docs site ─────────────────────────────────────────────────────────────
docs:
	@echo ""
	@echo "  FundLens docs running at http://localhost:$(PORT_DOCS)"
	@echo "  Press Ctrl+C to stop."
	@echo ""
	@cd docs && python3 -m http.server $(PORT_DOCS)

# ── Clean ─────────────────────────────────────────────────────────────────
clean:
	rm -rf $(FRONTEND)/dist
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .mypy_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +

.PHONY: help install dev build demo test test-backend test-frontend lint lint-fix typecheck preflight docs clean
