"""Core FridgeEnv environment implementing OpenEnv reset/step/state interface."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from env.data import INGREDIENT_INDEX, violates_restriction
from env.generator import generate_observation
from env.models import Action, FridgeItem, Observation, Reward
from env.scorer import compute_reward


class FridgeEnv:
    """OpenEnv-compliant RL environment for food waste reduction."""

    def __init__(self) -> None:
        self._observation: Observation | None = None
        self._original_inventory: list[FridgeItem] = []
        self._inventory: dict[str, float] = {}  # mutable: name -> remaining qty
        self._done: bool = False
        self._reward: Reward | None = None
        self._task_id: str | None = None
        self._seed: int | None = None

    def reset(
        self,
        task_id: str = "custom",
        seed: int = 0,
        custom_observation: Observation | None = None,
    ) -> Observation:
        """Generate a new episode. Returns initial observation.

        If custom_observation is provided, uses it directly instead of generating.
        """
        if custom_observation is not None:
            obs = custom_observation
        else:
            obs = generate_observation(seed, task_id)
        self._observation = obs
        self._original_inventory = list(obs.inventory)
        self._inventory = {item.name: item.quantity for item in obs.inventory}
        self._done = False
        self._reward = None
        self._task_id = task_id
        self._seed = seed
        return obs

    def step(self, action: Action) -> tuple[Observation, Reward, bool, dict]:
        """Execute the meal plan and return results. Single-step episode."""
        if self._observation is None:
            raise ValueError("Call reset() before step().")
        if self._done:
            raise ValueError("Episode already done. Call reset() first.")

        obs = self._observation
        horizon = obs.horizon
        current_date = obs.current_date
        restrictions = obs.dietary_restrictions

        # Build item expiry lookup
        expiry_map: dict[str, int] = {}  # name -> days until expiry from current_date
        for item in obs.inventory:
            expiry_map[item.name] = (item.expiry_date - current_date).days

        # Build category lookup from original inventory
        category_map: dict[str, str] = {}
        for item in obs.inventory:
            category_map[item.name] = item.category

        # Simulation state
        consumption_log: dict[str, float] = defaultdict(float)
        nutrition_log: dict[int, set[str]] = {}
        violation_log: list[str] = []
        warnings: list[str] = []

        # Group meals by day
        meals_by_day: dict[int, list] = defaultdict(list)
        for meal in action.meal_plan:
            meals_by_day[meal.day].append(meal)

        # Day-by-day simulation
        for day in range(1, horizon + 1):
            day_categories: set[str] = set()

            # Process meals for this day
            for meal in meals_by_day.get(day, []):
                for ingredient in meal.ingredients:
                    name = ingredient.name
                    requested_qty = ingredient.quantity

                    # Check if item exists in inventory
                    if name not in self._inventory:
                        warnings.append(f"Day {day}: {name} not in inventory, skipped")
                        continue

                    # Check if item has already expired
                    if expiry_map.get(name, 0) < day:
                        warnings.append(f"Day {day}: {name} already expired, skipped")
                        continue

                    # Check available quantity
                    available = self._inventory[name]
                    if available <= 0:
                        warnings.append(f"Day {day}: {name} fully consumed, skipped")
                        continue

                    # Clamp to available
                    used_qty = min(requested_qty, available)

                    # Check dietary restrictions
                    for restriction in restrictions:
                        if violates_restriction(name, restriction):
                            violation_log.append(f"Day {day}: {name} violates {restriction}")

                    # Deduct from inventory
                    self._inventory[name] -= used_qty
                    consumption_log[name] += used_qty

                    # Track category for nutrition
                    cat = category_map.get(name) or (
                        INGREDIENT_INDEX[name].category if name in INGREDIENT_INDEX else None
                    )
                    if cat:
                        day_categories.add(cat)

            nutrition_log[day] = day_categories

            # Expire items at end of day
            # Items with expiry_date <= current_date + day are expired after this day
            # (item is usable ON its expiry day, expired AFTER)

        # Collect expiry events: perishable items with remaining qty whose expiry has passed
        expiry_events: list[str] = []
        for item in self._original_inventory:
            days_until = (item.expiry_date - current_date).days
            remaining = self._inventory.get(item.name, 0)
            if remaining > 0 and days_until <= horizon:
                expiry_events.append(item.name)

        # Compute reward
        reward = compute_reward(
            original_inventory=self._original_inventory,
            consumption_log=dict(consumption_log),
            expiry_events=expiry_events,
            nutrition_log=nutrition_log,
            violation_log=violation_log,
            horizon=horizon,
        )

        # Build final observation
        final_inventory = [
            FridgeItem(
                name=item.name,
                quantity=max(0.01, self._inventory.get(item.name, 0)),
                unit=item.unit,
                expiry_date=item.expiry_date,
                category=item.category,
            )
            for item in self._original_inventory
            if self._inventory.get(item.name, 0) > 0
        ]

        final_obs = Observation(
            inventory=final_inventory,
            current_date=current_date + timedelta(days=horizon),
            horizon=horizon,
            household_size=obs.household_size,
            dietary_restrictions=restrictions,
            done=True,
            reward=reward.score,
        )

        self._done = True
        self._reward = reward
        self._observation = final_obs

        info = {
            "consumption_log": dict(consumption_log),
            "expiry_events": expiry_events,
            "nutrition_log": {k: list(v) for k, v in nutrition_log.items()},
            "violation_log": violation_log,
            "warnings": warnings,
        }

        return final_obs, reward, True, info

    def state(self) -> dict:
        """Return current environment state snapshot."""
        if self._observation is None:
            raise ValueError("No active episode. Call reset() first.")
        return {
            "task_id": self._task_id,
            "seed": self._seed,
            "done": self._done,
            "inventory": [i.model_dump(mode="json") for i in self._observation.inventory],
            "reward": self._reward.model_dump(mode="json") if self._reward else None,
        }
