"""LLM-based baseline agent for FridgeEnv using OpenAI API.

Runs 5 episodes per difficulty (easy, medium, hard) = 15 total LLM calls.
Produces results.json with scores.
"""

from __future__ import annotations

import json
import os
import sys

import httpx
from openai import OpenAI

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")

SYSTEM_PROMPT = """You are a meal planning agent. Given a fridge inventory with expiry dates, produce a meal plan that minimizes food waste.

Rules:
- Prioritize items expiring soonest — use them first
- Each day should include protein, carb, and vegetable for balanced nutrition
- Respect dietary restrictions — never use restricted items
- Use realistic portions (100-300g per ingredient per meal)
- Plan meals for EVERY day in the horizon

Return ONLY valid JSON matching this schema:
{"meal_plan": [{"day": int, "meal_name": string, "ingredients": [{"name": string, "quantity": float}]}]}"""

USER_TEMPLATE = """Fridge inventory:
{inventory}

Planning horizon: {horizon} days
Household size: {household_size} people
Dietary restrictions: {restrictions}
Current date: {current_date}

Create a meal plan that uses as many items as possible before they expire. Return JSON only."""


def format_inventory(items: list[dict]) -> str:
    lines = []
    for item in items:
        lines.append(
            f"  - {item['name']}: {item['quantity']}{item['unit']}, "
            f"expires {item['expiry_date']}, category: {item['category']}"
        )
    return "\n".join(lines)


def run_inference() -> dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    server = httpx.Client(base_url=API_BASE_URL, timeout=30.0)
    results: dict = {}

    for task_id in ["easy", "medium", "hard"]:
        scores = []
        for seed in range(5):
            print(f"  {task_id} seed={seed}...", end=" ", flush=True)

            # Reset environment
            obs = server.post("/reset", json={"task_id": task_id, "seed": seed}).json()

            # Build LLM prompt
            user_msg = USER_TEMPLATE.format(
                inventory=format_inventory(obs["inventory"]),
                horizon=obs["horizon"],
                household_size=obs["household_size"],
                restrictions=obs.get("dietary_restrictions", []) or "none",
                current_date=obs["current_date"],
            )

            # Call LLM with retries
            meal_plan = None
            for attempt in range(3):
                try:
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_msg},
                        ],
                        temperature=0.0,
                        response_format={"type": "json_object"},
                    )
                    raw = response.choices[0].message.content
                    meal_plan = json.loads(raw)
                    # Validate structure
                    if "meal_plan" not in meal_plan:
                        meal_plan = None
                        continue
                    break
                except (json.JSONDecodeError, Exception) as e:
                    print(f"retry({attempt+1})", end=" ", flush=True)
                    continue

            if meal_plan is None:
                meal_plan = {"meal_plan": []}
                print("fallback", end=" ")

            # Submit to environment
            result = server.post("/step", json=meal_plan).json()
            score = result["reward"]["score"]
            scores.append(score)
            print(f"score={score:.3f}")

        results[task_id] = {
            "mean_score": sum(scores) / len(scores),
            "scores": scores,
            "episodes": len(scores),
        }

    # Save results
    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== Results ===")
    for task_id, data in results.items():
        print(f"  {task_id}: mean={data['mean_score']:.3f} scores={data['scores']}")

    return results


if __name__ == "__main__":
    run_inference()
