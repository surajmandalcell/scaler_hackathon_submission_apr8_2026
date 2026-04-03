# FridgeEnv — Full Implementation Plan

## Context

**Hackathon:** Scaler x Meta PyTorch Hackathon (Round 1)
**Deadline:** April 8, 2026 11:59 PM
**Current state:** Empty repo with only `docs/hackathon_brief.pdf` and `docs/fridgeenv_plan.pdf`

**What we're building:** FridgeEnv — an OpenEnv-compliant RL environment where an agent receives a fridge inventory with expiration dates and must create a meal plan that minimizes food waste while respecting dietary restrictions and nutritional balance.

**Scoring:** Real-world utility (30%), Task/grader quality (25%), Environment design (20%), Code quality/spec (15%), Creativity (10%)

**DQ criteria:** Env doesn't deploy, plagiarized, grader always returns same score, no inference script

---

## Tooling

- **Monorepo:** npm workspaces
- **Python deps:** uv (lockfile for reproducibility)
- **Frontend:** Vite + React 18
- **Orchestration:** npm scripts at root (no Makefile)
- **Linting:** ruff (Python), eslint (JS)
- **Type checking:** mypy (Python), TypeScript optional
- **Testing:** pytest (Python), vitest (Frontend)

---

## Project Structure

```
openenv_scaler/
├── package.json                     # Root: npm workspaces + orchestration scripts
├── .npmrc                           # Workspace config
├── .gitignore
├── .env.example
├── Dockerfile
├── openenv.yaml                     # OpenEnv metadata and task definitions
├── inference.py                     # LLM-based baseline agent (OpenAI API)
├── README.md                        # HF Spaces metadata + docs
│
├── packages/
│   ├── backend/                     # Python: FastAPI + env + agents
│   │   ├── package.json             # npm scripts: test, lint, typecheck, dev
│   │   ├── pyproject.toml           # uv project config (deps, pytest, ruff, mypy)
│   │   ├── uv.lock                  # Locked Python deps
│   │   ├── app.py                   # FastAPI server: /reset, /step, /state, /health
│   │   ├── env/
│   │   │   ├── __init__.py          # Package exports
│   │   │   ├── data.py              # 50-item ingredient lookup table
│   │   │   ├── models.py            # Pydantic: Observation, Action, Reward
│   │   │   ├── generator.py         # Seeded deterministic fridge state factory
│   │   │   ├── scorer.py            # Deterministic reward calculation and grading
│   │   │   └── fridge_env.py        # Core: reset(), step(), state()
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # Abstract base agent
│   │   │   ├── random_agent.py      # Random baseline
│   │   │   ├── fifo_agent.py        # FIFO greedy baseline
│   │   │   └── eval.py              # Run 100 episodes per difficulty
│   │   └── tests/
│   │       ├── conftest.py          # Shared fixtures
│   │       ├── unit/
│   │       │   ├── test_data.py             # 11 tests
│   │       │   ├── test_models.py           # 12 tests
│   │       │   ├── test_generator.py        # 17 tests
│   │       │   ├── test_scorer.py           # 15 tests
│   │       │   ├── test_fridge_env.py       # 18 tests
│   │       │   └── test_agents.py           # 8 tests
│   │       ├── integration/
│   │       │   ├── test_api.py              # 10 tests (FastAPI TestClient)
│   │       │   ├── test_env_pipeline.py     # 5 tests (reset->step->reward)
│   │       │   └── test_agent_pipeline.py   # 5 tests (agent->env->score)
│   │       └── e2e/
│   │           ├── test_docker.py           # 4 tests (container build and health)
│   │           ├── test_full_workflow.py     # 3 tests (HTTP calls to running server)
│   │           └── test_inference.py        # 3 tests (inference.py end-to-end)
│   │
│   └── frontend/                    # React + Vite
│       ├── package.json             # Vite, React 18, vitest
│       ├── vite.config.js
│       ├── index.html
│       └── src/
│           ├── App.jsx              # Controls: task dropdown, seed, reset/step
│           └── components/
│               ├── FridgeView.jsx   # Grid of inventory items (color-coded)
│               ├── MealTimeline.jsx # Day-by-day meal visualization
│               └── ScoreCard.jsx    # Score display with breakdown
```

---

## npm Scripts (Root `package.json`)

