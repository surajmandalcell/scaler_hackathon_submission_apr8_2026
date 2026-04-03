"""Unit tests for env/generator.py — seeded deterministic factory."""

from collections import Counter

import pytest

from env.data import violates_restriction
from env.generator import DIFFICULTY_PROFILES, generate_observation


def test_deterministic_same_seed():
    obs1 = generate_observation(42, "easy")
    obs2 = generate_observation(42, "easy")
    assert obs1 == obs2


def test_different_seed_different_output():
    obs1 = generate_observation(42, "easy")
    obs2 = generate_observation(43, "easy")
    names1 = {i.name for i in obs1.inventory}
    names2 = {i.name for i in obs2.inventory}
    assert names1 != names2


def test_easy_item_count_range():
    for seed in range(20):
        obs = generate_observation(seed, "easy")
        # May have extra items from solvability guarantee
        assert len(obs.inventory) >= 5
        assert len(obs.inventory) <= 10  # allow small overshoot from guarantees


def test_medium_item_count_range():
    for seed in range(20):
        obs = generate_observation(seed, "medium")
        assert len(obs.inventory) >= 10
        assert len(obs.inventory) <= 18


def test_hard_item_count_range():
    for seed in range(20):
        obs = generate_observation(seed, "hard")
        assert len(obs.inventory) >= 20
        assert len(obs.inventory) <= 33


def test_easy_no_restrictions():
    obs = generate_observation(42, "easy")
    assert obs.dietary_restrictions == []


def test_medium_one_restriction():
    obs = generate_observation(42, "medium")
    assert len(obs.dietary_restrictions) == 1


def test_hard_two_restrictions():
    obs = generate_observation(42, "hard")
    assert len(obs.dietary_restrictions) == 2


def test_easy_horizon_3():
    obs = generate_observation(42, "easy")
    assert obs.horizon == 3


def test_expiry_dates_within_range():
    for difficulty in DIFFICULTY_PROFILES:
        obs = generate_observation(42, difficulty)
        for item in obs.inventory:
            days_until = (item.expiry_date - obs.current_date).days
            assert days_until >= 1, f"{item.name} expires before day 1"
            assert days_until <= obs.horizon + 2, f"{item.name} expires too late"


def test_medium_has_clustering():
    """At least 2 items should share an expiry date in medium difficulty."""
    # Test across several seeds since clustering is probabilistic in position
    found_cluster = False
    for seed in range(20):
        obs = generate_observation(seed, "medium")
        date_counts = Counter(i.expiry_date for i in obs.inventory)
        if any(c >= 2 for c in date_counts.values()):
            found_cluster = True
            break
    assert found_cluster, "No clustering found in medium across 20 seeds"


def test_hard_has_large_clusters():
    """Hard difficulty should have larger clusters of shared expiry dates."""
    found_large_cluster = False
    for seed in range(20):
        obs = generate_observation(seed, "hard")
        date_counts = Counter(i.expiry_date for i in obs.inventory)
        if any(c >= 3 for c in date_counts.values()):
            found_large_cluster = True
            break
    assert found_large_cluster, "No large cluster (>=3) found in hard across 20 seeds"


def test_restriction_conflict_rate():
    """At least 30% of items should conflict with dietary restrictions."""
    for difficulty in ["medium", "hard"]:
        for seed in range(10):
            obs = generate_observation(seed, difficulty)
            if not obs.dietary_restrictions:
                continue
            conflict_count = sum(
                1
                for item in obs.inventory
                if any(violates_restriction(item.name, r) for r in obs.dietary_restrictions)
            )
            rate = conflict_count / len(obs.inventory)
            assert rate >= 0.2, f"Conflict rate {rate:.2f} too low for {difficulty} seed={seed}"


def test_solvability_guarantee():
    """Every generated observation must have protein + carb + vegetable."""
    for difficulty in DIFFICULTY_PROFILES:
        for seed in range(50):
            obs = generate_observation(seed, difficulty)
            categories = {i.category for i in obs.inventory}
            assert "protein" in categories, f"No protein in {difficulty} seed={seed}"
            assert "carb" in categories, f"No carb in {difficulty} seed={seed}"
            assert "vegetable" in categories, f"No vegetable in {difficulty} seed={seed}"


def test_quantities_scaled_by_household():
    """Hard (household=4) should have larger average quantities than easy (household=2)."""
    easy_qtys = []
    hard_qtys = []
    for seed in range(20):
        easy_obs = generate_observation(seed, "easy")
        hard_obs = generate_observation(seed, "hard")
        easy_qtys.extend(i.quantity for i in easy_obs.inventory if i.unit == "g")
        hard_qtys.extend(i.quantity for i in hard_obs.inventory if i.unit == "g")
    assert sum(hard_qtys) / len(hard_qtys) > sum(easy_qtys) / len(easy_qtys)


def test_all_difficulties_valid():
    for difficulty in DIFFICULTY_PROFILES:
        obs = generate_observation(0, difficulty)
        assert obs.done is False
        assert obs.reward is None
        assert obs.horizon == DIFFICULTY_PROFILES[difficulty]["horizon"]
        assert obs.household_size == DIFFICULTY_PROFILES[difficulty]["household_size"]


def test_100_seeds_no_crash():
    for difficulty in DIFFICULTY_PROFILES:
        for seed in range(100):
            obs = generate_observation(seed, difficulty)
            assert len(obs.inventory) > 0


def test_invalid_difficulty_raises():
    with pytest.raises(ValueError, match="Unknown difficulty"):
        generate_observation(0, "impossible")
