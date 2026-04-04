# What Is This Project?

## The Short Version

We built a **test environment** (like a video game level) that AI agents play in. We did NOT train an AI model. Think of it like building a gym — other people's robots will come exercise in it.

## What the Hackathon Actually Wants

The hackathon is by **Scaler x Meta (PyTorch)**. The task is:

> Build an OpenEnv-compliant environment that simulates a real-world task for AI agents to learn from.

**OpenEnv** is a standard specification (like an API contract) for RL environments. It defines how agents interact with environments: reset, step, observe, get a score.

So the deliverable is NOT a trained model. It's the **environment itself** — the thing a model would be trained against.

## What We Built: FridgeEnv

**The scenario:** You have a fridge full of food. Some items expire tomorrow, some next week. You need to plan meals for the next few days to minimize waste. Oh, and some people in the household are vegetarian or lactose-intolerant.

**Why this matters:** Food waste costs over $1 trillion per year globally. A significant chunk happens because people don't plan meals around what's expiring.

### How It Works

```
1. Environment generates a fridge inventory
   (chicken expires in 2 days, rice good for 6 months, milk expires tomorrow...)

2. An AI agent looks at the fridge and creates a meal plan
   (Day 1: use the milk and chicken. Day 2: use the spinach before it wilts...)

3. Environment simulates the plan day by day
   - Deducts used ingredients
   - Expires items that pass their date
   - Checks if the agent violated dietary restrictions
   - Checks if meals are nutritionally balanced

4. Environment returns a score (0.0 to 1.0)
   - 1.0 = every perishable item got used before expiring
   - 0.0 = everything rotted in the fridge
```

### What the Scores Mean

The **grader score** (0.0 to 1.0) answers one question: **what fraction of perishable items did you touch before they expired?**

- Score 1.0 = You used every perishable item at least partially. Zero waste.
- Score 0.5 = Half the perishable items expired untouched.
- Score 0.0 = You didn't use anything. Everything went to waste.

Additional signals (for training, not grading):
- **Waste rate** = items that expired with food left / total perishable items
- **Nutrition score** = days with balanced meals (protein + carb + vegetable) / total days
- **Violations** = number of times dietary restrictions were broken (e.g. giving meat to a vegetarian household)

### The Three Difficulty Levels

**Easy** — Your first apartment.
- 5-8 items in the fridge
- Plan for 3 days
- 2 people, no dietary restrictions
- Each item expires on a different day — straightforward to prioritize

**Medium** — Family of three with a vegetarian.
- 10-15 items in the fridge
- Plan for a full week (7 days)
- 3 people, 1 dietary restriction (e.g. vegetarian)
- Some items share the same expiry date ("Tuesday everything goes bad") — forces harder prioritization

**Hard** — Large household, complex constraints.
- 20-30 items in the fridge
- Plan for 2 weeks (14 days)
- 4 people, 2 dietary restrictions (e.g. lactose-free AND gluten-free)
- Big clusters of items expiring on the same day, plus "decoy" items with long shelf life
- This creates a combinatorial explosion that even frontier LLMs struggle with

### Who Plays in This Environment?

We built three **baseline agents** to show the environment works:

1. **Random Agent** — Picks random items each day. Scores poorly (~0.6-0.7) because it wastes food by not prioritizing expiring items.

2. **FIFO Agent** — "First In, First Out" — always uses the soonest-expiring items first. Scores very well (~0.99) because it's greedy about preventing waste. But it ignores dietary restrictions and nutrition.

3. **LLM Agent (GLM-5.1)** — We give an LLM the fridge inventory as text, ask it to make a meal plan, and submit that plan. This tests whether language models can do practical planning. Scores 0.97 on easy, drops to 0.73 on medium, and 0.68 on hard — clear difficulty progression.

### What Gets Judged

The hackathon judges score the **environment quality**, not agent performance:

| What They Judge | Weight | Our Approach |
|----------------|--------|-------------|
| Is this a real problem? | 30% | Food waste is a $1T/year global issue |
| Are the tasks well-designed? | 25% | 3 difficulty levels, deterministic scoring, meaningful progression |
| Is the environment well-built? | 20% | Clean API (reset/step/state), rich reward signal, proper episode boundaries |
| Is the code good? | 15% | 137 tests, typed models, npm workspaces, Docker deployment |
| Is it creative? | 10% | Novel domain (food waste), interesting mechanics (dietary constraints + expiry clustering) |

### What This Project Is NOT

- **NOT a trained model** — No PyTorch training loops, no gradient descent, no model weights
- **NOT a chatbot** — The LLM agent is just a baseline to prove the environment works
- **NOT a database app** — All 50 food items are hardcoded, no external data
- **NOT a web app** — The frontend is just a visualization dashboard, the real product is the API

### The Tech Stack

- **Backend:** Python, FastAPI, Pydantic (the environment + API)
- **Frontend:** React + Vite (visualization dashboard)
- **Testing:** pytest (109 tests) + vitest (28 tests) = 137 total
- **Deployment:** Docker on Hugging Face Spaces
- **LLM Baseline:** OpenAI-compatible API (GLM-5.1 via Zhipu)
- **Package Management:** npm workspaces (monorepo), uv (Python)