```json
{
  "name": "openenv-scaler",
  "private": true,
  "workspaces": ["packages/*"],
  "scripts": {
    "install:backend": "cd packages/backend && uv sync",
    "install:all": "npm install && npm run install:backend",

    "test": "npm run test:unit && npm run test:integration",
    "test:unit": "npm run test:unit -w packages/backend",
    "test:integration": "npm run test:integration -w packages/backend",
    "test:e2e": "npm run test:e2e -w packages/backend",
    "test:frontend": "npm test -w packages/frontend",
    "test:all": "npm run test && npm run test:frontend && npm run test:e2e",

    "lint": "npm run lint -w packages/backend && npm run lint -w packages/frontend",
    "typecheck": "npm run typecheck -w packages/backend",

    "dev": "npm run dev -w packages/backend",
    "dev:frontend": "npm run dev -w packages/frontend",

    "build": "npm run build -w packages/frontend",
    "docker:build": "docker build -t fridgeenv .",
    "docker:run": "docker run --rm -p 7860:7860 fridgeenv",

    "validate": "openenv validate --url http://localhost:7860",
    "inference": "cd packages/backend && uv run python ../../inference.py",

    "preflight": "npm run lint && npm run typecheck && npm run test:all && npm run build"
  }
}
```

### Backend `packages/backend/package.json` scripts:
```json
{
  "scripts": {
    "test:unit": "uv run pytest tests/unit/ -v --tb=short",
    "test:integration": "uv run pytest tests/integration/ -v --tb=short",
    "test:e2e": "uv run pytest tests/e2e/ -v --tb=short",
    "lint": "uv run ruff check . && uv run ruff format --check .",
    "lint:fix": "uv run ruff check --fix . && uv run ruff format .",
    "typecheck": "uv run mypy env/ agents/ app.py --ignore-missing-imports",
    "dev": "uv run uvicorn app:app --host 0.0.0.0 --port 7860 --reload"
  }
}
```

---

## Phase 1: Project Bootstrapping

### Step 1.1: Init repo and monorepo
- `git init`
- Root `package.json` with npm workspaces
- `.npmrc` with workspace config
- `.gitignore` (Python, Node, Docker, .env, uv)
- `.env.example`: API_BASE_URL, MODEL_NAME, OPENAI_API_KEY, HF_TOKEN

### Step 1.2: Backend workspace
- `packages/backend/package.json` with npm scripts wrapping uv/pytest/ruff
- `packages/backend/pyproject.toml` with uv project config:
  - Runtime deps: fastapi>=0.115, uvicorn[standard], pydantic>=2.0, openai>=1.0, httpx
  - Dev deps: pytest, pytest-asyncio, pytest-cov, ruff, mypy
- `uv sync` to generate `uv.lock`
- Scaffold dirs + `__init__.py` files

### Step 1.3: Frontend workspace
- `packages/frontend/package.json` with Vite + React 18
- `vite.config.js` with API proxy to localhost:7860
- `index.html` shell

---

## Phase 2: Core Environment (Bottom-Up, Dependency Order)

### Step 2.1: `env/data.py` — Ingredient Lookup Table
50 food items across 6 categories:
- 10 protein, 10 carb, 12 vegetable, 8 dairy, 6 fruit, 4 condiment
- Each item: name, category, shelf_life_days (min, max), unit (g/ml/pcs), default_qty, contains_meat, contains_dairy, contains_gluten
- Condiments are non-perishable (shelf >= 30 days), excluded from waste scoring
- Helpers: `get_ingredients_by_category()`, `violates_restriction()`

**Tests — `tests/unit/test_data.py` (11 tests):**
- test_ingredient_count (exactly 50)
- test_category_distribution (10/10/12/8/6/4)
- test_unique_names
- test_valid_categories
- test_shelf_life_range (min <= max, min >= 1)
- test_valid_units (g/ml/pcs only)
- test_dietary_tags_type (all bools)
- test_condiments_long_shelf_life (min >= 30)
- test_proteins_have_variety (some meat, some not e.g. tofu)
- test_violates_restriction_logic
- test_get_by_category_returns_correct

### Step 2.2: `env/models.py` — Pydantic Models
- **FridgeItem**: name, quantity (>0), unit, expiry_date, category
- **Observation**: inventory, current_date, horizon (3-14), household_size (2-4), dietary_restrictions, done, reward, metadata
- **MealIngredient**: name, quantity (>0)
- **Meal**: day (>=1), meal_name, ingredients (min 1)
- **Action**: meal_plan (list of Meal)
- **Reward**: score (0-1), waste_rate, nutrition_score, items_used, items_expired, violations

