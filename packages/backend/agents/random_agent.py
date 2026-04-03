"""Random baseline agent for FridgeEnv."""

from __future__ import annotations

import random

from agents.base import BaseAgent


class RandomAgent(BaseAgent):
    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)

    def act(self, observation: dict) -> dict:
        inventory = observation["inventory"]
        horizon = observation["horizon"]

        meal_plan = []
        # Track available quantities locally
        available = {item["name"]: item["quantity"] for item in inventory}

        for day in range(1, horizon + 1):
            num_items = self._rng.randint(2, min(4, len(inventory)))
            candidates = [i for i in inventory if available.get(i["name"], 0) > 0]
            if not candidates:
                break

            chosen = self._rng.sample(candidates, min(num_items, len(candidates)))
            ingredients = []
            for item in chosen:
                fraction = self._rng.uniform(0.1, 0.5)
                qty = available[item["name"]] * fraction
                if qty > 0:
                    ingredients.append({"name": item["name"], "quantity": round(qty, 1)})
                    available[item["name"]] -= qty

            if ingredients:
                meal_plan.append(
                    {
                        "day": day,
                        "meal_name": f"random_meal_day{day}",
                        "ingredients": ingredients,
                    }
                )

        return {"meal_plan": meal_plan}
