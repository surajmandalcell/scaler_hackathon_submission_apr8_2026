"""Unit tests for env/data.py — ingredient lookup table."""

from env.data import (
    CATEGORIES,
    INGREDIENTS,
    get_ingredients_by_category,
    violates_restriction,
)


def test_ingredient_count():
    assert len(INGREDIENTS) == 50


def test_category_distribution():
    counts = {}
    for i in INGREDIENTS:
        counts[i.category] = counts.get(i.category, 0) + 1
    assert counts["protein"] == 10
    assert counts["carb"] == 10
    assert counts["vegetable"] == 12
    assert counts["dairy"] == 8
    assert counts["fruit"] == 6
    assert counts["condiment"] == 4


def test_unique_names():
    names = [i.name for i in INGREDIENTS]
    assert len(names) == len(set(names))


def test_valid_categories():
    for i in INGREDIENTS:
        assert i.category in CATEGORIES, f"{i.name} has invalid category {i.category}"


def test_shelf_life_range():
    for i in INGREDIENTS:
        min_life, max_life = i.shelf_life_days
        assert min_life >= 1, f"{i.name} has shelf_life min < 1"
        assert min_life <= max_life, f"{i.name} has min > max shelf_life"


def test_valid_units():
    valid_units = {"g", "ml", "pcs"}
    for i in INGREDIENTS:
        assert i.unit in valid_units, f"{i.name} has invalid unit {i.unit}"


def test_dietary_tags_type():
    for i in INGREDIENTS:
        assert isinstance(i.contains_meat, bool)
        assert isinstance(i.contains_dairy, bool)
        assert isinstance(i.contains_gluten, bool)


def test_condiments_long_shelf_life():
    condiments = get_ingredients_by_category("condiment")
    for c in condiments:
        assert c.shelf_life_days[0] >= 30, f"{c.name} condiment has short shelf life"


def test_proteins_have_variety():
    proteins = get_ingredients_by_category("protein")
    has_meat = [p for p in proteins if p.contains_meat]
    no_meat = [p for p in proteins if not p.contains_meat]
    assert len(has_meat) >= 2, "Need some meat-containing proteins"
    assert len(no_meat) >= 2, "Need some non-meat proteins (tofu, eggs, tempeh)"


def test_violates_restriction_logic():
    assert violates_restriction("chicken_breast", "vegetarian") is True
    assert violates_restriction("tofu", "vegetarian") is False
    assert violates_restriction("whole_milk", "lactose-free") is True
    assert violates_restriction("chicken_breast", "lactose-free") is False
    assert violates_restriction("whole_wheat_bread", "gluten-free") is True
    assert violates_restriction("white_rice", "gluten-free") is False
    assert violates_restriction("nonexistent_food", "vegetarian") is False


def test_get_by_category_returns_correct():
    for cat in CATEGORIES:
        items = get_ingredients_by_category(cat)
        assert len(items) > 0, f"No items in category {cat}"
        assert all(i.category == cat for i in items)
