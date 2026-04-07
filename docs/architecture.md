# Architecture

How FundLens fits together.

## Layered view

```
+-----------------------------------------------------------+
|                    React Frontend (Vite)                  |
|     Dashboard, NAV Bridge, Explorer, Agent Runner, Docs   |
+--------------------------+--------------------------------+
                           |
                  REST /api/* + GET /
                           |
+--------------------------v--------------------------------+
|                    FastAPI App (uvicorn)                  |
|                                                           |
|  /api/*       custom REST endpoints for the React UI      |
|  /reset       OpenEnv lifecycle (create_app from openenv) |
|  /step        OpenEnv lifecycle (CallToolAction)          |
|  /state       OpenEnv lifecycle                           |
|  /health      health check                                |
+------+-----------------+----------------------------------+
       |                 |
       |                 |
+------v---------+  +----v--------------------------+
|  REST API      |  |  FundLensEnvironment          |
|  uses _api_    |  |  (MCPEnvironment subclass)    |
|  store         |  |                               |
|  directly      |  |  15 MCP tools registered      |
|                |  |  via FastMCP decorators       |
+------+---------+  +----+--------------------------+
       |                 |
       +--------+--------+
                |
       +--------v---------+
       |   DataStore      |
       |   (in-memory)    |
       |                  |
       |  funds, deals,   |
       |  ownership,      |
       |  cashflows       |
       +--------+---------+
                |
       +--------v----------+
       |   seed_data.py    |
       |                   |
       |  load_easy_task   |
       |  load_medium_task |
       |  load_hard_task   |
       +-------------------+
```

## Monorepo layout

```
openenv_scaler/
  packages/
    backend/
      pyproject.toml         setuptools + ruff + mypy + pytest config
      fundlens/
        __init__.py
        models.py            Pydantic: Fund, Deal, Ownership, Cashflow,
                             FundLensObservation, FundLensState, FundLensAction
        client.py            MCPToolClient subclass
        server/
          app.py             FastAPI: REST API + OpenEnv + static file serving
          environment.py     FundLensEnvironment with 15 MCP tools
          calculations.py    Pure-Python NAV bridge, MOIC, XIRR
          grader.py          Tolerance-based scoring
          seed_data.py       3 difficulty scenarios with realistic fund data
          data_store.py      In-memory store (Funds, Deals, Ownership, Cashflows)
      agents/                Multi-agent specialist system
      tests/                 69 tests across calculations, grader, environment,
                             REST API, seed data, data store

    frontend/
      package.json
      vite.config.js         dev server proxies to backend on :7860
      index.html             DM Serif Display + Plus Jakarta Sans + JetBrains Mono
      src/
        main.jsx
        App.jsx              5-page router (Dashboard, Bridge, Explorer, Agent, Docs)
        index.css            Finance design system (deep blue + emerald)
        components/
          Dashboard.jsx
          NAVBridge.jsx
          FundExplorer.jsx
          AgentRunner.jsx
          DocsPage.jsx
          ScoreCard.jsx
          *.test.jsx         Vitest + React Testing Library

  inference.py               Baseline LLM agent using OpenAI client
  openenv.yaml               Environment manifest (3 tasks)
  Dockerfile                 Multi-stage: Node frontend build + Python runtime
  Makefile                   Quick targets (install, test, demo, docs, ...)
  README.md                  Project README
  EXPLANATION.md             Plain-English summary for judges
  docs/                      These docs
```

## How an agent talks to the environment

```
[ LLM Agent ]
     |
     | 1. POST /reset {"task_id": "easy"}
     v
[ FundLensEnvironment.reset() ]
     |
     | loads seed_data into self._store
     | computes correct answers
     v
[ Returns FundLensObservation with task_description, available_funds, message ]
     |
     | 2. POST /step {"tool_name": "get_nav_bridge", "arguments": {"fund_id": "alpha"}}
     v
[ MCPEnvironment dispatches to the registered tool ]
     |
     | calls compute_nav_bridge(fund_id, store)
     v
[ Returns observation with tool_result containing the 8-line bridge dict ]
     |
     | 3. POST /step {"tool_name": "submit_report", "arguments": {"nav_bridge": {...}}}
     v
[ grade_full_submission compares against correct answers, applies tolerances ]
     |
     v
[ Returns observation with grading_result containing reward in [0.0, 1.0] ]
```

## Tech stack

| Layer    | Tech                                                             |
|----------|------------------------------------------------------------------|
| Backend  | Python 3.11, FastAPI, uvicorn, openenv-core, FastMCP, Pydantic v2 |
| Frontend | React 18, Vite 6, Vitest                                         |
| Lint     | ruff                                                             |
| Types    | mypy                                                             |
| Tests    | pytest, vitest                                                   |
| Docker   | Multi-stage (node:20-slim + python:3.11-slim)                    |
| LLM      | Any OpenAI-compatible endpoint (HuggingFace, OpenAI, z.ai, etc.) |

## Why no scipy/numpy

The Dockerfile aims for a minimal image. The XIRR calculation in `calculations.py` is implemented in pure Python with Newton-Raphson iteration. No scipy, no numpy, no pandas. This keeps the image small and the runtime fast.

## Why MCP tools

The MCP (Model Context Protocol) is the right abstraction for this domain. Agents need to query different views of fund data -- by fund, by deal, by sector, by cashflow type -- and a tool-based interface scales better than a single fat observation. The 15 tools cover everything from raw cashflows to pre-aggregated bridges.
