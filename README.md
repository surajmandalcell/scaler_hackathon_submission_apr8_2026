---
title: FundLens
emoji: chart
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
tags:
  - openenv
  - private-equity
  - finance
  - mcp
---

# FundLens -- PE Fund NAV Bridge Environment

FundLens is an **OpenEnv-compliant** environment that tests AI agents on a real, painful problem in private equity: building NAV bridges and computing fund performance metrics from raw deal-level data. Agents interact with a fund database through 15 MCP tools, reconcile beginning-to-ending net asset value across an 8-line bridge, compute MOIC and IRR, and submit a structured report for tolerance-based grading.

This is not a trained model. It is a benchmark environment in the spirit of the OpenEnv project: a reproducible test harness with deterministic seed data, well-defined action and observation spaces, and a grader that returns a scalar reward in `[0.0, 1.0]`.

## The Problem

PE fund analysts spend weeks each quarter reconciling NAV bridges in Excel. Beginning NAV (an appraiser's mark) plus contributions, minus dispositions, plus operating income should -- after a careful adjustment for income reversal and a write-up/down plug -- equal the ending NAV (the next appraiser mark). Doing this correctly across multiple deals, with co-investment ownership splits and dated cashflows feeding an XIRR computation, is exactly the kind of structured-but-tedious work that AI agents should be able to automate.

NAV bridge reconciliation is hard because:

- Cashflows arrive at irregular dates and must be tagged by category (contribution, distribution, income).
- Operating income is included in cashflow-adjusted NAV but must be reversed before computing the appraiser write-up/down -- a double-counting trap.
- Fund-of-fund and co-investment structures introduce ownership percentages that must be applied consistently.
- IRR requires dated cashflows plus a terminal NAV and a numerical solver. Off-by-one errors on dates or signs silently produce wildly wrong answers.

FundLens turns this into a graded task where every line item is either inside the tolerance band or it is not.

## Quick Start

```bash
# Install backend (Python) and frontend (Node) dependencies
npm run install:all

# Run the OpenEnv server (FastAPI + MCP, port 7860)
npm run dev

# In a separate terminal, run the React dev server (port 5173)
npm run dev:frontend

# Run all tests (69 backend + 12 frontend)
npm run test:all

# Build the React frontend bundle
npm run build

# Build and run the Docker image (mapped to host port 27860)
npm run docker:build
npm run docker:run

# Run the baseline LLM agent against the local server
npm run inference
```

The OpenEnv server listens on `http://localhost:7860`. The React UI in dev mode listens on `http://localhost:5173` and proxies API calls to the backend.

## The Environment

### Action Space

Agents interact with the environment by sending `CallToolAction` payloads to `POST /step`. Each action invokes one of 15 MCP tools registered on the FundLens server. The terminal action is `submit_report`, which scores the agent's NAV bridge and metrics against the ground truth.

```json
{
  "tool_name": "get_nav_bridge",
  "tool_args": { "fund_id": "alpha" }
}
```

### Observation Space

Each step returns a `FundLensObservation`:

```json
{
  "result": { "...": "tool response payload" },
  "task_id": "easy",
  "submitted": false,
  "score": null,
  "step_count": 4
}
```

After `submit_report`, the observation includes a per-item breakdown and the final scalar score in `[0.0, 1.0]`.

### Reward

A single scalar in `[0.0, 1.0]` returned on `submit_report`. Partial credit is awarded per graded item: if 7 of 8 NAV bridge lines fall inside the tolerance band, the reward is `0.875`. The grader is deterministic.

## Tasks

| Task | Fund(s) | Properties | Graded items | What the agent computes |
|------|---------|------------|--------------|--------------------------|
| `easy` | RE Alpha Fund I | 3, all 100% owned | 8 | 8-line NAV bridge only |
| `medium` | RE Beta Fund II | 5, all 100% owned | 9 | NAV bridge + MOIC |
| `hard` | RE Alpha + Beta + Gamma (cross-fund) | Co-investment in Prestige Tower (Beta 40%, Gamma 35%) | 10 | NAV bridge + MOIC + IRR |

### The 8-Line NAV Bridge

```
  Beginning NAV       (appraiser value at period start)
+ Contribution        (capital deployed during period)
- Disposition         (proceeds received during period)
+ Income              (rental / operating income during period)
= Cashflow-Adjusted NAV
- Income Reversal     (-Income, removed from valuation)
+/- Write Up/Down     (plug = Ending NAV - CF-Adj - Income Reversal)
= Ending NAV          (appraiser value at period end)
```

### Performance Metrics

- **MOIC** = `(Total Distributions + Unrealized Value) / Total Invested Capital`
- **IRR** = XIRR over dated cashflows plus a terminal NAV value, solved by Newton-Raphson in pure Python (no scipy dependency).

## Grading

The grader applies tolerance bands per item and returns the fraction of items inside their band.

| Item | Tolerance |
|------|-----------|
| NAV bridge line amounts | +/- $0.50M |
| MOIC | +/- 0.02x |
| IRR | +/- 1.0% absolute |

### Scoring Weights

| Task | Bridge weight | Metrics weight |
|------|---------------|----------------|
| `easy` | 100% | -- |
| `medium` | 60% | 40% (MOIC) |
| `hard` | 50% | 50% (MOIC + IRR) |

## MCP Tools

Fifteen tools are exposed via FastMCP. Agents call them through the OpenEnv `/step` endpoint.

| Tool | Purpose |
|------|---------|
| `get_available_filters` | List funds, deals, and date ranges available in the current scenario |
| `get_portfolio_summary` | Top-level portfolio: AUM, deal count, sector mix |
| `get_nav_bridge` | Pre-computed NAV bridge for a specific fund (for verification) |
| `get_irr` | Pre-computed IRR for a fund (for verification) |
| `compare_funds` | Side-by-side comparison of multiple funds |
| `get_sector_report` | Sector-level exposure and performance |
| `get_deal_exposure` | Per-deal ownership percentages and committed capital |
| `get_raw_cashflows` | Raw dated cashflow records (the source of truth) |
| `get_cashflow_summary` | Aggregated cashflows by category and period |
| `get_deal_info` | Deal-level metadata: name, sector, geography, status |
| `get_portfolio_bridge` | Roll-up bridge across multiple funds |
| `get_deal_bridge` | NAV bridge at the deal level |
| `get_deal_metrics` | Deal-level MOIC and IRR |
| `get_portfolio_metrics` | Portfolio-level MOIC and IRR |
| `submit_report` | Submit the agent's final bridge + metrics for grading |

## Architecture

FundLens is a monorepo with a Python backend and a React frontend, glued together by `npm` workspaces and a multi-stage Docker build.

### Tech Stack

| Layer | Stack |
|-------|-------|
| Backend | Python 3.11, FastAPI, openenv-core, FastMCP, Pydantic v2, uvicorn |
| Frontend | React 18, Vite 6, custom finance design system |
| Numerics | Pure-Python XIRR (Newton-Raphson, no scipy) |
| Testing | pytest (69 tests), vitest (12 tests) |
| Packaging | npm workspaces, multi-stage Docker |

### REST API

In addition to the OpenEnv `/reset`, `/step`, `/state`, `/health` endpoints, FundLens exposes a small REST API that the React frontend uses to render fund data.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/reset` | POST | Initialize episode with `task_id` |
| `/step` | POST | Execute MCP tool call (`CallToolAction`) |
| `/state` | GET | Current episode state |
| `/health` | GET | Health check |
| `/api/load-scenario?task_id=easy\|medium\|hard` | POST | Load seed data for the frontend |
| `/api/portfolio` | GET | Fund-level summary |
| `/api/bridge/{fund_id}` | GET | 8-line NAV bridge |
| `/api/deals/{fund_id}` | GET | Deals + ownership |
| `/api/cashflows/{fund_id}` | GET | Cashflow records |
| `/api/sectors` | GET | Sector breakdown |

## Baseline Scores

The repository ships with `inference.py`, a baseline agent that uses the OpenAI client to drive a frontier LLM through the MCP tool loop. To reproduce:

```bash
npm run inference
```

See `inference.py` and the `results.json` artifact for per-episode detail.

## Docker

The Docker image is a multi-stage build: stage 1 compiles the React frontend with Node 20, stage 2 packages the Python backend on `python:3.11-slim` and copies in the built bundle.

```bash
npm run docker:build
npm run docker:run
# Server at http://localhost:27860
```

The host port `27860` is project-specific to avoid collisions with other local services. Inside the container the server still binds to `7860`.

## Project Layout

```
openenv_scaler/
├── packages/
│   ├── backend/                      # Python package: fundlens
│   │   ├── fundlens/
│   │   │   ├── models.py             # Pydantic models
│   │   │   └── server/
│   │   │       ├── app.py            # FastAPI + OpenEnv + MCP
│   │   │       ├── environment.py    # OpenEnv environment
│   │   │       ├── calculations.py   # NAV bridge, MOIC, XIRR
│   │   │       ├── grader.py         # Tolerance-based scoring
│   │   │       ├── seed_data.py      # 3 deterministic scenarios
│   │   │       └── data_store.py     # In-memory store
│   │   ├── tests/                    # 69 backend tests
│   │   └── pyproject.toml
│   └── frontend/                     # React + Vite SPA
│       ├── src/
│       │   ├── App.jsx               # 5-page router
│       │   └── components/
│       │       ├── Dashboard.jsx
│       │       ├── NAVBridge.jsx
│       │       ├── FundExplorer.jsx
│       │       ├── AgentRunner.jsx
│       │       ├── DocsPage.jsx
│       │       └── ScoreCard.jsx
│       └── vite.config.js
├── inference.py                      # Baseline LLM agent
├── openenv.yaml                      # OpenEnv manifest
├── Dockerfile                        # Multi-stage build
├── package.json                      # npm workspaces
├── README.md
└── EXPLANATION.md                    # Plain-English overview for judges
```

## License and Attribution

Built for the **Scaler x Meta (PyTorch) 2026 Hackathon, Round 1**. FundLens is an OpenEnv environment submission focused on real-world utility, task and grader quality, environment design, code quality, and creativity.
