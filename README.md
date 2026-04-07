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

<div align="center">

# FundLens

**A test environment that grades AI agents on private-equity fund reporting.**

Built for the [Scaler x Meta (PyTorch) 2026 Hackathon](https://meta.com), Round 1.

[Quick Start](#quick-start) ·
[How It Works](#how-it-works) ·
[Project Structure](#project-structure) ·
[Browse the Docs](#browse-the-docs)

</div>

---

## What is this?

FundLens is an [OpenEnv](https://github.com/anthropics/openenv-spec) environment. Think of it as a **test for AI agents**, not an AI itself. You point an LLM agent at it and FundLens grades how well the agent can do real PE fund accounting work — specifically, reconciling NAV bridges (a thing fund analysts spend weeks on every quarter in Excel).

Three things to know:

1. **It is not a model.** It is a graded benchmark. Agents talk to it; it scores them.
2. **The task is real.** NAV bridge reconciliation is genuinely how PE funds report quarterly to LPs.
3. **The grading is deterministic.** Tolerance-based scoring with partial credit, returns a number between `0.0` and `1.0`.

---

## Quick Start

You will need:

- **Python 3.11+**
- **Node.js 20+**
- **Make** (preinstalled on macOS and Linux)

### Run it locally (3 commands)

```bash
make install   # one-time setup
make demo      # builds the UI and starts the server
```

Then open your browser to **http://localhost:7860** and click around.

### Run the tests

```bash
make test
```

You should see **69 backend tests** and **12 frontend tests** all passing.

### Browse the documentation

```bash
make docs
```

Open **http://localhost:8765** for a custom-themed docs site with API reference, architecture diagrams, and the full NAV bridge walkthrough.

> [!TIP]
> Stuck? Run `make` with no arguments to see every available command.

---

## All `make` targets

| Command          | What it does                                                            |
|------------------|-------------------------------------------------------------------------|
| `make install`   | Installs Python (`pip`) and Node (`npm`) dependencies                   |
| `make demo`      | Builds the React UI and starts the server at `localhost:7860`           |
| `make test`      | Runs all backend + frontend tests                                       |
| `make docs`      | Serves the documentation site at `localhost:8765`                       |
| `make build`     | Builds the React frontend bundle only                                   |
| `make lint`      | Runs `ruff` over the backend                                            |
| `make typecheck` | Runs `mypy` over the backend                                            |
| `make preflight` | Full quality gate: lint + typecheck + tests + build                     |
| `make clean`     | Removes caches and build artifacts                                      |

---

## Run with Docker

If you don't want to install Python and Node, run it in Docker instead.

```bash
npm run docker:build
npm run docker:run
```

The server is now at **http://localhost:27860**. Same UI, same API, no local dependencies.

> [!NOTE]
> The host port is `27860` (not `7860`) to avoid colliding with other local services. Inside the container the server still listens on `7860`.

---

## Run the baseline agent

FundLens ships with `inference.py`, a reference agent that drives a real LLM through the environment.

```bash
# 1. Set your LLM credentials (works with any OpenAI-compatible endpoint)
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
export HF_TOKEN=hf_your-token-here

# 2. Make sure the server is running (in another terminal)
make demo

# 3. Run the agent
npm run inference
```

The script runs all three difficulty tasks and prints the reward for each.

---

## How It Works

FundLens gives an AI agent access to a fake PE fund database and asks it to do quarterly reporting work. The agent uses **15 MCP tools** to query funds, deals, ownership, and cashflows, computes the answer, and submits it for grading.

### The 3 difficulty levels

| Level    | Fund(s)                          | What the agent must compute |
|----------|----------------------------------|------------------------------|
| `easy`   | RE Alpha Fund I (3 properties)   | 8-line NAV bridge            |
| `medium` | RE Beta Fund II (5 properties)   | NAV bridge + MOIC            |
| `hard`   | Cross-fund (Alpha + Beta + Gamma, with co-investment) | NAV bridge + MOIC + IRR |

### The 8-line NAV bridge

```
  Beginning NAV       (appraiser value at period start)
+ Contribution        (capital deployed during period)
- Disposition         (proceeds received during period)
+ Income              (rental / operating income during period)
= Cashflow-Adjusted NAV
- Income Reversal     (-Income, removed from valuation)
+/- Write Up/Down     (the plug = Ending NAV - CF-Adj - Income Reversal)
= Ending NAV          (appraiser value at period end)
```

If you find this confusing, that's the point — it's a real-world task that humans get wrong all the time. See [`docs/nav-bridge.md`](docs/nav-bridge.md) for a worked example.

### How an agent talks to the environment

```
1. POST /reset      { task_id: "easy" }
                    -> server loads the scenario and returns an observation

2. POST /step       { tool_name: "get_nav_bridge", arguments: { fund_id: "alpha" } }
                    -> server runs the MCP tool and returns the result

3. POST /step       { tool_name: "submit_report", arguments: { nav_bridge: {...} } }
                    -> server grades the submission and returns a reward in [0.0, 1.0]
```

That's it. No streaming, no callbacks, no long-running episodes. One reset, a few tool calls, one submit.

### Grading

Tolerance-based with partial credit. Get 7 of 8 bridge items right -> reward of `0.875`.

| Item                    | Tolerance         |
|-------------------------|-------------------|
| NAV bridge line amounts | +/- $0.50M        |
| MOIC                    | +/- 0.02x         |
| IRR                     | +/- 1.0% absolute |

| Task     | Bridge weight | Metrics weight       |
|----------|---------------|----------------------|
| `easy`   | 100%          | -                    |
| `medium` | 60%           | 40% (MOIC)           |
| `hard`   | 50%           | 50% (MOIC + IRR)     |

---

## Tech Stack

| Layer    | What we use                                                              |
|----------|--------------------------------------------------------------------------|
| Backend  | Python 3.11, FastAPI, openenv-core, FastMCP, Pydantic v2, uvicorn        |
| Frontend | React 18, Vite 6, custom finance design system (no Tailwind, no MUI)     |
| Numerics | Pure-Python XIRR via Newton-Raphson (no scipy, no numpy, no pandas)      |
| Tests    | pytest (69), vitest (12)                                                 |
| Quality  | ruff (lint), mypy (types)                                                |
| Packaging| npm workspaces, multi-stage Docker (Node 20 + Python 3.11-slim)          |

---

## Project Structure

```
openenv_scaler/
├── Makefile              # quick commands (you are here)
├── inference.py          # baseline LLM agent
├── openenv.yaml          # OpenEnv environment manifest
├── Dockerfile            # multi-stage build
├── README.md             # this file
├── EXPLANATION.md        # plain-English summary for judges
│
├── packages/
│   ├── backend/                      # Python package: `fundlens`
│   │   ├── fundlens/
│   │   │   ├── models.py             # Pydantic models
│   │   │   └── server/
│   │   │       ├── app.py            # FastAPI app + REST + MCP
│   │   │       ├── environment.py    # OpenEnv environment + 15 MCP tools
│   │   │       ├── calculations.py   # NAV bridge, MOIC, XIRR
│   │   │       ├── grader.py         # Tolerance-based scoring
│   │   │       ├── seed_data.py      # 3 deterministic scenarios
│   │   │       └── data_store.py     # In-memory store
│   │   ├── tests/                    # 69 backend tests
│   │   └── pyproject.toml
│   │
│   └── frontend/                     # React + Vite SPA
│       ├── src/
│       │   ├── App.jsx               # 5-page router
│       │   ├── index.css             # finance design system
│       │   └── components/
│       │       ├── Dashboard.jsx
│       │       ├── NAVBridge.jsx
│       │       ├── FundExplorer.jsx
│       │       ├── AgentRunner.jsx
│       │       ├── DocsPage.jsx
│       │       └── ScoreCard.jsx
│       └── vite.config.js
│
└── docs/                             # documentation site (`make docs`)
    ├── index.html                    # docsify entry
    ├── README.md                     # docs landing page
    ├── quick-start.md
    ├── architecture.md
    ├── api.md
    ├── mcp-tools.md
    ├── nav-bridge.md
    └── grading.md
```

---

## Browse the Docs

The complete reference lives in [`docs/`](docs/) and is best browsed with the dev server:

```bash
make docs
```

| Page                                          | What's in it                                       |
|-----------------------------------------------|----------------------------------------------------|
| [Quick Start](docs/quick-start.md)            | Five-minute setup walkthrough                      |
| [Architecture](docs/architecture.md)          | Layered diagram, monorepo layout, agent flow       |
| [HTTP API](docs/api.md)                       | Every endpoint with curl examples                  |
| [MCP Tools](docs/mcp-tools.md)                | All 15 tools and recommended call sequences        |
| [NAV Bridge](docs/nav-bridge.md)              | The 8-line formula explained with a worked example|
| [Grading](docs/grading.md)                    | Tolerances, weights, scoring math                  |

---

## Hackathon Submission

Built for the **Scaler x Meta (PyTorch) 2026 Hackathon, Round 1**. Submission criteria:

| Criterion             | Weight | Where to look                                             |
|-----------------------|--------|-----------------------------------------------------------|
| Real-world utility    | 30%    | The task is literal PE fund analyst work                  |
| Task & grader quality | 25%    | Three honest difficulty levels, deterministic grader      |
| Environment design    | 20%    | Full MCP integration, multi-step agent loop, 15 tools     |
| Code quality & spec   | 15%    | 81 tests, ruff clean, mypy clean, Dockerfile builds       |
| Creativity & novelty  | 10%    | First PE fund reporting benchmark in OpenEnv              |

See [`EXPLANATION.md`](EXPLANATION.md) for the plain-English judges' guide.