**Tests — `tests/unit/test_models.py` (12 tests):**
- test_fridge_item_valid, test_fridge_item_negative_qty_rejected
- test_observation_valid, test_observation_horizon_bounds, test_observation_household_bounds
- test_observation_serialization_roundtrip
- test_meal_ingredient_valid, test_meal_requires_ingredients
- test_action_valid
- test_reward_score_bounds, test_reward_valid
- test_observation_has_openenv_fields (done, reward, metadata)

### Step 2.3: `env/generator.py` — Seeded Deterministic Factory
- Three difficulty profiles:
  - **Easy**: 5-8 items, 3-day horizon, 2 people, no restrictions
  - **Medium**: 10-15 items, 7-day horizon, 3 people, 1 restriction
  - **Hard**: 20-30 items, 14-day horizon, 4 people, 2 restrictions
- Uses `random.Random(seed)` instance for thread safety
- Fixed `current_date = date(2026, 1, 1)`
- Weighted sampling (perishables 2x, condiments 0.5x)
- Expiry clustering for medium/hard difficulty
- Solvability guarantee: at least 1 protein + 1 carb + 1 vegetable
- At least 30% of items conflict with chosen dietary restrictions

**Tests — `tests/unit/test_generator.py` (17 tests):**
- test_deterministic_same_seed
- test_different_seed_different_output
- test_easy/medium/hard_item_count_range (3 tests)
- test_easy_no_restrictions, test_medium_one_restriction, test_hard_two_restrictions
- test_easy_horizon_3
- test_expiry_dates_within_range
- test_medium_has_clustering, test_hard_has_large_clusters
- test_restriction_conflict_rate (>= 30%)
- test_solvability_guarantee (protein + carb + veg present)
- test_quantities_scaled_by_household
- test_all_difficulties_valid
- test_100_seeds_no_crash

### Step 2.4: `env/scorer.py` — Deterministic Scoring
- **Grader score**: used_perishables / total_perishables (0.0-1.0)
- **Detailed reward**: per-item consumption (+1.0 full, proportional partial, -1.0 expired), per-day nutrition (+0.2 balanced), per-violation penalty (-0.3)
- Condiments excluded from waste calculation
- Standalone `compute_grader_score()` for openenv.yaml

**Tests — `tests/unit/test_scorer.py` (15 tests):**
- test_perfect_score (all consumed = 1.0)
- test_zero_score (nothing consumed = 0.0)
- test_partial_consumption
- test_condiments_excluded_from_waste
- test_nutrition_bonus, test_nutrition_penalty_missing_category
- test_dietary_violation_penalty, test_multiple_violations
- test_grader_score_range (always 0-1)
- test_waste_rate_calculation, test_nutrition_score_calculation
- test_empty_inventory (edge case = 1.0)
- test_deterministic
- test_items_used_count, test_items_expired_count

### Step 2.5: `env/fridge_env.py` — Core Environment
- `FridgeEnv.reset(task_id, seed)` -> Observation
- `FridgeEnv.step(action)` -> (Observation, Reward, done=True, info)
- `FridgeEnv.state()` -> dict
- Single-step episodes (submit full plan, get reward)

**Step simulation logic:**
1. For each day 1..horizon:
   - Process meals for that day
   - For each ingredient: validate exists, clamp overconsumption, check dietary violations, deduct
   - Track nutrition categories per day
   - Expire items where expiry_date <= current_date + day
2. Call compute_reward() with all logs
3. Return (final_obs, reward, True, info_dict)

**Tests — `tests/unit/test_fridge_env.py` (18 tests):**
- test_reset_returns_observation, test_reset_clears_previous_state
- test_step_returns_done_true, test_step_without_reset_raises, test_double_step_raises
- test_state_before_reset_raises, test_state_after_reset, test_state_after_step
- test_deterministic_reset
- test_ingredient_consumption, test_unknown_ingredient_skipped, test_overconsumption_clamped
- test_dietary_violation_detected, test_expiry_simulation
- test_nutrition_tracking, test_empty_meal_plan (scores 0)
- test_perfect_plan_high_score
- test_all_difficulties_round_trip

### Step 2.6: `env/__init__.py` — Package Exports

---

## Phase 3: Agents

### Step 3.1: `agents/base.py` — Abstract interface
### Step 3.2: `agents/random_agent.py` — Random baseline (expected: 0.2-0.4 easy)
### Step 3.3: `agents/fifo_agent.py` — FIFO greedy baseline (expected: 0.7-0.9 easy)
### Step 3.4: `agents/eval.py` — Run 100 episodes per difficulty, aggregate scores

