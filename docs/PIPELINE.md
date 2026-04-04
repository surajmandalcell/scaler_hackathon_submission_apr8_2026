# FridgeEnv — Technical Pipeline

This document explains exactly what happens at every stage, what role each component plays, and where RL fits in.

---

## The Big Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                        WE BUILT THIS                            │
│                                                                 │
│   ┌──────────┐    ┌──────────────┐    ┌────────────────────┐   │
│   │ Generator │───▶│ Environment  │───▶│ Scorer / Grader    │   │
│   │ (seed+rng)│    │ (simulation) │    │ (reward function)  │   │
│   └──────────┘    └──────┬───────┘    └────────────────────┘   │
│                          │                                      │
│                    ┌─────▼─────┐                                │
│                    │ FastAPI   │                                 │
│                    │ /reset    │                                 │
│                    │ /step     │                                 │
│                    │ /state    │                                 │
│                    └─────┬─────┘                                │
│                          │                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │   AGENTS PLUG IN HERE   │
              │                         │
              │  • Random (heuristic)   │
              │  • FIFO (heuristic)     │
              │  • LLM (inference.py)   │
              │  • RL model (future)    │  ◀── This is what researchers
              │  • Your custom agent    │      would train against our env
              └─────────────────────────┘
```

Our job: build the gym.
Their job (researchers, RL agents, LLMs): work out in it.

---

## Stage-by-Stage Pipeline

### Stage 1: Episode Generation (`reset`)

**What triggers it:** `POST /reset {"task_id": "hard", "seed": 42}`

**What happens:**

```
generator.py
│
├── random.Random(42)          ← Seeded RNG instance (NOT global random)
│                                 This makes it deterministic: seed 42
│                                 always produces the exact same fridge.
│
├── Pick difficulty profile
│   hard = {items: 20-30, horizon: 14d, household: 4, restrictions: 2}
│
├── Sample N items from 50-ingredient table
│   Weighted: perishables 2x, condiments 0.5x
│   So the fridge isn't full of olive oil and soy sauce
│
├── Assign expiry dates
│   Each item: current_date + rng.randint(1, horizon+2)
│   Hard mode: cluster 4-6 items on the same expiry date
│   This creates "expiry pressure" — too much expires at once
│
├── Scale quantities by household size
│   4 people need more food than 2
│
├── Pick dietary restrictions
│   Hard: 2 restrictions (e.g. lactose-free + gluten-free)
│   Ensure ≥20% of items conflict with restrictions
│   This creates trap ingredients the agent must avoid
│
└── Guarantee solvability
    At least 1 protein + 1 carb + 1 vegetable in inventory
    So it's never impossible to make a balanced meal
```

**Output:** An `Observation` JSON with inventory, dates, constraints.

**Why seeded RNG matters for RL:**
- Agent trains on seed 0..99999, each producing a different fridge
- Same seed = same fridge = reproducible benchmarks
- You can compare two agents on the exact same 1000 scenarios
- This is standard in ALL RL environments (Gymnasium, Atari, MuJoCo, etc.)

---

### Stage 2: Agent Decides (`act`)

**This is NOT part of our environment.** This is what plugs into it.

The agent receives the observation and must return a meal plan. Three baseline agents show different strategies:

**Random Agent** — No intelligence
```
For each day:
    Pick 2-4 random items
    Use 10-50% of available quantity
```
Result: ~63-72% score. Wastes most food.

**FIFO Agent** — Simple heuristic
```
Sort items by expiry date (soonest first)
For each day:
    Use items about to expire tomorrow (all of it)
    Then spread remaining items across days
    Try to hit protein + carb + vegetable
```
Result: ~99% score. Touches everything but ignores dietary restrictions.

**LLM Agent (inference.py)** — Language model reasoning
```
Format fridge inventory as text prompt
Send to GLM-5.1 / GPT-4o via OpenAI API
Parse JSON response into meal plan
```
Result: 97% easy, 73% medium, 68% hard. Understands restrictions but
struggles with combinatorial planning on large inventories.

**Future RL Agent** — This is the whole point
```
A reinforcement learning model that trains against our environment:
    for episode in range(1_000_000):
        obs = env.reset(seed=episode)
        action = model.predict(obs)      ← neural network
        obs, reward, done, info = env.step(action)
        model.update(reward)             ← gradient descent
