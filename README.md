---
title: FundLens
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
tags:
  - openenv
  - private-equity
  - finance
  - mcp
---

<!--
The YAML block above is HuggingFace Spaces metadata. HF reads it to render
the Space card (title, emoji, gradient) and to know which container port
to expose (7860). It is required for HF deployment but invisible on GitHub.
-->

# FundLens

> A test environment that grades AI agents on private-equity fund reporting.
> Built for the **Scaler × Meta (PyTorch) Hackathon — Round 1**.

FundLens is an [OpenEnv](https://github.com/anthropics/openenv-spec) environment, not a model. You point an LLM agent at it and FundLens scores how well the agent can do real PE quarterly reporting work — specifically, reconciling **8-line NAV bridges** with optional **MOIC + IRR** for cross-fund co-investment.

The task is the same one PE fund analysts spend weeks on every quarter in Excel. The grader is deterministic, tolerance-based, and returns a scalar reward in `[0.0, 1.0]`.

---

## Quick start

```bash
make install   # one-time: Python venv + npm deps
make demo      # builds the React UI and starts the server
```

Open <http://localhost:7860>. The SPA has five views:

| View | What it does |
|---|---|
| **Analyst** | Dashboard / NAV Bridge / Explorer / Agent — read-only inspection of the loaded scenario |
| **Admin** | Manual data entry, xlsx upload, side-by-side AI vs correct comparison, answer-key export |
| **Investor** | Plain-English LP portal: portfolio, NAV walk, ITD summary, properties |
| **Playground** | Drive any of the 15 MCP tools by hand the same way an agent does |
| **Docs** | Tools, formulas, grading reference |

### Other targets

| Command | What it does |
|---|---|
| `make test` | Backend pytest + frontend vitest (87 + 19 = 106 tests) |
| `make lint` / `make typecheck` | ruff / mypy over `packages/backend` |
| `make preflight` | Full quality gate: lint + typecheck + tests + build |
| `make docs` | Standalone docs site at <http://localhost:8765> |
| `make clean` | Remove caches and build artifacts |

### Run with Docker

```bash
npm run docker:build && npm run docker:run
```

Server lands at <http://localhost:27860> (host port `27860` to avoid colliding with other local services; container still listens on `7860`).

### Run the baseline LLM agent

```bash
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
export HF_TOKEN=hf_your-token-here
make demo &       # in another terminal
npm run inference
```

---

## How an agent talks to it

```
POST /reset    {"task_id": "easy"}
               → loads the scenario, returns initial observation
POST /step     {"tool_name": "get_nav_bridge", "arguments": {"fund_id": "alpha"}}
               → server runs the MCP tool and returns the result
POST /step     {"tool_name": "submit_report", "arguments": {"nav_bridge": {…}}}
               → server grades the submission and returns reward ∈ [0, 1]
```

15 MCP tools cover the full **discover → fetch → compute → submit** loop. The Playground view in the SPA exposes them all so you can drive the loop by hand.

## Three difficulty levels

| Level | Funds | Graded items | Total weight |
|---|---|---|---|
| `easy` | Alpha (3 properties, 100% owned) | 8 (bridge only) | bridge 100% |
| `medium` | Beta (5 properties, FX + debt MTM) | 9 (bridge + MOIC) | bridge 60% / MOIC 40% |
| `hard` | Alpha + Beta + Gamma (cross-fund, co-investment) | 10 (bridge + MOIC + IRR) | bridge 50% / MOIC 25% / IRR 25% |

## Grading tolerances

| Metric | Tolerance |
|---|---|
| NAV bridge line amounts | ± $0.50 M |
| MOIC | ± 0.02 x |
| IRR | ± 1.0 % absolute |

Inside the band: full credit for that item. Outside: zero. The final score is the weighted sum, so partial bridges get partial reward — agents always have a gradient.

---

## Tech stack

- **Backend** — Python 3.11, FastAPI, openenv-core, FastMCP, Pydantic v2, uvicorn
- **Frontend** — React 18 + Vite 6, Material Design 3 light-mode design system, MD3 shared-axis transitions
- **Numerics** — pure-Python XIRR via Newton-Raphson (no scipy, no numpy, no pandas)
- **Tests** — pytest (87) + vitest (19)
- **Quality gate** — ruff + mypy clean, multi-stage Docker (Node 20 build → Python 3.11-slim runtime)

## Repo layout

```
packages/backend/fundlens/    # Python package
  server/
    app.py                    # FastAPI: /reset, /step, /state + REST + admin/session routers
    environment.py            # OpenEnv MCPEnvironment + 15 MCP tools
    calculations.py           # NAV bridge, MOIC, pure-Python XIRR
    grader.py                 # tolerance-based grader
    seed_data.py              # 3 deterministic scenarios
  admin/                      # xlsx upload parsing + answer-key export
  tests/                      # 87 backend tests
packages/frontend/src/        # React SPA: 5 personas with their own sub-tabs
inference.py                  # baseline LLM agent (OpenAI-compatible client)
openenv.yaml                  # OpenEnv environment manifest
docs/                         # standalone docs site (`make docs`)
EXPLANATION.md                # plain-English judges' guide
```

## Hackathon submission

Built for **Scaler × Meta (PyTorch) Hackathon, Round 1**. See [`EXPLANATION.md`](EXPLANATION.md) for the plain-English judges' walkthrough — the *why* behind the task, the income-reversal trap, the cross-fund ownership math, and how each rubric criterion is addressed.
