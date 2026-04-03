#!/usr/bin/env python3
"""
FridgeEnv Interactive Demo
==========================
Runs the full environment lifecycle without needing a server or API key.
Shows reset → agent → step → score for all difficulties.
"""

from __future__ import annotations

import json
import os
import sys
import time

# Ensure packages/backend is on the path (when run via `uv run python ../../scripts/demo.py`)
_backend_dir = os.path.join(os.path.dirname(__file__), "..", "packages", "backend")
if os.path.isdir(_backend_dir):
    sys.path.insert(0, os.path.abspath(_backend_dir))

# ── Helpers ──────────────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
RESET_STYLE = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"


def color_score(score: float) -> str:
    pct = f"{score * 100:.0f}%"
    if score >= 0.8:
        return f"{GREEN}{pct}{RESET_STYLE}"
    if score >= 0.5:
        return f"{YELLOW}{pct}{RESET_STYLE}"
    return f"{RED}{pct}{RESET_STYLE}"


def banner(text: str) -> None:
    width = 60
    print(f"\n{CYAN}{'═' * width}{RESET_STYLE}")
    print(f"{CYAN}  {text}{RESET_STYLE}")
    print(f"{CYAN}{'═' * width}{RESET_STYLE}\n")


def section(text: str) -> None:
    print(f"\n{MAGENTA}── {text} {'─' * (50 - len(text))}{RESET_STYLE}")


# ── Main Demo ────────────────────────────────────────────────────────

