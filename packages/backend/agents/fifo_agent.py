"""FIFO greedy baseline agent for FridgeEnv — uses soonest-expiring items first."""

from __future__ import annotations

from agents.base import BaseAgent


class FIFOAgent(BaseAgent):
    def act(self, observation: dict) -> dict:
        inventory = observation["inventory"]
        horizon = observation["horizon"]
        current_date = observation["current_date"]

        # Sort by expiry date ascending (soonest first)
        sorted_inv = sorted(inventory, key=lambda x: x["expiry_date"])

        # Track available quantities
        available = {item["name"]: item["quantity"] for item in inventory}
        category_map = {item["name"]: item["category"] for item in inventory}
        expiry_map = {item["name"]: item["expiry_date"] for item in inventory}

        meal_plan = []
        for day in range(1, horizon + 1):
            day_candidates = [i for i in sorted_inv if available.get(i["name"], 0) > 0]
            if not day_candidates:
                break

            ingredients = []
            used_names: set[str] = set()

            # Priority 1: use items expiring today or tomorrow (urgent)
            for item in day_candidates:
                name = item["name"]
                if name in used_names:
                    continue
                # Use all of items about to expire
                days_left = _days_between(current_date, expiry_map[name]) - day
                if days_left <= 1 and available[name] > 0:
                    portion = available[name]  # use everything
                    ingredients.append({"name": name, "quantity": round(portion, 1)})
                    available[name] = 0
                    used_names.add(name)

            # Priority 2: balanced meal (protein + carb + vegetable)
            for target_cat in ["protein", "carb", "vegetable"]:
                # Skip if we already have this category from urgent items
                if any(category_map.get(i["name"]) == target_cat for i in ingredients):
                    continue
                for item in day_candidates:
                    name = item["name"]
                    if name in used_names:
                        continue
                    if category_map.get(name) == target_cat and available[name] > 0:
                        # Use a fair share: divide remaining by days left
                        days_remaining = max(1, horizon - day + 1)
                        portion = available[name] / days_remaining
                        portion = max(portion, available[name] * 0.3)
                        portion = min(portion, available[name])
                        ingredients.append({"name": name, "quantity": round(portion, 1)})
                        available[name] -= portion
                        used_names.add(name)
                        break

            # Priority 3: fill with more soonest-expiring items
            for item in day_candidates:
                name = item["name"]
                if name in used_names or available[name] <= 0:
                    continue
                if len(ingredients) >= 5:
                    break
                days_left = _days_between(current_date, expiry_map[name]) - day
                days_remaining = max(1, horizon - day + 1)
                portion = available[name] / days_remaining
                portion = max(portion, available[name] * 0.2)
                portion = min(portion, available[name])
                if portion > 0:
                    ingredients.append({"name": name, "quantity": round(portion, 1)})
                    available[name] -= portion
                    used_names.add(name)

            if ingredients:
                meal_plan.append(
                    {
                        "day": day,
                        "meal_name": f"fifo_meal_day{day}",
                        "ingredients": ingredients,
                    }
                )

        return {"meal_plan": meal_plan}


def _days_between(date_str: str, expiry_str: str) -> int:
    """Compute days between two ISO date strings."""
    from datetime import date

    d1 = date.fromisoformat(date_str) if isinstance(date_str, str) else date_str
    d2 = date.fromisoformat(expiry_str) if isinstance(expiry_str, str) else expiry_str
    return (d2 - d1).days
