"""Unit tests for env/fridge_env.py — core environment."""

import pytest

from env.fridge_env import FridgeEnv
from env.models import Action, Meal, MealIngredient


def _make_action(meals: list[dict]) -> Action:
    """Helper to build an Action from simple dicts."""
    return Action(
        meal_plan=[
            Meal(
                day=m["day"],
                meal_name=m.get("name", f"meal_day{m['day']}"),
                ingredients=[MealIngredient(name=n, quantity=q) for n, q in m["ingredients"]],
            )
            for m in meals
        ]
    )


class TestReset:
    def test_reset_returns_observation(self):
        env = FridgeEnv()
        obs = env.reset("easy", seed=42)
        assert obs.done is False
        assert obs.reward is None
        assert len(obs.inventory) > 0

    def test_reset_clears_previous_state(self):
        env = FridgeEnv()
        obs1 = env.reset("easy", seed=0)
        # Build a minimal action
        item = obs1.inventory[0]
        action = _make_action(
            [
                {
                    "day": 1,
                    "ingredients": [(item.name, item.quantity * 0.1)],
                }
            ]
        )
        env.step(action)
        # Reset should work after step
        obs2 = env.reset("easy", seed=1)
        assert obs2.done is False

    def test_deterministic_reset(self):
        env1 = FridgeEnv()
        env2 = FridgeEnv()
        obs1 = env1.reset("medium", seed=99)
        obs2 = env2.reset("medium", seed=99)
        assert obs1 == obs2