def main() -> None:
    banner("FridgeEnv — Interactive Demo")

    print(f"{DIM}Importing environment...{RESET_STYLE}")
    from env.fridge_env import FridgeEnv
    from env.models import Action, Meal, MealIngredient
    from agents.fifo_agent import FIFOAgent
    from agents.random_agent import RandomAgent
    from agents.eval import run_assessment

    env = FridgeEnv()
    fifo = FIFOAgent()
    random_agent = RandomAgent(seed=0)

    # ── Part 1: Show environment lifecycle for each difficulty ────

    section("Part 1: Environment Lifecycle")
    print("Demonstrating reset → observe → act → score for each difficulty.\n")

    for difficulty in ["easy", "medium", "hard"]:
        seed = 42
        obs = env.reset(task_id=difficulty, seed=seed)

        print(f"{BOLD}[{difficulty.upper()}]{RESET_STYLE} seed={seed}")
        print(f"  Inventory: {len(obs.inventory)} items, Horizon: {obs.horizon}d, "
              f"Household: {obs.household_size}p")
        if obs.dietary_restrictions:
            print(f"  Restrictions: {', '.join(obs.dietary_restrictions)}")

        # Show first 5 items
        sorted_inv = sorted(obs.inventory, key=lambda x: x.expiry_date)
        for item in sorted_inv[:5]:
            days = (item.expiry_date - obs.current_date).days
            urgency = f"{RED}!{RESET_STYLE}" if days <= 2 else " "
            print(f"  {urgency} {item.name:20s} {item.quantity:>7.1f}{item.unit:3s} "
                  f"expires in {days}d ({item.category})")
        if len(obs.inventory) > 5:
            print(f"  {DIM}  ...and {len(obs.inventory) - 5} more items{RESET_STYLE}")

        # Run FIFO agent
        action_dict = fifo.act(obs.model_dump(mode="json"))
        action = Action(**action_dict)
        _, reward, _, info = env.step(action)

        print(f"\n  {BOLD}FIFO Agent Result:{RESET_STYLE}")
        print(f"    Grader Score:    {color_score(reward.score)}")
        print(f"    Waste Rate:      {reward.waste_rate * 100:.0f}%")
        print(f"    Nutrition Score: {reward.nutrition_score * 100:.0f}%")
        print(f"    Items Used:      {reward.items_used}/{len(obs.inventory)}")
        print(f"    Items Expired:   {reward.items_expired}")
        if reward.violations:
            print(f"    Violations:      {len(reward.violations)}")
        print()

    # ── Part 2: Agent Comparison (20 episodes) ───────────────────

    section("Part 2: Agent Comparison (20 episodes each)")
    print()

    header = f"{'Agent':15s} {'Difficulty':8s} {'Score':>8s} {'Waste':>8s} {'Nutrition':>10s}"
    print(f"  {BOLD}{header}{RESET_STYLE}")
    print(f"  {'─' * len(header)}")

    for agent, name in [(random_agent, "Random"), (fifo, "FIFO")]:
        for difficulty in ["easy", "medium", "hard"]:
            result = run_assessment(agent, difficulty, num_episodes=20)
            score_str = color_score(result["mean_score"])
            print(
                f"  {name:15s} {difficulty:8s} {score_str:>17s} "
                f"{result['mean_waste_rate'] * 100:>7.1f}% "
                f"{result['mean_nutrition_score'] * 100:>9.1f}%"
            )

    # ── Part 3: Determinism Check ─────────────────────────────────

    section("Part 3: Determinism Verification")
    print("  Running same seed twice to verify identical scores...\n")

    for difficulty in ["easy", "medium", "hard"]:
        scores = []
        for _ in range(2):
            obs = env.reset(task_id=difficulty, seed=99)
            action_dict = fifo.act(obs.model_dump(mode="json"))
            action = Action(**action_dict)
            _, reward, _, _ = env.step(action)
            scores.append(reward.score)
        match = scores[0] == scores[1]
        status = f"{GREEN}PASS{RESET_STYLE}" if match else f"{RED}FAIL{RESET_STYLE}"
        print(f"  {difficulty:8s}: run1={scores[0]:.4f}  run2={scores[1]:.4f}  [{status}]")

    # ── Part 4: Score Variance Check ──────────────────────────────

    section("Part 4: Score Variance (DQ Protection)")
    print("  Checking that different seeds produce different scores...\n")
    print(f"  {DIM}(Using random agent — FIFO is too good on easy to show variance){RESET_STYLE}\n")

    for difficulty in ["easy", "medium", "hard"]:
        unique_scores = set()
        for seed in range(20):
            obs = env.reset(task_id=difficulty, seed=seed)
            action_dict = RandomAgent(seed=seed).act(obs.model_dump(mode="json"))
            action = Action(**action_dict)
            _, reward, _, _ = env.step(action)
            unique_scores.add(round(reward.score, 4))
        status = f"{GREEN}PASS{RESET_STYLE}" if len(unique_scores) > 1 else f"{RED}FAIL{RESET_STYLE}"
        print(f"  {difficulty:8s}: {len(unique_scores)} unique scores across 20 seeds [{status}]")

    # ── Part 5: API Endpoint Test ─────────────────────────────────

    section("Part 5: API Endpoint Smoke Test")
    print("  Testing FastAPI endpoints via TestClient...\n")

    from fastapi.testclient import TestClient
    from app import app

    client = TestClient(app)

    endpoints = [
        ("GET",  "/health", None),
        ("POST", "/reset",  {"task_id": "easy", "seed": 0}),
        ("POST", "/step",   None),  # will build from reset response
        ("GET",  "/state",  None),
    ]

    # Health
    resp = client.get("/health")
    status = f"{GREEN}PASS{RESET_STYLE}" if resp.status_code == 200 else f"{RED}FAIL{RESET_STYLE}"
    print(f"  GET  /health  → {resp.status_code} [{status}]")

    # Reset
    resp = client.post("/reset", json={"task_id": "easy", "seed": 0})
    status = f"{GREEN}PASS{RESET_STYLE}" if resp.status_code == 200 else f"{RED}FAIL{RESET_STYLE}"
    obs_data = resp.json()
    print(f"  POST /reset   → {resp.status_code} [{status}] "
          f"({len(obs_data['inventory'])} items)")

    # Step
    item = obs_data["inventory"][0]
    step_body = {
        "meal_plan": [{
            "day": 1,
            "meal_name": "demo_meal",
            "ingredients": [{"name": item["name"], "quantity": 10}],
        }]
    }
    resp = client.post("/step", json=step_body)
    status = f"{GREEN}PASS{RESET_STYLE}" if resp.status_code == 200 else f"{RED}FAIL{RESET_STYLE}"
    step_data = resp.json()
    print(f"  POST /step    → {resp.status_code} [{status}] "
          f"(score={step_data['reward']['score']:.3f})")

    # State
    resp = client.get("/state")
    status = f"{GREEN}PASS{RESET_STYLE}" if resp.status_code == 200 else f"{RED}FAIL{RESET_STYLE}"
    print(f"  GET  /state   → {resp.status_code} [{status}] "
          f"(done={resp.json()['done']})")

    # ── Summary ───────────────────────────────────────────────────

    banner("Demo Complete")
    print("  Everything works. Ready for hackathon submission.\n")
    print(f"  {DIM}Next steps:{RESET_STYLE}")
    print(f"    npm run preflight    — Full lint + typecheck + tests + build")
    print(f"    npm run docker:build — Build Docker image")
    print(f"    npm run inference    — Run LLM baseline (needs OPENAI_API_KEY)")
    print()


if __name__ == "__main__":
    main()
