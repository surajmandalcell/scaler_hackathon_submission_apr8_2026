"""Seeded deterministic fridge state factory for FridgeEnv."""

from __future__ import annotations

import random
from datetime import date, timedelta

from env.data import (
    DIETARY_RESTRICTIONS,
    INGREDIENTS,
    IngredientDef,
    get_ingredients_by_category,
)
from env.models import FridgeItem, Observation

DIFFICULTY_PROFILES: dict[str, dict] = {
    "easy": {"items": (5, 8), "horizon": 3, "household_size": 2, "restrictions": 0},
    "medium": {"items": (10, 15), "horizon": 7, "household_size": 3, "restrictions": 1},
    "hard": {"items": (20, 30), "horizon": 14, "household_size": 4, "restrictions": 2},
}

CURRENT_DATE = date(2026, 1, 1)

# Sampling weights: perishables 2x, condiments 0.5x
_CATEGORY_WEIGHTS: dict[str, float] = {
    "protein": 2.0,
    "carb": 1.0,
    "vegetable": 2.0,
    "dairy": 2.0,
    "fruit": 1.5,
    "condiment": 0.5,
}


def _build_weights(ingredients: list[IngredientDef]) -> list[float]:
    return [_CATEGORY_WEIGHTS.get(i.category, 1.0) for i in ingredients]


def _ensure_category_present(
    selected: list[IngredientDef],
    category: str,
    rng: random.Random,
) -> list[IngredientDef]:
    """Ensure at least one item of the given category is present."""
    if any(i.category == category for i in selected):
        return selected
    candidates = get_ingredients_by_category(category)
    replacement = rng.choice(candidates)
    # Replace a random non-essential item (not protein/carb/vegetable if we still need them)
    replaceable = [
        idx for idx, i in enumerate(selected) if i.category not in ("protein", "carb", "vegetable")
    ]
    if not replaceable:
        # All items are essential categories — just append
        selected.append(replacement)
    else:
        selected[rng.choice(replaceable)] = replacement
    return selected


def _apply_clustering(
    expiry_dates: list[date],
    cluster_size: int,
    rng: random.Random,
) -> list[date]:
    """Force some items to share the same expiry date."""
    if len(expiry_dates) < cluster_size:
        return expiry_dates
    # Pick a cluster of items and set them to the same date
    indices = rng.sample(range(len(expiry_dates)), min(cluster_size, len(expiry_dates)))
    shared_date = expiry_dates[indices[0]]
    for idx in indices:
        expiry_dates[idx] = shared_date
    return expiry_dates


