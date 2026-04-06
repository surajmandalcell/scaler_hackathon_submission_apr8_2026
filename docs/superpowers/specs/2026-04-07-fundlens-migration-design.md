# FundLens Migration & React Frontend Design

## Context

Migrating from FridgeEnv (food waste RL benchmark) to FundLens (PE fund NAV bridge benchmark) as the primary submission for Scaler x Meta (PyTorch) 2026 Hackathon. FundLens scores higher on 55% of the judging criteria (task quality, environment design, creativity) due to harder agent challenge, full MCP compliance via openenv-core, and original financial domain.

The migration involves:
1. Restructuring FundLens into the existing `packages/backend` + `packages/frontend` monorepo
2. Replacing Gradio dashboards with a React frontend using a finance-appropriate design system
3. Adding code quality infrastructure (ruff, mypy, expanded tests)
4. Ensuring all pass/fail submission gates are met

**Deadline: April 8, 2026 at 11:59 PM**

---

## Project Structure

```
openenv_scaler/
  package.json                 npm workspaces orchestrator
  inference.py                 FundLens baseline agent (root-level, mandatory)
  openenv.yaml                 FundLens manifest (3 tasks)
  Dockerfile                   Multi-stage (Node build + Python runtime)
  README.md                    FundLens documentation
  EXPLANATION.md               Plain-English hackathon context
  .env.example                 Template (no real keys)
  .gitignore                   Updated for Python + Node

  packages/
    backend/
      pyproject.toml            Package config + ruff + mypy
      fundlens/                 Python package
        __init__.py
        models.py               Pydantic domain + OpenEnv models
        client.py               MCPToolClient wrapper
        server/
          app.py                FastAPI + static file serving (no Gradio)
          environment.py        15 MCP tools (unchanged logic)
          calculations.py       XIRR, NAV bridge, metrics (unchanged)
          grader.py             Tolerance-based scoring (unchanged)
          seed_data.py          3 difficulty scenarios (unchanged)
          data_store.py         In-memory + SQLite (unchanged)
      agents/                   Multi-agent system (moved from fundlens/agents/)
      tests/                    Expanded test suite

    frontend/
      package.json              @fundlens/frontend
      index.html
      vite.config.js
      src/
        main.jsx
        App.jsx                 Router: Dashboard | NAVBridge | Explorer | AgentRunner | Docs
        index.css               Finance design system
        components/
          Dashboard.jsx         Portfolio overview + difficulty selector + score
          NAVBridge.jsx          8-line bridge viewer with explanations
          FundExplorer.jsx       Deals, cashflows, sectors by fund
          AgentRunner.jsx       Run baseline, show tool calls + grading
          DocsPage.jsx          API reference + grading tolerances
          ScoreCard.jsx         Reward display with per-item breakdown
```

---

## Design System

**Palette:**
- `--bg: #0b0f19` / `--bg-raised: #111827` / `--bg-surface: #1f2937`
- `--accent: #10b981` (emerald -- growth/money)
- `--accent-blue: #3b82f6` (trust/data)
- `--danger: #ef4444` / `--warn: #f59e0b`
- Text: `#f1f5f9` / `#94a3b8` / `#64748b` / `#475569`
- Lines: `#1e293b` / `#334155`

**Typography:**
- Display: `"DM Serif Display", Georgia, serif`
- Body: `"Plus Jakarta Sans", system-ui, sans-serif`
- Data: `"JetBrains Mono", monospace`

**Motifs:**
- Left-border accent bars on cards
- Emerald glow on positive values, red on negative
- Large metric numbers with small labels below
- Restrained animations (enter fade, number transition)

---

## Frontend Pages

### Dashboard (default view)
- Header: "FundLens" title + hackathon subtitle
- Difficulty toggle: Easy / Medium / Hard buttons
- "Load Scenario" button -> POST /reset with task_id
- Fund cards: name, NAV movement (beginning -> ending), MOIC badge, IRR badge
- Mode indicator: what gets graded at current difficulty
- Score section: appears after agent run

### NAV Bridge
- Fund selector dropdown
- 8-row table: Step | Amount ($M) | Explanation
- Additions green-tinted, subtractions red-tinted, totals bold
- Subtotal rows (cashflow_adjusted_nav, ending_nav) highlighted

### Explorer
- Fund selector -> deals table (property, sector, location, ownership%, capital, returns)
- Sector breakdown cards
- Cashflow summary per fund

### Agent Runner
- "Run Agent" button -> calls /reset then iterates /step
- Step log: tool_name + arguments + result (scrollable)
- Final grading card: per-item scores
- Reward prominently displayed

### Docs
- API endpoints table
- Data model schemas (Fund, Deal, Ownership, Cashflow)
- Grading tolerances table
- NAV bridge formula walkthrough

---

## Backend Changes

### app.py rewrite
- Remove Gradio imports and mounts
- Add StaticFiles mount for React build at `/`
- Add REST API endpoints for frontend:
  - `GET /api/portfolio` -- portfolio summary
  - `GET /api/bridge/{fund_id}` -- NAV bridge
  - `GET /api/deals/{fund_id}` -- deals + ownership
  - `GET /api/cashflows/{fund_id}` -- cashflow summary
  - `GET /api/sectors` -- sector report
  - `GET /api/exposure/{deal_id}` -- cross-fund exposure
  - `POST /api/run-agent` -- run baseline with step-by-step results

These wrap existing MCP tool logic -- no new calculations.

### Dependencies removed
- `gradio` (no longer needed)

### Dependencies added (pyproject.toml)
- `ruff` (dev)
- `mypy` (dev)
- `pytest`, `pytest-asyncio`, `pytest-cov` (dev)

---

## Files Deleted
- `fundlens/admin/` (Gradio admin)
- `fundlens/investor/` (Gradio investor)
- Old FridgeEnv: `packages/backend/env/`, `packages/backend/agents/`, `packages/backend/app.py`
- Old FridgeEnv frontend components
- Old `inference.py` (FridgeEnv version)
- Old `openenv.yaml` (FridgeEnv version)
- Old `README.md`, `EXPLANATION.md` (FridgeEnv versions)

## Files Preserved (moved)
- `fundlens/server/*` -> `packages/backend/fundlens/server/*`
- `fundlens/models.py` -> `packages/backend/fundlens/models.py`
- `fundlens/client.py` -> `packages/backend/fundlens/client.py`
- `fundlens/agents/*` -> `packages/backend/agents/*`
- `fundlens/tests/*` -> `packages/backend/tests/*`

## Environment Variables (reused from .env)
- `API_BASE_URL` -- LLM endpoint
- `OPENAI_API_KEY` -- API key (rename from existing)
- `MODEL_NAME` -- model identifier
- `ENV_SERVER_URL` -- local server URL (default http://localhost:7860)
- `HF_TOKEN` -- HuggingFace token

---

## Verification

1. `npm run preflight` -- lint + typecheck + all tests + build
2. Docker: `docker build -t fundlens . && docker run -p 27860:7860 fundlens`
3. Manual: visit UI, load all 3 difficulties, verify NAV bridge displays correctly
4. Inference: `npm run inference` completes all 3 tasks with scores
5. Endpoints: `/health` returns 200, `/reset` returns observation, `/step` returns reward