```
This is what researchers would build. Our environment provides the
training loop's reset/step/reward cycle. We don't train the model —
we provide the gym it trains in.

---

### Stage 3: Simulation (`step`)

**What triggers it:** `POST /step {"meal_plan": [...]}`

**What happens — day-by-day simulation in `fridge_env.py`:**

```
For day = 1 to horizon:
│
├── Get all meals planned for this day
│
├── For each ingredient in each meal:
│   │
│   ├── Does this item exist in inventory?
│   │   No → skip, log warning
│   │
│   ├── Has it already expired?
│   │   Yes → skip, log warning
│   │
│   ├── Is there enough quantity?
│   │   No → clamp to what's available (use what's left)
│   │
│   ├── Does it violate dietary restrictions?
│   │   e.g. chicken_breast in a vegetarian household
│   │   Yes → log violation (penalty later), but still deduct
│   │
│   ├── Deduct quantity from inventory
│   │   inventory["chicken_breast"] -= 250
│   │
│   └── Track which food categories were used today
│       {protein, carb, vegetable} → balanced meal = nutrition bonus
│
├── After processing all meals for this day:
│   Record nutrition balance for the day
│
└── Items whose expiry_date has passed are now expired
    Any remaining quantity on them counts as waste
```

This is a **physics engine for food**. Just like a robotics simulator
computes joint angles and gravity, this computes expiry dates and
consumption. The agent's intelligence determines the outcome.

---

### Stage 4: Scoring (`compute_reward`)

**What happens in `scorer.py`:**

```
Inputs:
  original_inventory    ← what the fridge started with
  consumption_log       ← {item_name: total_qty_consumed}
  expiry_events         ← items that expired with food still left
  nutrition_log         ← {day: set_of_categories_present}
  violation_log         ← dietary restriction breaches
  horizon               ← total days

Grader Score (what OpenEnv validation checks):
  perishable_items = items where category != "condiment"
  used_items = perishable items where consumption > 0
  score = used_items / total_perishable_items
  
  Range: 0.0 (nothing used) to 1.0 (everything touched)

Waste Rate:
  expired_with_remaining / total_perishable

Nutrition Score:
  days_with_balanced_meals / total_days
  balanced = has protein AND carb AND vegetable

Violation Count:
  Number of dietary restriction breaches
```

**Why the scoring matters for RL:**
- The grader score is what gets reported to the hackathon judges
- But the detailed signals (waste, nutrition, violations) are what
  an RL agent would use as its reward function during training
- Sparse reward (just 0/1) is hard to learn from
- Rich reward (you wasted 30%, nutrition was good 4/7 days, 2 violations)
  gives the agent gradient — it knows what to improve

---

### Stage 5: Full RL Training Loop (what researchers would do)

This is the part WE DON'T BUILD. Our environment enables it.

```python
import torch
from stable_baselines3 import PPO

# Our environment wraps into a Gymnasium interface
env = FridgeEnvGym(difficulty="hard")

# Standard RL training
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=1_000_000)

# The model repeatedly calls:
#   obs = env.reset()        ← our generator
#   action = model(obs)      ← their neural network
#   obs, reward = env.step() ← our simulation + scorer
#   model.update(reward)     ← their gradient descent

# After training, evaluate
mean_reward = evaluate_policy(model, env, n_eval_episodes=100)
print(f"Trained agent scores: {mean_reward}")
```

The seeded RNG ensures:
- Training uses random seeds → agent sees diverse fridges
- Evaluation uses fixed seeds → fair comparison between agents
- Same eval seeds for all agents → apples-to-apples benchmark

---

## Where Each File Fits

```
env/data.py        → 50 ingredients (the "world" objects)
env/models.py      → Data contracts (Observation, Action, Reward)
env/generator.py   → Stage 1: seeded scenario generation
env/fridge_env.py  → Stage 3: day-by-day simulation engine
env/scorer.py      → Stage 4: reward computation

agents/base.py     → Agent interface (what plugs in)
agents/random_agent.py → Baseline: random decisions
agents/fifo_agent.py   → Baseline: greedy heuristic
inference.py           → Baseline: LLM via API

app.py             → HTTP layer (OpenEnv spec endpoints)
openenv.yaml       → Environment metadata for OpenEnv registry
```

---

## Why This Design Gets Points

| Hackathon Criteria | How Our Pipeline Addresses It |
|---|---|
| **Real-world utility (30%)** | Food waste is a $1T/year problem. The simulation models actual fridge dynamics — expiry dates, dietary needs, portion planning |
| **Task quality (25%)** | Three difficulty tiers. Deterministic seeded generation. Hard mode creates genuine combinatorial pressure (30 items, 14 days, 2 restrictions, expiry clusters) |
| **Environment design (20%)** | Clean reset/step/state cycle. Rich reward signal (not just pass/fail). Single-step episodes with day-by-day internal simulation |
| **Code quality (15%)** | 137 tests. Typed Pydantic models. OpenEnv validate 6/6. Docker deployment |
| **Creativity (10%)** | Novel domain. Dietary restrictions as constraints. Expiry clustering as difficulty mechanic. Nutrition balance as secondary objective |
