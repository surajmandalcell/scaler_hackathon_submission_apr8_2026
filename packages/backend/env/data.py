"""Hardcoded 50-item ingredient lookup table for FridgeEnv."""

from typing import NamedTuple

CATEGORIES = ["protein", "carb", "vegetable", "dairy", "fruit", "condiment"]
DIETARY_RESTRICTIONS = ["vegetarian", "lactose-free", "gluten-free"]


class IngredientDef(NamedTuple):
    name: str
    category: str
    shelf_life_days: tuple[int, int]  # (min, max) for seeded jitter
    unit: str  # g, ml, pcs
    default_qty: float
    contains_meat: bool
    contains_dairy: bool
    contains_gluten: bool


# fmt: off
INGREDIENTS: list[IngredientDef] = [
    # === PROTEIN (10) ===
    IngredientDef("chicken_breast",    "protein",   (3, 5),    "g",   500, True,  False, False),
    IngredientDef("ground_beef",       "protein",   (2, 4),    "g",   400, True,  False, False),
    IngredientDef("salmon_fillet",     "protein",   (2, 3),    "g",   300, True,  False, False),
    IngredientDef("pork_chops",        "protein",   (3, 5),    "g",   400, True,  False, False),
    IngredientDef("shrimp",            "protein",   (1, 3),    "g",   300, True,  False, False),
    IngredientDef("tofu",              "protein",   (5, 7),    "g",   400, False, False, False),
    IngredientDef("eggs",              "protein",   (14, 21),  "pcs", 12,  False, False, False),
    IngredientDef("turkey_slices",     "protein",   (3, 5),    "g",   250, True,  False, False),
    IngredientDef("tempeh",            "protein",   (5, 7),    "g",   300, False, False, False),
    IngredientDef("canned_tuna",       "protein",   (180, 365),"g",   200, True,  False, False),

    # === CARB (10) ===
    IngredientDef("white_rice",        "carb",      (180, 365),"g",   1000, False, False, False),
    IngredientDef("whole_wheat_bread", "carb",      (3, 7),    "g",   500,  False, False, True),
    IngredientDef("pasta",             "carb",      (180, 365),"g",   500,  False, False, True),
    IngredientDef("potatoes",          "carb",      (14, 28),  "g",   1000, False, False, False),
    IngredientDef("tortillas",         "carb",      (7, 14),   "g",   400,  False, False, True),
    IngredientDef("oats",              "carb",      (180, 365),"g",   500,  False, False, True),
    IngredientDef("quinoa",            "carb",      (180, 365),"g",   400,  False, False, False),
    IngredientDef("couscous",          "carb",      (180, 365),"g",   400,  False, False, True),
    IngredientDef("sweet_potatoes",    "carb",      (14, 28),  "g",   800,  False, False, False),
    IngredientDef("naan_bread",        "carb",      (3, 5),    "g",   300,  False, True,  True),

    # === VEGETABLE (12) ===
    IngredientDef("spinach",           "vegetable", (3, 5),    "g",   200,  False, False, False),
    IngredientDef("bell_peppers",      "vegetable", (5, 7),    "g",   300,  False, False, False),
    IngredientDef("broccoli",          "vegetable", (3, 5),    "g",   300,  False, False, False),
    IngredientDef("carrots",           "vegetable", (14, 21),  "g",   500,  False, False, False),
    IngredientDef("tomatoes",          "vegetable", (3, 5),    "g",   400,  False, False, False),
    IngredientDef("onions",            "vegetable", (21, 30),  "g",   500,  False, False, False),
    IngredientDef("mushrooms",         "vegetable", (3, 5),    "g",   200,  False, False, False),
    IngredientDef("zucchini",          "vegetable", (4, 7),    "g",   300,  False, False, False),
    IngredientDef("cucumber",          "vegetable", (5, 7),    "g",   300,  False, False, False),
    IngredientDef("green_beans",       "vegetable", (3, 5),    "g",   250,  False, False, False),
    IngredientDef("kale",              "vegetable", (3, 5),    "g",   200,  False, False, False),
    IngredientDef("corn",              "vegetable", (3, 5),    "pcs", 4,    False, False, False),

    # === DAIRY (8) ===
    IngredientDef("whole_milk",        "dairy",     (5, 7),    "ml",  1000, False, True,  False),
    IngredientDef("cheddar_cheese",    "dairy",     (14, 28),  "g",   300,  False, True,  False),
    IngredientDef("greek_yogurt",      "dairy",     (7, 14),   "g",   500,  False, True,  False),
    IngredientDef("butter",            "dairy",     (14, 30),  "g",   250,  False, True,  False),
    IngredientDef("cream_cheese",      "dairy",     (7, 14),   "g",   200,  False, True,  False),
    IngredientDef("mozzarella",        "dairy",     (7, 14),   "g",   300,  False, True,  False),
    IngredientDef("sour_cream",        "dairy",     (7, 14),   "g",   200,  False, True,  False),
    IngredientDef("parmesan",          "dairy",     (30, 60),  "g",   200,  False, True,  False),

    # === FRUIT (6) ===
    IngredientDef("bananas",           "fruit",     (3, 5),    "pcs", 6,    False, False, False),
    IngredientDef("strawberries",      "fruit",     (2, 4),    "g",   300,  False, False, False),
    IngredientDef("apples",            "fruit",     (14, 28),  "g",   500,  False, False, False),
    IngredientDef("lemons",            "fruit",     (14, 21),  "pcs", 4,    False, False, False),
    IngredientDef("blueberries",       "fruit",     (3, 5),    "g",   200,  False, False, False),
    IngredientDef("avocados",          "fruit",     (2, 4),    "pcs", 3,    False, False, False),

    # === CONDIMENT (4) ===
    IngredientDef("olive_oil",         "condiment", (180, 365),"ml",  500,  False, False, False),
    IngredientDef("soy_sauce",         "condiment", (180, 365),"ml",  300,  False, False, True),
    IngredientDef("hot_sauce",         "condiment", (180, 365),"ml",  200,  False, False, False),
    IngredientDef("mustard",           "condiment", (180, 365),"ml",  250,  False, False, False),
]
# fmt: on

# O(1) lookup by name
INGREDIENT_INDEX: dict[str, IngredientDef] = {i.name: i for i in INGREDIENTS}


def get_ingredients_by_category(category: str) -> list[IngredientDef]:
    """Return all ingredients in a given category."""
    return [i for i in INGREDIENTS if i.category == category]


def violates_restriction(ingredient_name: str, restriction: str) -> bool:
    """Check if an ingredient violates a dietary restriction."""
    ingredient = INGREDIENT_INDEX.get(ingredient_name)
    if ingredient is None:
        return False
    if restriction == "vegetarian":
        return ingredient.contains_meat
    if restriction == "lactose-free":
        return ingredient.contains_dairy
    if restriction == "gluten-free":
        return ingredient.contains_gluten
    return False
