"""Integration tests for the env reset->step->reward pipeline."""

from env.fridge_env import FridgeEnv
from env.models import Action, Meal, MealIngredient


def _use_all_items_action(obs) -> Action:
    """Build an action that uses all inventory items across all days."""
    meals = []
    for day in range(1, obs.horizon + 1):
        ingredients = [
            MealIngredient(name=item.name, quantity=item.quantity / obs.horizon)
            for item in obs.inventory
        ]
        meals.append(Meal(day=day, meal_name=f"day{day}", ingredients=ingredients))
    return Action(meal_plan=meals)


def test_reset_step_roundtrip_easy():
    env = FridgeEnv()
    obs = env.reset("easy", seed=0)
    action = _use_all_items_action(obs)
    _, reward, done, _ = env.step(action)
    assert done is True
    assert 0.0 <= reward.score <= 1.0


def test_reset_step_roundtrip_medium():
    env = FridgeEnv()
    obs = env.reset("medium", seed=0)
    action = _use_all_items_action(obs)
    _, reward, done, _ = env.step(action)
    assert done is True
    assert 0.0 <= reward.score <= 1.0


def test_reset_step_roundtrip_hard():
    env = FridgeEnv()
    obs = env.reset("hard", seed=0)
    action = _use_all_items_action(obs)
    _, reward, done, _ = env.step(action)
    assert done is True
    assert 0.0 <= reward.score <= 1.0


def test_deterministic_pipeline():
    """Same seed must produce same reward."""
    scores = []
    for _ in range(3):
        env = FridgeEnv()
        obs = env.reset("easy", seed=42)
        action = _use_all_items_action(obs)
        _, reward, _, _ = env.step(action)
        scores.append(reward.score)
    assert all(s == scores[0] for s in scores)


def test_different_seeds_different_rewards():
    """Different seeds should produce different scores (not constant)."""
    scores = set()
    for seed in range(20):
        env = FridgeEnv()
        obs = env.reset("easy", seed=seed)
        # Use only the first item (partial plan) so scores vary by inventory composition
        item = obs.inventory[0]
        action = Action(
            meal_plan=[
                Meal(
                    day=1,
                    meal_name="partial",
                    ingredients=[MealIngredient(name=item.name, quantity=item.quantity * 0.5)],
                )
            ]
        )
        _, reward, _, _ = env.step(action)
        scores.add(round(reward.score, 4))
    # At least some variance
    assert len(scores) > 1, "All seeds produced identical scores — grader may be broken"
