"""LLM-based baseline agent for FridgeEnv using OpenAI API.

Runs 5 episodes per difficulty (easy, medium, hard) = 15 total LLM calls.
Saves everything to outputs/ directory.

Environment variables:
    OPENAI_API_KEY  - API key (required)
    API_BASE_URL    - LLM API base URL (default: https://api.openai.com/v1)
    MODEL_NAME      - Model to use (default: gpt-4o-mini)
    ENV_SERVER_URL  - FridgeEnv server URL (default: http://localhost:7860)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx
from openai import OpenAI

# Resolve paths relative to this script, not CWD
SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "outputs"

ENV_SERVER_URL = os.environ.get("ENV_SERVER_URL", "http://localhost:7860")
API_BASE_URL = os.environ.get("API_BASE_URL", None)
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

    # Create outputs directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / run_id
    run_dir.mkdir(exist_ok=True)

    # Build OpenAI client
    client_kwargs = {"api_key": api_key}
    if API_BASE_URL:
        client_kwargs["base_url"] = API_BASE_URL
    client = OpenAI(**client_kwargs)

    server = httpx.Client(base_url=ENV_SERVER_URL, timeout=60.0)

    print(f"LLM: {MODEL_NAME} @ {API_BASE_URL or 'default OpenAI'}")
    print(f"Env: {ENV_SERVER_URL}")
    print(f"Output: {run_dir}")
    print()

    results: dict = {}
    all_episodes: list[dict] = []

    for task_id in ["easy", "medium", "hard"]:
        scores = []
        task_dir = run_dir / task_id
        task_dir.mkdir(exist_ok=True)

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
            raw_response = None
            for attempt in range(3):
                try:
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_msg},
                        ],
                        temperature=0.0,
                    )
                    raw_response = response.choices[0].message.content
                    raw = raw_response.strip()
                    if raw.startswith("```"):
                        lines = raw.split("\n")
                        raw = "\n".join(
                            l for l in lines if not l.strip().startswith("```")
                        )
                    meal_plan = json.loads(raw)
                    if "meal_plan" not in meal_plan:
                        meal_plan = None
                        continue
                    break
                except (json.JSONDecodeError, Exception) as e:
                    print(
                        f"retry({attempt+1}: {type(e).__name__})",
                        end=" ",
                        flush=True,
                    )
                    continue

            if meal_plan is None:
                meal_plan = {"meal_plan": []}
                print("fallback", end=" ")

            # Submit to environment
            step_result = server.post("/step", json=meal_plan).json()
            score = step_result["reward"]["score"]
            scores.append(score)
            print(f"score={score:.3f}")

            # Save episode detail
            episode = {
                "task_id": task_id,
                "seed": seed,
                "observation": obs,
                "meal_plan": meal_plan,
                "raw_llm_response": raw_response,
                "reward": step_result["reward"],
                "info": step_result.get("info", {}),
            }
            all_episodes.append(episode)

            # Save individual episode file
            ep_file = task_dir / f"seed_{seed}.json"
            with open(ep_file, "w") as f:
                json.dump(episode, f, indent=2, default=str)

        results[task_id] = {
            "mean_score": sum(scores) / len(scores),
            "scores": scores,
            "episodes": len(scores),
        }

    # Save summary results
    results_file = run_dir / "results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    # Also save to project root for hackathon submission
    with open(SCRIPT_DIR / "results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 50}")
    print("Results:")
    for task_id, data in results.items():
        print(f"  {task_id}: mean={data['mean_score']:.3f} scores={data['scores']}")
    print(f"\nSaved to: {run_dir}")
    print(f"  results.json        — score summary")
    print(f"  easy/seed_0.json    — full episode detail (observation, meal plan, reward)")
    print(f"  medium/seed_0.json  — ...")
    print(f"  hard/seed_0.json    — ...")

    return results


if __name__ == "__main__":
    run_inference()