**Tests — `tests/unit/test_agents.py` (8 tests):**
- test_fifo_returns_valid_action, test_random_returns_valid_action
- test_fifo_uses_soonest_first, test_fifo_covers_horizon, test_random_covers_horizon
- test_fifo_scores_higher_than_random_easy (statistical, 20 seeds)
- test_eval_runs_without_error, test_eval_output_format

---

## Phase 4: FastAPI Server

### Step 4.1: `packages/backend/app.py`
- `GET /health` -> {"status": "ok"}
- `POST /reset` {task_id, seed} -> Observation
- `POST /step` Action -> {observation, reward, done, info}
- `GET /state` -> current state (409 before reset)
- Static file serving for React frontend build at `/`

### Step 4.2: `openenv.yaml` (project root)
- spec_version: 1, name: FridgeEnv, type: environment, runtime: docker, port: 7860
- 3 tasks (easy, medium, hard) with grader references

**Tests — `tests/integration/test_api.py` (10 tests):**
- test_health_returns_200
- test_reset_returns_observation, test_reset_different_tasks
- test_step_returns_reward, test_step_before_reset_returns_400
- test_state_before_reset_returns_409, test_state_after_reset, test_state_after_step
- test_full_roundtrip
- test_reset_clears_previous_episode

---

## Phase 5: Inference Script

### `inference.py` (project root)
- 15 LLM calls total (3 tasks x 5 seeds)
- OpenAI client with temperature=0.0 and json_object format
- 3 retries on parse failure, empty plan fallback
- Produces results.json
- Runtime approximately 75 seconds

**Tests — `tests/e2e/test_inference.py` (3 tests):**
- test_inference_script_syntax (importable)
- test_prompt_template_format
- test_fallback_on_bad_json (mocked)

---

## Phase 6: Integration and Pipeline Tests

### `tests/integration/test_env_pipeline.py` (5 tests):
- test_reset_step_roundtrip_easy/medium/hard
- test_deterministic_pipeline (same seed = same reward)
- test_different_seeds_different_rewards

### `tests/integration/test_agent_pipeline.py` (5 tests):
- test_fifo_agent_easy_pipeline (score > 0.5)
- test_fifo_agent_medium_pipeline (score > 0.2)
- test_random_agent_produces_valid_score
- test_eval_100_episodes_easy
- test_eval_results_format

### `tests/e2e/test_docker.py` (4 tests):
- test_docker_build
- test_docker_run_health
- test_docker_reset_step
- test_docker_port_7860

### `tests/e2e/test_full_workflow.py` (3 tests):
- test_server_reset_step_state
- test_server_multiple_episodes
- test_server_concurrent_safety

---

## Phase 7: Frontend (React + Vite)

- **FridgeView.jsx**: Grid of inventory cards, color-coded by days-to-expiry (green >5, yellow 3-5, red <3)
- **MealTimeline.jsx**: Horizontal day-by-day timeline showing meals
- **ScoreCard.jsx**: Grader score, waste rate, nutrition score, violations
- **App.jsx**: Task dropdown, seed input, Reset/Step buttons

---

## Phase 8: Docker and Deployment

### `Dockerfile` (project root)
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Python deps (cached layer)
COPY packages/backend/pyproject.toml packages/backend/uv.lock packages/backend/
RUN cd packages/backend && uv sync --frozen --no-dev

