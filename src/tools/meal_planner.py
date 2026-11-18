import random
from typing import Any, Dict, List, Optional
from src.models import MealPlan, DayMeals, Recipe
from src.tools.base import BaseTool, ToolResult
from src.tools.recipe_search import RecipeSearchTool


DAYS_OF_WEEK = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday"
]


class MealPlannerTool(BaseTool):
    name = "meal_planner"
    description = (
        "Create balanced daily and weekly meal plans, customize meal slots, "
        "enforce dietary constraints, and swap individual meals upon request."
    )

    def __init__(self, recipe_search_tool: Optional[RecipeSearchTool] = None):
        self.search_tool = recipe_search_tool or RecipeSearchTool()

    def execute(
        self,
        number_of_days: int = 7,
        meals_per_day: Optional[List[str]] = None,
        diet: Optional[str] = None,
        preferences: Optional[List[str]] = None,
        excluded_foods: Optional[List[str]] = None,
        vegetarian_days: Optional[int] = None,
        max_cooking_time: Optional[int] = None,
        modify_day: Optional[str] = None,
        modify_meal_type: Optional[str] = None,
        new_recipe_name: Optional[str] = None,
        existing_plan: Optional[MealPlan] = None,
        **kwargs
    ) -> ToolResult:
        # Case A: Modify an existing plan
        if existing_plan and modify_day and modify_meal_type and new_recipe_name:
            success = existing_plan.update_meal(modify_day, modify_meal_type, new_recipe_name)
            if success:
                return ToolResult(
                    success=True,
                    data=existing_plan,
                    message=f"Updated **{modify_day.capitalize()} {modify_meal_type.capitalize()}** to **{new_recipe_name}**.\n\n{existing_plan.format_markdown()}"
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"Day '{modify_day}' not found in active meal plan."
                )

        # Case B: Generate a new meal plan
        if number_of_days <= 0 or number_of_days > 14:
            return ToolResult(success=False, error="number_of_days must be between 1 and 14.")

        active_meals = [m.lower() for m in (meals_per_day or ["breakfast", "lunch", "dinner"])]
        all_recipes = self.search_tool._recipes
        if not all_recipes:
            return ToolResult(success=False, error="No recipes available to build a meal plan.")

        # Classify available recipes by meal type and diet
        veg_recipes = [r for r in all_recipes if "vegetarian" in [d.lower() for d in r.diet]]
        non_veg_recipes = [r for r in all_recipes if "non-vegetarian" in [d.lower() for d in r.diet]]

        # Exclude foods if requested
        if excluded_foods:
            ex_lower = [f.lower() for f in excluded_foods]
            all_recipes = [
                r for r in all_recipes
                if not any(ex in [i.name.lower() for i in r.ingredients] for ex in ex_lower)
            ]
            veg_recipes = [r for r in veg_recipes if r in all_recipes]
            non_veg_recipes = [r for r in non_veg_recipes if r in all_recipes]

        # Apply max cooking time constraint if requested
        if max_cooking_time:
            all_recipes = [r for r in all_recipes if r.cook_time <= max_cooking_time]
            veg_recipes = [r for r in veg_recipes if r.cook_time <= max_cooking_time]
            non_veg_recipes = [r for r in non_veg_recipes if r.cook_time <= max_cooking_time]

        plan_days = DAYS_OF_WEEK[:number_of_days]
        # Determine which days are vegetarian if requested
        veg_day_set = set()
        if vegetarian_days and vegetarian_days > 0:
            num_veg = min(vegetarian_days, len(plan_days))
            veg_day_set = set(plan_days[:num_veg])
        elif diet == "vegetarian":
            veg_day_set = set(plan_days)

        week_plan: Dict[str, DayMeals] = {}

        for day in plan_days:
            is_veg_day = day in veg_day_set
            candidate_pool = veg_recipes if is_veg_day else all_recipes
            if not candidate_pool:
                candidate_pool = all_recipes

            day_meals = DayMeals()

            for meal_type in active_meals:
                # Find matching recipes for this meal type
                type_candidates = [
                    r for r in candidate_pool
                    if r.meal_type and r.meal_type.lower() == meal_type
                ]
                if not type_candidates:
                    type_candidates = candidate_pool

                chosen = random.choice(type_candidates) if type_candidates else all_recipes[0]
                day_meals.set_meal(meal_type, chosen.name)

            week_plan[day] = day_meals

        title = f"{number_of_days}-Day Meal Plan"
        if diet:
            title += f" ({diet.capitalize()})"
        meal_plan = MealPlan(title=title, number_of_days=number_of_days, week=week_plan)

        return ToolResult(
            success=True,
            data=meal_plan,
            message=meal_plan.format_markdown()
        )

    def fallback(self, **kwargs) -> Optional[ToolResult]:
        # Return a simple 3-meal default template
        plan_days = DAYS_OF_WEEK[:7]
        week_plan = {
            day: DayMeals(
                breakfast="Egg Sandwich",
                lunch="Chicken Rice",
                dinner="Vegetable Pasta"
            ) for day in plan_days
        }
        fallback_plan = MealPlan(title="Standard 7-Day Balanced Plan", number_of_days=7, week=week_plan)
        return ToolResult(
            success=True,
            data=fallback_plan,
            message=fallback_plan.format_markdown()
        )
