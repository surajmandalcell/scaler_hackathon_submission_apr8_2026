"""Pydantic models for FridgeEnv OpenEnv interface."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class FridgeItem(BaseModel):
    name: str
    quantity: float = Field(gt=0)
    unit: str
    expiry_date: date
    category: str


class Observation(BaseModel):
    inventory: list[FridgeItem]
    current_date: date
    horizon: int = Field(ge=3, le=14)
    household_size: int = Field(ge=2, le=4)
    dietary_restrictions: list[str] = Field(default_factory=list)
    # OpenEnv base fields
    done: bool = False
    reward: float | None = None
    metadata: dict = Field(default_factory=dict)  # type: ignore[type-arg]


class MealIngredient(BaseModel):
    name: str
    quantity: float = Field(gt=0)


class Meal(BaseModel):
    day: int = Field(ge=1)
    meal_name: str
    ingredients: list[MealIngredient] = Field(min_length=1)


class Action(BaseModel):
    meal_plan: list[Meal]


class Reward(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    waste_rate: float
    nutrition_score: float
    items_used: int
    items_expired: int
    violations: list[str]
