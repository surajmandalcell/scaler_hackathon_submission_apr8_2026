---
title: FridgeEnv
emoji: 🥦
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
tags:
  - openenv
  - reinforcement-learning
  - food-waste
---

# FridgeEnv — Food Waste Reduction RL Benchmark

An **OpenEnv-compliant** reinforcement learning environment where AI agents learn to minimize household food waste through intelligent meal planning.

## The Problem

Global food waste exceeds **$1 trillion per year**. A significant portion occurs at the household level — perishable items expire before they're used, often because meals aren't planned around what's actually in the fridge.

## How It Works

1. **Agent receives** a fridge inventory with expiration dates, dietary restrictions, and a planning horizon
2. **Agent submits** a complete meal plan (which items to cook on which days)
3. **Environment scores** the plan based on waste minimization, nutritional balance, and dietary compliance

### Three Difficulty Levels

| Level | Items | Horizon | Household | Restrictions | Challenge |
|-------|-------|---------|-----------|-------------|-----------|
| **Easy** | 5-8 | 3 days | 2 people | None | Basic planning |
| **Medium** | 10-15 | 7 days | 3 people | 1 restriction | Expiry clustering |
| **Hard** | 20-30 | 14 days | 4 people | 2 restrictions | Combinatorial explosion |

### Observation Space

```json
{
  "inventory": [
    {"name": "chicken_breast", "quantity": 500, "unit": "g", "expiry_date": "2026-01-04", "category": "protein"}
  ],
  "current_date": "2026-01-01",
  "horizon": 3,
  "household_size": 2,
  "dietary_restrictions": []
}
```

### Action Space

```json
{
  "meal_plan": [
    {
      "day": 1,
      "meal_name": "stir_fry",
      "ingredients": [
        {"name": "chicken_breast", "quantity": 250},
        {"name": "broccoli", "quantity": 150}
      ]
    }
  ]
}
```

### Reward

- **Grader score** (0.0-1.0): Fraction of perishable items with any usage before expiry
- **Nutrition score**: Days with balanced macros (protein + carb + vegetable) / total days
- **Violations**: -0.3 per dietary restriction breach

## Setup

```bash
# Install everything
npm run install:all

# Run backend dev server
npm run dev

# Run frontend dev server (separate terminal)
npm run dev:frontend

# Run all tests
npm run test

# Full preflight check
npm run preflight
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/reset` | POST | Start new episode: `{"task_id": "easy", "seed": 42}` |
| `/step` | POST | Submit meal plan, get reward |
| `/state` | GET | Current environment state |

## Baseline Scores

| Agent | Easy | Medium | Hard |
|-------|------|--------|------|
| Random | 0.72 | 0.66 | 0.63 |
| FIFO (greedy) | 1.00 | 0.99 | 0.99 |
| LLM (GLM-5.1) | 0.97 | 0.73 | 0.68 |

LLM scores from GLM-5.1 via OpenAI-compatible API (5 episodes per difficulty). Full per-episode detail in `outputs/`.

The **hard** task shows clear difficulty progression — GLM-5.1 drops from 97% on easy to 68% on hard. Overlapping expiry clusters combined with dual dietary restrictions create combinatorial planning that even frontier models struggle with.

## Docker

```bash
npm run docker:build
npm run docker:run
# Server at http://localhost:7860
```

## Project Structure

```
openenv_scaler/
├── packages/
│   ├── backend/           # Python: FastAPI + env + agents
│   │   ├── env/           # Core environment (data, models, generator, scorer)
│   │   ├── agents/        # Baseline agents (random, FIFO)
│   │   ├── tests/         # 109 tests (unit + integration + e2e)
│   │   └── app.py         # FastAPI server
│   └── frontend/          # React + Vite dashboard
├── inference.py           # LLM baseline agent
├── openenv.yaml           # OpenEnv manifest
└── Dockerfile
```

## Tech Stack

- **Backend**: Python 3.11, FastAPI, Pydantic v2, uv
- **Frontend**: React 18, Vite
- **Testing**: pytest (109 tests), vitest
- **Deployment**: Docker, Hugging Face Spaces

---

*Scaler x Meta PyTorch Hackathon 2026 — Round 1*
