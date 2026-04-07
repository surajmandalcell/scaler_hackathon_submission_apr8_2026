# FundLens -- Plain-English Explanation

A fast read for judges. Skip the README if you only have five minutes.

## What is this project?

FundLens is an **OpenEnv environment**. That means it is a test harness for AI agents -- a server that exposes an action space, an observation space, and a grader, so that any agent (LLM-driven, RL-trained, or hand-coded) can be evaluated against the same task in a reproducible way.

It is **not a trained model**. There are no weights, no fine-tuning artifacts, no reinforcement learning checkpoints. The submission is the environment itself: the seed data, the API surface, the grader, and a baseline agent that demonstrates the loop end-to-end.

The environment lives behind a FastAPI server that conforms to the OpenEnv `/reset`, `/step`, `/state`, `/health` contract, and additionally exposes a fund database via 15 MCP (Model Context Protocol) tools.

## What do agents do?

Agents play the role of a private equity fund analyst preparing a quarterly NAV report. On `/reset` they receive a task (`easy`, `medium`, or `hard`) which loads a deterministic fund scenario into the server. They then issue MCP tool calls through `/step` to:

1. **Discover** what funds, deals, and date ranges exist (`get_available_filters`, `get_portfolio_summary`).
2. **Pull raw data** -- dated cashflows, deal metadata, ownership percentages (`get_raw_cashflows`, `get_deal_info`, `get_deal_exposure`).
3. **Compute** the 8-line NAV bridge for the period: beginning NAV plus contributions, minus dispositions, plus income, minus income reversal, plus a write-up/down plug, equals ending NAV.
4. **Compute** performance metrics where required: MOIC for medium tasks, MOIC + IRR for hard tasks.
5. **Submit** the report via the `submit_report` tool, which terminates the episode and returns a scalar score.

The agent never trains, never sees the answer key during the episode, and gets one submission per episode.

## Why is this problem real?

PE fund analysts spend weeks per quarter building NAV bridges in Excel. The math is not algorithmically deep -- it is structured arithmetic over dated cashflows -- but it is brittle. The most common production bug is double-counting operating income: it gets included in cashflow-adjusted NAV, and then it has to be reversed before computing the appraiser's write-up/down. Forget the reversal and you book your income twice.

Cross-fund and co-investment deals make it worse. If two funds each own 40% and 35% of the same property, every cashflow has to be split before it lands in either fund's bridge. IRR adds a numerical wrinkle: it requires solving a polynomial root over dated cashflows plus a terminal NAV value, which means an off-by-one on a date or a sign flip on a distribution silently produces an answer that looks reasonable but is wrong by hundreds of basis points.

This is precisely the work that a tool-using LLM agent should be able to automate. FundLens makes it measurable.

## How does scoring work?

Tolerance-based, deterministic, scalar in `[0.0, 1.0]`.

- Each NAV bridge line item is graded against a +/- $0.50M tolerance.
- MOIC is graded against a +/- 0.02x tolerance.
- IRR is graded against a +/- 1.0% absolute tolerance.

Inside the band: full credit for that item. Outside: zero credit. The final score is the weighted sum.

| Task | Bridge | Metrics | Total items |
|------|--------|---------|-------------|
| easy | 100% | -- | 8 |
| medium | 60% | 40% (MOIC) | 9 |
| hard | 50% | 50% (MOIC + IRR) | 10 |

Partial credit is intentional. Agents that get most of the bridge right but miss one line item still receive proportional reward, which gives gradient to anyone optimizing against the environment.

## What makes this challenging?

- **The income-reversal trap.** Naive agents add operating income to cashflow-adjusted NAV and forget to subtract it before computing the write-up/down plug. The bridge then fails to balance and the plug absorbs the error silently.
- **XIRR.** IRR over dated cashflows requires Newton-Raphson iteration. We ship a pure-Python implementation so the environment has zero numeric dependencies, but the agent has to either replicate that math or trust the right tool. The terminal NAV must be included as a final positive cashflow on the period end date -- a step that is easy to forget.
- **Cross-fund ownership.** In the hard task, Prestige Tower is co-owned by two funds (40% Beta, 35% Gamma). Every cashflow against Prestige Tower has to be scaled by the right ownership percentage before it lands in either fund's bridge.
- **Tool selection under uncertainty.** With 15 MCP tools, the agent has to choose between calling the pre-computed convenience tools (`get_nav_bridge`, `get_irr`) or assembling the bridge itself from raw cashflows. The grader does not care which path is taken, but agents that blindly trust the convenience tools without sanity-checking against raw data can get tripped up by their own tool sequencing.
- **Scale.** The seed scenarios are small enough to debug, but the data store is structured to handle 100k+ cashflow rows so the environment generalizes to realistic fund sizes.

## What judges evaluate

The hackathon brief weights five criteria. Here is how FundLens maps to each.

| Criterion | Weight | How FundLens addresses it |
|-----------|--------|---------------------------|
| Real-world utility | 30% | NAV bridge reconciliation is a quarterly bottleneck for every PE fund. The 8-line bridge in this environment is the same one analysts build in Excel today. |
| Task and grader quality | 25% | Deterministic seed data, three difficulty tiers (8, 9, 10 graded items), tolerance bands chosen to match real analyst review thresholds, partial credit per item, 69 backend tests covering calculations, grader, and API. |
| Environment design | 20% | OpenEnv-compliant `/reset`, `/step`, `/state`, `/health`. 15 MCP tools cover the full discover-fetch-compute-submit loop. Pydantic v2 models enforce a strict schema on every action and observation. A REST API and React frontend let humans inspect the same data the agent sees. |
| Code quality and spec | 15% | Monorepo with `npm` workspaces, multi-stage Docker, pyproject + pytest + ruff + mypy, vitest for the frontend, deterministic seed data, no scipy or pandas dependencies in the numeric core. |
| Creativity and novelty | 10% | A pure-Python XIRR solver, a finance-themed React frontend that doubles as a debugging interface, three difficulty tiers that introduce co-investment ownership splits at the hardest level. |

## How to run it yourself

```bash
npm run install:all      # install backend + frontend deps
npm run dev              # FastAPI + OpenEnv + MCP at :7860
npm run dev:frontend     # React UI at :5173 (proxies to backend)
npm run test:all         # 69 backend tests + 12 frontend tests
npm run inference        # baseline LLM agent run
npm run docker:build && npm run docker:run    # container at :27860
```

## Technical highlights

- **Pure-Python XIRR.** Newton-Raphson root finder over dated cashflows. No scipy, no numpy. Zero numeric dependencies in the core.
- **15 MCP tools.** Full discover-fetch-compute-submit loop exposed via FastMCP, with terminal `submit_report` tool that triggers grading.
- **69 backend tests.** Coverage across calculations, grader, environment, REST API, seed data, and the in-memory data store.
- **React + Vite frontend.** Five-page SPA (Dashboard, NAV Bridge, Fund Explorer, Agent Runner, Docs) with a custom finance design system, used both as a demo surface and as a debugging tool against the same backend.
- **Multi-stage Docker.** Node 20 builds the frontend in stage 1, Python 3.11-slim packages the backend in stage 2 with the built bundle copied in. Single image, host port `27860` to avoid local collisions.
- **OpenEnv-compliant.** `/reset`, `/step`, `/state`, `/health` plus a `CallToolAction` action space and a `FundLensObservation` observation space, all schema-validated by Pydantic v2.

Built for the Scaler x Meta (PyTorch) 2026 Hackathon, Round 1.
