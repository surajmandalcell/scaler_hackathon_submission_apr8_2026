"""Deterministic scoring for FridgeEnv."""

from __future__ import annotations

from env.models import FridgeItem, Reward


def compute_reward(
    original_inventory: list[FridgeItem],
    consumption_log: dict[str, float],
    expiry_events: list[str],
    nutrition_log: dict[int, set[str]],
    violation_log: list[str],
    horizon: int,
) -> Reward:
    """Compute the full reward signal from simulation logs.

    Args:
        original_inventory: The initial inventory before simulation.
        consumption_log: item_name -> total quantity consumed.
        expiry_events: Names of items that expired with remaining quantity.
        nutrition_log: day -> set of categories present in meals that day.
        violation_log: List of dietary violation descriptions.
        horizon: Number of days in the planning horizon.
    """
    # Separate perishable items (condiments excluded from waste scoring)
    perishable = [i for i in original_inventory if i.category != "condiment"]

    # --- Grader score (OpenEnv validation) ---
    if not perishable:
        grader_score = 1.0
    else:
        used_before_expiry = sum(1 for i in perishable if consumption_log.get(i.name, 0) > 0)
        grader_score = used_before_expiry / len(perishable)

    # --- Waste rate ---
    expired_perishable = [i for i in perishable if i.name in expiry_events]
    waste_rate = len(expired_perishable) / len(perishable) if perishable else 0.0

    # --- Nutrition score ---
    balanced_days = 0
    for day in range(1, horizon + 1):
        cats = nutrition_log.get(day, set())
        if "protein" in cats and "carb" in cats and "vegetable" in cats:
            balanced_days += 1
    nutrition_score = balanced_days / horizon if horizon > 0 else 0.0

    # --- Item counts ---
    items_used = sum(1 for i in original_inventory if consumption_log.get(i.name, 0) > 0)
    items_expired = len(expiry_events)

    return Reward(
        score=_clamp(grader_score, 0.0, 1.0),
        waste_rate=waste_rate,
        nutrition_score=nutrition_score,
        items_used=items_used,
        items_expired=items_expired,
        violations=violation_log,
    )


def compute_grader_score(
    original_inventory: list[FridgeItem],
    consumption_log: dict[str, float],
) -> float:
    """Standalone grader score for openenv.yaml reference."""
    perishable = [i for i in original_inventory if i.category != "condiment"]
    if not perishable:
        return 1.0
    used = sum(1 for i in perishable if consumption_log.get(i.name, 0) > 0)
    return _clamp(used / len(perishable), 0.0, 1.0)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
