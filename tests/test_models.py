import json
from pathlib import Path
import pytest
from src.models import (
    Ingredient,
    Recipe,
    MealPlan,
    DayMeals,
    AgentState,
    TaskPlan,
    ActionEventType
)


def test_ingredient_scaling():
    ing = Ingredient(name="chicken breast", quantity=300, unit="g")
    scaled = ing.scale(2.0)
    assert scaled.quantity == 600
    assert scaled.name == "chicken breast"
    assert scaled.unit == "g"

    scaled_half = ing.scale(0.5)
    assert scaled_half.quantity == 150


def test_recipe_model_and_markdown():
    recipe = Recipe(
        name="Spicy Chicken Rice",
        servings=2,
        prep_time=10,
        cook_time=25,
        difficulty="Easy",
        cuisine="Asian",
        ingredients=[
            Ingredient(name="chicken", quantity=300, unit="g"),
            Ingredient(name="rice", quantity=200, unit="g")
        ],
        instructions=[
            "Prepare ingredients",
            "Cook chicken",
            "Add rice and simmer"
        ],
        tips="Add chili to taste"
    )

    assert recipe.total_time == 35
    scaled = recipe.scale_servings(4)
    assert scaled.servings == 4
    assert scaled.ingredients[0].quantity == 600
    assert scaled.ingredients[1].quantity == 400

    md = scaled.format_markdown()
    assert "## Spicy Chicken Rice" in md
    assert "**Servings:** 4" in md
    assert "- 600 g chicken" in md
    assert "1. Prepare ingredients" in md
    assert "### Tips" in md
    assert "Add chili to taste" in md


def test_meal_plan_model():
    plan = MealPlan(
        title="Weekly Test Plan",
        number_of_days=7,
        week={
            "monday": DayMeals(breakfast="Egg Sandwich", lunch="Chicken Rice", dinner="Vegetable Pasta"),
            "tuesday": DayMeals(breakfast="Oatmeal", lunch="Chicken Wrap", dinner="Dal Rice")
        }
    )

    assert plan.week["monday"].breakfast == "Egg Sandwich"
    assert plan.week["tuesday"].dinner == "Dal Rice"

    # Update Wednesday dinner
    plan.week["wednesday"] = DayMeals(dinner="Chicken Curry")
    updated = plan.update_meal("wednesday", "dinner", "Vegetable Stir Fry")
    assert updated is True
    assert plan.week["wednesday"].dinner == "Vegetable Stir Fry"

    md = plan.format_markdown()
    assert "Weekly Test Plan" in md
    assert "Monday" in md
    assert "Vegetable Stir Fry" in md


def test_agent_state_and_step_limit():
    state = AgentState(user_id="user1", max_steps=3)
    assert state.step_count == 0

    assert state.increment_step() is True
    assert state.increment_step() is True
    assert state.increment_step() is True
    # 4th step should exceed max_steps (3)
    assert state.increment_step() is False
    assert state.action_logs[-1].event_type == ActionEventType.LIMIT_EXCEEDED


def test_datasets_integrity():
    root = Path(__file__).parent.parent
    recipes_file = root / "data" / "recipes.json"
    subs_file = root / "data" / "substitutions.json"

    assert recipes_file.exists()
    assert subs_file.exists()

    with open(recipes_file, "r", encoding="utf-8") as f:
        recipes_data = json.load(f)
        assert len(recipes_data) >= 10
        for r in recipes_data:
            rec = Recipe(**r)
            assert rec.name
            assert len(rec.ingredients) > 0

    with open(subs_file, "r", encoding="utf-8") as f:
        subs_data = json.load(f)
        assert "butter" in subs_data
        assert "soy sauce" in subs_data
        assert len(subs_data["butter"]["substitutes"]) > 0
