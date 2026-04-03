"""Unit tests for env/scorer.py — deterministic scoring."""

from datetime import date

from env.models import FridgeItem
from env.scorer import compute_grader_score, compute_reward


def _item(name: str, qty: float = 100, category: str = "protein") -> FridgeItem:
    return FridgeItem(
        name=name,
        quantity=qty,
        unit="g",
        expiry_date=date(2026, 1, 5),
        category=category,
    )


def test_perfect_score():
    inventory = [_item("a"), _item("b"), _item("c")]
    consumption = {"a": 100, "b": 100, "c": 100}
    r = compute_reward(inventory, consumption, [], {}, [], horizon=3)
    assert r.score == 1.0


def test_zero_score():
    inventory = [_item("a"), _item("b")]
    r = compute_reward(inventory, {}, ["a", "b"], {}, [], horizon=3)
    assert r.score == 0.0


def test_partial_consumption():
    inventory = [_item("a"), _item("b"), _item("c"), _item("d")]
    consumption = {"a": 50, "b": 50}  # 2 of 4 used
    r = compute_reward(inventory, consumption, ["c", "d"], {}, [], horizon=3)
    assert r.score == 0.5


def test_condiments_excluded_from_waste():
    inventory = [
        _item("chicken", category="protein"),
        _item("olive_oil", category="condiment"),
    ]
    # Only chicken consumed, olive_oil untouched but it's condiment
    consumption = {"chicken": 100}
    r = compute_reward(inventory, consumption, [], {}, [], horizon=3)
    # 1 perishable (chicken), 1 used = 1.0
    assert r.score == 1.0
    assert r.waste_rate == 0.0


def test_nutrition_bonus():
    nutrition_log = {
        1: {"protein", "carb", "vegetable"},
        2: {"protein", "carb", "vegetable"},
        3: {"protein"},
    }
    inventory = [_item("a")]
    consumption = {"a": 100}
    r = compute_reward(inventory, consumption, [], nutrition_log, [], horizon=3)
    assert r.nutrition_score == 2 / 3


def test_nutrition_penalty_missing_category():
    nutrition_log = {1: {"protein", "carb"}}  # no vegetable
    inventory = [_item("a")]
    consumption = {"a": 100}
    r = compute_reward(inventory, consumption, [], nutrition_log, [], horizon=3)
    assert r.nutrition_score == 0.0


def test_dietary_violation_penalty():
    violations = ["used chicken_breast in vegetarian plan"]
    inventory = [_item("a")]
    consumption = {"a": 100}
    r = compute_reward(inventory, consumption, [], {}, violations, horizon=3)
    assert len(r.violations) == 1


def test_multiple_violations():
    violations = ["v1", "v2", "v3"]
    inventory = [_item("a")]
    consumption = {"a": 100}
    r = compute_reward(inventory, consumption, [], {}, violations, horizon=3)
    assert len(r.violations) == 3


def test_grader_score_range():
    """Grader score must always be in [0.0, 1.0]."""
    inventory = [_item("a"), _item("b")]
    for consumed in [{}, {"a": 50}, {"a": 100, "b": 100}]:
        r = compute_reward(inventory, consumed, [], {}, [], horizon=3)
        assert 0.0 <= r.score <= 1.0


def test_waste_rate_calculation():
    inventory = [_item("a"), _item("b"), _item("c")]
    # 1 of 3 perishable items expired
    r = compute_reward(inventory, {"a": 100, "b": 100}, ["c"], {}, [], horizon=3)
    assert abs(r.waste_rate - 1 / 3) < 0.01


def test_nutrition_score_calculation():
    nutrition_log = {
        1: {"protein", "carb", "vegetable"},
        2: {"protein", "carb", "vegetable"},
        3: {"protein", "carb", "vegetable"},
        4: {"carb"},
        5: {"protein"},
    }
    inventory = [_item("a")]
    consumption = {"a": 100}
    r = compute_reward(inventory, consumption, [], nutrition_log, [], horizon=5)
    assert r.nutrition_score == 3 / 5


def test_empty_inventory():
    r = compute_reward([], {}, [], {}, [], horizon=3)
    assert r.score == 1.0  # nothing to waste
    assert r.waste_rate == 0.0


def test_deterministic():
    inventory = [_item("a"), _item("b")]
    consumption = {"a": 50}
    r1 = compute_reward(inventory, consumption, ["b"], {}, [], horizon=3)
    r2 = compute_reward(inventory, consumption, ["b"], {}, [], horizon=3)
    assert r1 == r2


def test_items_used_count():
    inventory = [_item("a"), _item("b"), _item("c")]
    consumption = {"a": 10, "c": 5}
    r = compute_reward(inventory, consumption, [], {}, [], horizon=3)
    assert r.items_used == 2


def test_items_expired_count():
    inventory = [_item("a"), _item("b")]
    r = compute_reward(inventory, {}, ["a", "b"], {}, [], horizon=3)
    assert r.items_expired == 2


def test_grader_score_standalone():
    inventory = [_item("a"), _item("b"), _item("c", category="condiment")]
    consumption = {"a": 10}
    # condiment excluded: 1 of 2 perishable used
    score = compute_grader_score(inventory, consumption)
    assert score == 0.5
