"""Unit tests for env/models.py — Pydantic models."""

from datetime import date

import pytest
from pydantic import ValidationError

from env.models import Action, FridgeItem, Meal, MealIngredient, Observation, Reward


def test_fridge_item_valid():
    item = FridgeItem(
        name="chicken_breast",
        quantity=500,
        unit="g",
        expiry_date=date(2026, 1, 5),
        category="protein",
    )
    assert item.name == "chicken_breast"
    assert item.quantity == 500


def test_fridge_item_negative_qty_rejected():
    with pytest.raises(ValidationError):
        FridgeItem(
            name="chicken_breast",
            quantity=-1,
            unit="g",
            expiry_date=date(2026, 1, 5),
            category="protein",
        )


def test_observation_valid():
    obs = Observation(
        inventory=[
            FridgeItem(
                name="tofu",
                quantity=400,
                unit="g",
                expiry_date=date(2026, 1, 5),
                category="protein",
            ),
        ],
        current_date=date(2026, 1, 1),
        horizon=3,
        household_size=2,
        dietary_restrictions=[],
    )
    assert obs.done is False
    assert obs.reward is None
    assert len(obs.inventory) == 1


def test_observation_horizon_bounds():
    base = dict(
        inventory=[],
        current_date=date(2026, 1, 1),
        household_size=2,
        dietary_restrictions=[],
    )
    with pytest.raises(ValidationError):
        Observation(**base, horizon=2)
    with pytest.raises(ValidationError):
        Observation(**base, horizon=15)
    Observation(**base, horizon=3)
    Observation(**base, horizon=14)


def test_observation_household_bounds():
    base = dict(
        inventory=[],
        current_date=date(2026, 1, 1),
        horizon=3,
        dietary_restrictions=[],
    )
    with pytest.raises(ValidationError):
        Observation(**base, household_size=1)
    with pytest.raises(ValidationError):
        Observation(**base, household_size=5)
    Observation(**base, household_size=2)
    Observation(**base, household_size=4)


def test_observation_serialization_roundtrip():
    obs = Observation(
        inventory=[
            FridgeItem(
                name="tofu",
                quantity=400,
                unit="g",
                expiry_date=date(2026, 1, 5),
                category="protein",
            ),
        ],
        current_date=date(2026, 1, 1),
        horizon=7,
        household_size=3,
        dietary_restrictions=["vegetarian"],
    )
    data = obs.model_dump(mode="json")
    obs2 = Observation(**data)
    assert obs2.inventory[0].name == "tofu"
    assert obs2.horizon == 7


def test_meal_ingredient_valid():
    mi = MealIngredient(name="tofu", quantity=200)
    assert mi.name == "tofu"
    assert mi.quantity == 200


def test_meal_requires_ingredients():
    with pytest.raises(ValidationError):
        Meal(day=1, meal_name="empty_meal", ingredients=[])


def test_action_valid():
    action = Action(
        meal_plan=[
            Meal(
                day=1,
                meal_name="stir_fry",
                ingredients=[
                    MealIngredient(name="tofu", quantity=200),
                    MealIngredient(name="broccoli", quantity=150),
                ],
            ),
            Meal(
                day=2,
                meal_name="rice_bowl",
                ingredients=[
                    MealIngredient(name="white_rice", quantity=300),
                ],
            ),
        ]
    )
    assert len(action.meal_plan) == 2


def test_reward_score_bounds():
    with pytest.raises(ValidationError):
        Reward(
            score=-0.1,
            waste_rate=0,
            nutrition_score=0,
            items_used=0,
            items_expired=0,
            violations=[],
        )
    with pytest.raises(ValidationError):
        Reward(
            score=1.1, waste_rate=0, nutrition_score=0, items_used=0, items_expired=0, violations=[]
        )


def test_reward_valid():
    r = Reward(
        score=0.75,
        waste_rate=0.25,
        nutrition_score=0.8,
        items_used=5,
        items_expired=2,
        violations=["used meat in vegetarian plan"],
    )
    assert r.score == 0.75
    assert len(r.violations) == 1


def test_observation_has_openenv_fields():
    obs = Observation(
        inventory=[],
        current_date=date(2026, 1, 1),
        horizon=3,
        household_size=2,
        dietary_restrictions=[],
    )
    assert hasattr(obs, "done")
    assert hasattr(obs, "reward")
    assert hasattr(obs, "metadata")
    assert obs.done is False
    assert obs.reward is None
    assert obs.metadata == {}