def generate_observation(seed: int, difficulty: str) -> Observation:
    """Generate a deterministic Observation for the given seed and difficulty."""
    if difficulty not in DIFFICULTY_PROFILES:
        raise ValueError(f"Unknown difficulty: {difficulty}. Use: {list(DIFFICULTY_PROFILES)}")

    profile = DIFFICULTY_PROFILES[difficulty]
    rng = random.Random(seed)

    # 1. Determine item count
    n = rng.randint(profile["items"][0], profile["items"][1])

    # 2. Sample ingredients with weighted selection (no duplicates)
    weights = _build_weights(INGREDIENTS)
    selected: list[IngredientDef] = []
    available = list(range(len(INGREDIENTS)))

    for _ in range(min(n, len(INGREDIENTS))):
        avail_weights = [weights[i] for i in available]
        chosen_idx = rng.choices(available, weights=avail_weights, k=1)[0]
        selected.append(INGREDIENTS[chosen_idx])
        available.remove(chosen_idx)

    # 3. Ensure solvability: at least 1 protein + 1 carb + 1 vegetable
    selected = _ensure_category_present(selected, "protein", rng)
    selected = _ensure_category_present(selected, "carb", rng)
    selected = _ensure_category_present(selected, "vegetable", rng)

    horizon = profile["horizon"]
    household_size = profile["household_size"]

    # 4. Generate expiry dates
    expiry_dates = [CURRENT_DATE + timedelta(days=rng.randint(1, horizon + 2)) for _ in selected]

    # 5. Apply clustering for medium/hard
    if difficulty == "medium":
        expiry_dates = _apply_clustering(expiry_dates, rng.randint(2, 3), rng)
    elif difficulty == "hard":
        # Apply two rounds of clustering for harder scenarios
        expiry_dates = _apply_clustering(expiry_dates, rng.randint(4, 6), rng)
        expiry_dates = _apply_clustering(expiry_dates, rng.randint(3, 5), rng)

    # 6. Scale quantities by household size
    quantities = [
        round(ing.default_qty * household_size * rng.uniform(0.5, 1.5), 1) for ing in selected
    ]

    # 7. Choose dietary restrictions
    num_restrictions = profile["restrictions"]
    if num_restrictions > 0:
        restrictions = rng.sample(DIETARY_RESTRICTIONS, num_restrictions)

        # Ensure at least 30% of items conflict with at least one restriction
        conflict_count = sum(
            1 for ing in selected if any(_ingredient_violates(ing, r) for r in restrictions)
        )
        min_conflicts = max(1, int(len(selected) * 0.3))

        # If not enough conflicts, swap in items that do conflict
        attempts = 0
        while conflict_count < min_conflicts and attempts < 20:
            # Find a non-conflicting item to replace
            non_conflicting = [
                idx
                for idx, ing in enumerate(selected)
                if not any(_ingredient_violates(ing, r) for r in restrictions)
            ]
            if not non_conflicting:
                break

            # Find a conflicting ingredient not already in selection
            selected_names = {i.name for i in selected}
            conflict_candidates = [
                ing
                for ing in INGREDIENTS
                if ing.name not in selected_names
                and any(_ingredient_violates(ing, r) for r in restrictions)
            ]
            if not conflict_candidates:
                break

            replace_idx = rng.choice(non_conflicting)
            new_ing = rng.choice(conflict_candidates)
            selected[replace_idx] = new_ing
            quantities[replace_idx] = round(
                new_ing.default_qty * household_size * rng.uniform(0.5, 1.5), 1
            )
            expiry_dates[replace_idx] = CURRENT_DATE + timedelta(days=rng.randint(1, horizon + 2))

            conflict_count = sum(
                1 for ing in selected if any(_ingredient_violates(ing, r) for r in restrictions)
            )
            attempts += 1
    else:
        restrictions = []

    # Re-ensure solvability after swaps
    selected = _ensure_category_present(selected, "protein", rng)
    selected = _ensure_category_present(selected, "carb", rng)
    selected = _ensure_category_present(selected, "vegetable", rng)

    # Pad quantities/expiry_dates if _ensure_category_present appended items
    while len(quantities) < len(selected):
        ing = selected[len(quantities)]
        quantities.append(round(ing.default_qty * household_size * rng.uniform(0.5, 1.5), 1))
        expiry_dates.append(CURRENT_DATE + timedelta(days=rng.randint(1, horizon + 2)))

    # 8. Build FridgeItems
    inventory = [
        FridgeItem(
            name=ing.name,
            quantity=qty,
            unit=ing.unit,
            expiry_date=exp,
            category=ing.category,
        )
        for ing, qty, exp in zip(selected, quantities, expiry_dates, strict=True)
    ]

    return Observation(
        inventory=inventory,
        current_date=CURRENT_DATE,
        horizon=horizon,
        household_size=household_size,
        dietary_restrictions=restrictions,
        done=False,
        reward=None,
    )


def _ingredient_violates(ingredient: IngredientDef, restriction: str) -> bool:
    """Check if an IngredientDef violates a restriction (internal helper)."""
    if restriction == "vegetarian":
        return ingredient.contains_meat
    if restriction == "lactose-free":
        return ingredient.contains_dairy
    if restriction == "gluten-free":
        return ingredient.contains_gluten
    return False