# Node for frontend build
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm && rm -rf /var/lib/apt/lists/*
COPY packages/frontend/ packages/frontend/
RUN cd packages/frontend && npm ci && npm run build

# App code
COPY packages/backend/ packages/backend/
COPY openenv.yaml inference.py ./

EXPOSE 7860
CMD ["uv", "run", "--directory", "packages/backend", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

### `.dockerignore`
- .venv, __pycache__, .git, tests, docs, node_modules, .env

### HF Spaces README.md metadata
- sdk: docker, app_port: 7860, tags: openenv

---

## Phase 9: README.md
- Environment description and motivation (food waste is a $1T/year problem)
- Action/observation space definitions
- Task descriptions with difficulty progression
- Setup and usage instructions (`npm run install:all`, `npm run dev`, `npm run test`)
- Baseline scores table (Random, FIFO, LLM)

---

## Test Suite: 111 Tests Total

| Category | File | Count | What it Tests |
|----------|------|-------|---------------|
| **Unit** | test_data.py | 11 | Ingredient count, categories, dietary tags, helpers |
| **Unit** | test_models.py | 12 | Pydantic validation, serialization, bounds |
| **Unit** | test_generator.py | 17 | Determinism, difficulty profiles, clustering, solvability |
| **Unit** | test_scorer.py | 15 | Perfect/zero/partial scores, condiment exclusion, violations |
| **Unit** | test_fridge_env.py | 18 | Reset/step/state lifecycle, consumption, expiry, edge cases |
| **Unit** | test_agents.py | 8 | Valid actions, FIFO vs random comparison, eval format |
| **Integration** | test_api.py | 10 | All HTTP endpoints, error codes, roundtrips |
| **Integration** | test_env_pipeline.py | 5 | Reset-step-reward flow, determinism across seeds |
| **Integration** | test_agent_pipeline.py | 5 | Agent-env-score pipeline, eval 100 episodes |
| **E2E** | test_docker.py | 4 | Container build, health check, API roundtrip, port |
| **E2E** | test_full_workflow.py | 3 | Full HTTP workflow, multiple episodes, concurrency |
| **E2E** | test_inference.py | 3 | Script syntax, prompt format, JSON fallback |
| | **TOTAL** | **111** | |

---

## Implementation Order (Critical Path)

| # | Module | Depends On | Blocks |
|---|--------|------------|--------|
| 1 | Project setup (monorepo, uv, workspaces) | nothing | Everything |
| 2 | env/data.py + tests | nothing | Generator |
| 3 | env/models.py + tests | nothing | Generator, Scorer, Env |
| 4 | env/generator.py + tests | data, models | FridgeEnv |
| 5 | env/scorer.py + tests | models | FridgeEnv |
| 6 | env/fridge_env.py + tests | all env/ | App, Agents |
| 7 | agents/*.py + tests | env/ | Inference |
| 8 | agents/eval.py + tests | agents, env | Baseline scores |
| 9 | app.py + integration tests | env/ | Inference, Validate |
| 10 | openenv.yaml | scorer | Validate |
| 11 | inference.py + tests | app.py | Submission |
| 12 | Dockerfile + e2e tests | all | Deployment |
| 13 | Frontend | app.py | Nice-to-have |
| 14 | README.md | all | Submission |

Steps 1-10 required to pass `openenv validate`. Steps 1-12 for full automated validation gate.

---

## Verification Checklist (Pre-Submission)

- [ ] `npm run preflight` passes (lint + typecheck + all tests + build)
- [ ] `npm run test` passes all 111 backend tests
- [ ] `npm run test:frontend` passes frontend tests
- [ ] `npm run lint` passes (ruff + eslint)
- [ ] `npm run typecheck` passes (mypy)
- [ ] `openenv validate --url http://localhost:7860` passes
- [ ] `npm run docker:build && npm run docker:run` starts on port 7860
- [ ] GET /health returns 200
- [ ] POST /reset returns valid Observation for all 3 tasks
- [ ] POST /step returns Reward with done=true, score in [0,1]
- [ ] GET /state returns 409 before reset, valid state after
- [ ] `npm run inference` completes under 20 min, produces results.json
- [ ] Deterministic: same seed = same score (verified with 2 runs)
- [ ] Scores vary across seeds (not constant — DQ criterion)
- [ ] Frontend loads at `/`
- [ ] FIFO agent scores > Random agent (validates grader quality)

---

## Key Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| LLM returns invalid JSON | 3 retries + json_object format + empty plan fallback |
| Grader returns constant score | Test 100 seeds, verify variance > 0 |
| Unsolvable generated state | Generator guarantees 1 protein + 1 carb + 1 veg |
| openenv validate schema mismatch | Install openenv-core, validate locally before push |
| Date serialization issues | Use model_dump(mode="json") for ISO dates |
| Expiry off-by-one | Unit test day boundaries explicitly |
| uv not in Docker | Multi-stage: copy uv binary from official image |

---

## Expected Baseline Scores

| Agent | Easy | Medium | Hard |
|-------|------|--------|------|
| Random | 0.2-0.4 | 0.1-0.3 | 0.05-0.15 |
| FIFO (greedy) | 0.7-0.9 | 0.4-0.6 | 0.2-0.4 |
| LLM | 0.8-1.0 | 0.5-0.7 | 0.3-0.5 |

Hard task designed so frontier models struggle below 0.5 — overlapping expiry clusters + dual dietary restrictions create combinatorial planning that greedy/naive approaches cannot solve optimally.
