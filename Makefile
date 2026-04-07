.DEFAULT_GOAL := help

PORT_BACKEND ?= 7860
PORT_DOCS    ?= 8765

help:
	@echo ""
	@echo "  FundLens -- PE Fund NAV Bridge Environment"
	@echo "  -------------------------------------------"
	@echo ""
	@echo "  make install   Install backend (pip) and frontend (npm) dependencies"
	@echo "  make test      Run all backend + frontend tests"
	@echo "  make build     Build the React frontend for production"
	@echo "  make demo      Build frontend and run the app at http://localhost:$(PORT_BACKEND)"
	@echo "  make docs      Serve project documentation at http://localhost:$(PORT_DOCS)"
	@echo "  make lint      Run ruff lint over the backend"
	@echo "  make typecheck Run mypy over the backend"
	@echo "  make preflight Lint, typecheck, test, and build (full quality gate)"
	@echo "  make clean     Remove caches and build artifacts"
	@echo ""

install:
	npm run install:all

test:
	npm run test:all

lint:
	npm run lint

typecheck:
	npm run typecheck

build:
	npm run build

preflight:
	npm run preflight

demo: build
	@echo ""
	@echo "  FundLens demo running at http://localhost:$(PORT_BACKEND)"
	@echo "  Press Ctrl+C to stop."
	@echo ""
	@npm run dev

docs:
	@echo ""
	@echo "  FundLens docs running at http://localhost:$(PORT_DOCS)"
	@echo "  Press Ctrl+C to stop."
	@echo ""
	@cd docs && python3 -m http.server $(PORT_DOCS)

clean:
	rm -rf packages/frontend/dist
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .mypy_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +

.PHONY: help install test lint typecheck build preflight demo docs clean
