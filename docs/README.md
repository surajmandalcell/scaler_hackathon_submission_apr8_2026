# FundLens

> PE Fund NAV Bridge Environment for the Scaler x Meta PyTorch Hackathon 2026.

FundLens is an [OpenEnv](https://github.com/anthropics/openenv-spec)-compliant environment that tests AI agents on **real estate private equity fund reporting**. Agents query fund data via [MCP tools](mcp-tools.md), compute 8-line NAV bridges, and submit performance metrics (MOIC, IRR) for tolerance-based grading.

## What this is

This is a **test environment**, not a trained model. It provides:

- A scoring framework for evaluating LLM agents on a structured financial reasoning task
- Three difficulty levels with realistic PE fund data
- 15 MCP tools for querying funds, deals, ownership, and cashflows
- A pure-Python XIRR calculator (Newton-Raphson, no scipy)
- Tolerance-based grading with partial credit

## Why it matters

Fund analysts at PE firms spend weeks each quarter manually building NAV bridges in Excel -- reconciling beginning NAV to ending NAV through cashflow adjustments. Mistakes are costly and the process scales poorly. This environment turns that workflow into a benchmark for AI agents.

## The task

Given a portfolio of real estate funds, agents must compute the 8-line NAV bridge:

```
Beginning NAV
+ Contribution        (capital deployed)
- Disposition         (proceeds received)
+ Income              (rental / operating income)
= Cashflow-Adjusted NAV
- Income Reversal     (income removed from valuation)
+/- Write Up/Down     (the plug, derived from ending NAV)
= Ending NAV          (appraiser value at period end)
```

For medium and hard tasks, agents must also compute MOIC and (for hard) IRR using a real XIRR calculation.

## Difficulty levels

| Level  | Fund                  | Properties | Graded                       |
|--------|-----------------------|------------|------------------------------|
| Easy   | RE Alpha Fund I       | 3 (100% owned) | NAV bridge only          |
| Medium | RE Beta Fund II       | 5 (100% owned) | NAV bridge + MOIC        |
| Hard   | Alpha + Beta + Gamma  | 9 (with co-investment) | NAV bridge + MOIC + IRR |

## How to use these docs

The sidebar on the left has everything. If you're a judge, start with [Quick Start](quick-start.md). If you're an engineer, jump to the [Architecture](architecture.md) and [HTTP API](api.md).

## Project status

| Component  | Status                                    |
|------------|-------------------------------------------|
| Backend    | 69 passing tests, ruff + mypy clean       |
| Frontend   | React 18 + Vite, 12 passing tests         |
| Docker     | Multi-stage build, runs on port 7860      |
| Inference  | Baseline LLM agent via OpenAI client      |

Built for the Scaler x Meta (PyTorch) 2026 Hackathon, Round 1.
