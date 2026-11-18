import pytest
from src.tools import (
    RecipeSearchTool,
    IngredientSubstitutionTool,
    RecipeCalculatorTool,
    MealPlannerTool,
    MemoryTool,
    BaseTool,
    ToolResult
)
from src.models import Recipe, Ingredient


def test_recipe_search_tool():
    tool = RecipeSearchTool()
    
    # 1. Search with chicken and rice
    res = tool.execute(ingredients=["chicken", "rice"])
    assert res.success is True
    assert len(res.data) >= 1
    names = [r.name for r in res.data]
    assert any("Chicken" in n for n in names)

    # 2. Search vegetarian
    res_veg = tool.execute(diet=["vegetarian"])
    assert res_veg.success is True
    for r in res_veg.data:
        assert "vegetarian" in [d.lower() for d in r.diet]

    # 3. Excluded ingredients
    res_no_onion = tool.execute(ingredients=["chicken"], excluded_ingredients=["onion"])
    assert res_no_onion.success is True
    for r in res_no_onion.data:
        ing_names = [i.name.lower() for i in r.ingredients]
        assert not any("onion" in i for i in ing_names)

    # 4. Max cooking time
    res_quick = tool.execute(max_cooking_time=15)
    assert res_quick.success is True
    for r in res_quick.data:
        assert r.cook_time <= 15


def test_ingredient_substitution_tool():
    tool = IngredientSubstitutionTool()
    
    # Butter substitution
    res = tool.execute(ingredient="butter")
    assert res.success is True
    assert "butter" in res.data["ingredient"].lower()
    sub_names = [s["name"].lower() for s in res.data["substitutes"]]
    assert any("oil" in s for s in sub_names)
    assert "Note: Substitutions will alter the flavor" in res.message

    # Soy sauce substitution
    res_soy = tool.execute(ingredient="soy sauce")
    assert res_soy.success is True
    assert any("tamari" in s["name"].lower() for s in res_soy.data["substitutes"])

    # Fallback for unknown
    res_unknown = tool.run_with_retry(ingredient="rare dragonfruit peel")
    assert res_unknown.success is True
    assert res_unknown.fallback_used is True


def test_recipe_calculator_tool():
    tool = RecipeCalculatorTool()
    
    recipe = Recipe(
        name="Chicken Rice",
        servings=2,
        prep_time=10,
        cook_time=25,
        difficulty="Easy",
        ingredients=[
            Ingredient(name="chicken", quantity=300, unit="g"),
            Ingredient(name="rice", quantity=200, unit="g")
        ],
        instructions=["Cook chicken", "Add rice"]
    )

    # Scale 2 servings -> 6 servings (3x)
    res = tool.execute(recipe=recipe, target_servings=6)
    assert res.success is True
    scaled_recipe: Recipe = res.data
    assert scaled_recipe.servings == 6
    assert scaled_recipe.ingredients[0].quantity == 900
    assert scaled_recipe.ingredients[1].quantity == 600

    # Invalid servings error handling
    res_err = tool.execute(recipe=recipe, target_servings=0)
    assert res_err.success is False
    assert "positive integer" in res_err.error


def test_meal_planner_tool():
    tool = MealPlannerTool()
    
    # 7-day meal plan
    res = tool.execute(number_of_days=7, meals_per_day=["breakfast", "lunch", "dinner"])
    assert res.success is True
    plan = res.data
    assert plan.number_of_days == 7
    assert len(plan.week) == 7
    assert plan.week["monday"].breakfast is not None

    # Modify Wednesday dinner
    res_mod = tool.execute(
        existing_plan=plan,
        modify_day="wednesday",
        modify_meal_type="dinner",
        new_recipe_name="Vegetarian Pasta"
    )
    assert res_mod.success is True
    assert plan.week["wednesday"].dinner == "Vegetarian Pasta"


def test_memory_tool(tmp_path):
    storage_file = tmp_path / "test_user_prefs.json"
    tool = MemoryTool(storage_path=str(storage_file))

    # Remember
    res = tool.execute(action="remember", user_id="test_user", preference="User prefers spicy food")
    assert res.success is True
    assert "User prefers spicy food" in res.data

    # Recall
    res_recall = tool.execute(action="recall", user_id="test_user", query="spicy")
    assert res_recall.success is True
    assert len(res_recall.data) == 1
    assert "spicy" in res_recall.data[0].lower()

    # Forget
    res_forget = tool.execute(action="forget", user_id="test_user", preference="spicy")
    assert res_forget.success is True
    assert len(res_forget.data) == 0


def test_tool_retry_and_recovery():
    class FlakyTool(BaseTool):
        name = "flaky"
        description = "Test flaky tool"
        calls = 0

        def execute(self, **kwargs) -> ToolResult:
            self.calls += 1
            if self.calls < 3:
                return ToolResult(success=False, error="Temporary failure")
            return ToolResult(success=True, data="Success on 3rd try")

    tool = FlakyTool()
    res = tool.run_with_retry(max_retries=2)
    assert res.success is True
    assert res.data == "Success on 3rd try"
    assert res.retry_count == 2