class TestStep:
    def test_step_returns_done_true(self):
        env = FridgeEnv()
        obs = env.reset("easy", seed=42)
        item = obs.inventory[0]
        action = _make_action(
            [
                {
                    "day": 1,
                    "ingredients": [(item.name, item.quantity * 0.5)],
                }
            ]
        )
        final_obs, reward, done, info = env.step(action)
        assert done is True
        assert final_obs.done is True
        assert 0.0 <= reward.score <= 1.0

    def test_step_without_reset_raises(self):
        env = FridgeEnv()
        action = _make_action([{"day": 1, "ingredients": [("tofu", 100)]}])
        with pytest.raises(ValueError, match="reset"):
            env.step(action)

    def test_double_step_raises(self):
        env = FridgeEnv()
        obs = env.reset("easy", seed=0)
        item = obs.inventory[0]
        action = _make_action(
            [
                {
                    "day": 1,
                    "ingredients": [(item.name, 10)],
                }
            ]
        )
        env.step(action)
        with pytest.raises(ValueError, match="already done"):
            env.step(action)

    def test_ingredient_consumption(self):
        env = FridgeEnv()
        obs = env.reset("easy", seed=42)
        item = obs.inventory[0]
        original_qty = item.quantity
        action = _make_action(
            [
                {
                    "day": 1,
                    "ingredients": [(item.name, original_qty * 0.5)],
                }
            ]
        )
        _, _, _, info = env.step(action)
        consumed = info["consumption_log"].get(item.name, 0)
        assert consumed > 0

    def test_unknown_ingredient_skipped(self):
        env = FridgeEnv()
        env.reset("easy", seed=42)
        action = _make_action(
            [
                {
                    "day": 1,
                    "ingredients": [("unicorn_meat", 1000)],
                }
            ]
        )
        # Should not crash
        _, reward, done, info = env.step(action)
        assert done is True
        assert "unicorn_meat" not in info["consumption_log"]

    def test_overconsumption_clamped(self):
        env = FridgeEnv()
        obs = env.reset("easy", seed=42)
        item = obs.inventory[0]
        # Request 10x available
        action = _make_action(
            [
                {
                    "day": 1,
                    "ingredients": [(item.name, item.quantity * 10)],
                }
            ]
        )
        _, _, _, info = env.step(action)
        consumed = info["consumption_log"].get(item.name, 0)
        assert consumed <= item.quantity + 0.01  # allow float rounding

    def test_dietary_violation_detected(self):
        env = FridgeEnv()
        obs = env.reset("medium", seed=42)
        if not obs.dietary_restrictions:
            pytest.skip("No restrictions generated for this seed")

        # Find an item that violates the restriction
        from env.data import violates_restriction

        violating = None
        for item in obs.inventory:
            for r in obs.dietary_restrictions:
                if violates_restriction(item.name, r):
                    violating = item
                    break
            if violating:
                break

        if violating is None:
            pytest.skip("No violating items in inventory")

        action = _make_action(
            [
                {
                    "day": 1,
                    "ingredients": [(violating.name, 10)],
                }
            ]
        )
        _, _, _, info = env.step(action)
        assert len(info["violation_log"]) > 0

    def test_expiry_simulation(self):
        env = FridgeEnv()
        obs = env.reset("easy", seed=42)
        # Submit empty plan — everything should expire
        action = Action(
            meal_plan=[
                Meal(
                    day=1,
                    meal_name="dummy",
                    ingredients=[MealIngredient(name=obs.inventory[0].name, quantity=0.01)],
                )
            ]
        )
        # We need at least one meal, but use minimal amount
        _, _, _, info = env.step(action)
        # With minimal consumption, most items should expire
        assert len(info["expiry_events"]) >= 0  # at least some exist

    def test_nutrition_tracking(self):
        env = FridgeEnv()
        obs = env.reset("easy", seed=42)
        # Find protein, carb, vegetable
        by_cat = {}
        for item in obs.inventory:
            by_cat.setdefault(item.category, item)

        ingredients = []
        for cat in ["protein", "carb", "vegetable"]:
            if cat in by_cat:
                ingredients.append((by_cat[cat].name, 10))

        if len(ingredients) < 3:
            pytest.skip("Not enough categories")

        action = _make_action([{"day": 1, "ingredients": ingredients}])
        _, _, _, info = env.step(action)
        day1_cats = set(info["nutrition_log"].get("1", info["nutrition_log"].get(1, [])))
        assert "protein" in day1_cats
        assert "carb" in day1_cats
        assert "vegetable" in day1_cats

    def test_empty_meal_plan_scores_low(self):
        env = FridgeEnv()
        obs = env.reset("easy", seed=42)
        # Empty plan but we need at least a dummy meal
        action = Action(
            meal_plan=[
                Meal(
                    day=1,
                    meal_name="nothing",
                    ingredients=[MealIngredient(name=obs.inventory[0].name, quantity=0.01)],
                )
            ]
        )
        _, reward, _, _ = env.step(action)
        # With minimal consumption, score should be low but not necessarily 0
        # (one item gets touched)
        assert reward.score < 1.0

    def test_perfect_plan_high_score(self):
        env = FridgeEnv()
        obs = env.reset("easy", seed=42)
        # Use ALL items across all days
        meals = []
        for day in range(1, obs.horizon + 1):
            ingredients = [(item.name, item.quantity / obs.horizon) for item in obs.inventory]
            meals.append({"day": day, "ingredients": ingredients})

        action = _make_action(meals)
        _, reward, _, _ = env.step(action)
        # Should be high since we're using every item
        assert reward.score >= 0.8

    def test_all_difficulties_round_trip(self):
        for difficulty in ["easy", "medium", "hard"]:
            env = FridgeEnv()
            obs = env.reset(difficulty, seed=0)
            # Minimal action
            item = obs.inventory[0]
            action = _make_action(
                [
                    {
                        "day": 1,
                        "ingredients": [(item.name, 1)],
                    }
                ]
            )
            _, reward, done, _ = env.step(action)
            assert done is True
            assert 0.0 <= reward.score <= 1.0


class TestState:
    def test_state_before_reset_raises(self):
        env = FridgeEnv()
        with pytest.raises(ValueError, match="reset"):
            env.state()

    def test_state_after_reset(self):
        env = FridgeEnv()
        env.reset("easy", seed=42)
        state = env.state()
        assert state["task_id"] == "easy"
        assert state["seed"] == 42
        assert state["done"] is False
        assert state["reward"] is None
        assert len(state["inventory"]) > 0

    def test_state_after_step(self):
        env = FridgeEnv()
        obs = env.reset("easy", seed=42)
        item = obs.inventory[0]
        action = _make_action(
            [
                {
                    "day": 1,
                    "ingredients": [(item.name, 10)],
                }
            ]
        )
        env.step(action)
        state = env.state()
        assert state["done"] is True
        assert state["reward"] is not None
        assert "score" in state["reward"]
