from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DayMeals(BaseModel):
    breakfast: Optional[str] = Field(None, description="Recipe name for breakfast")
    lunch: Optional[str] = Field(None, description="Recipe name for lunch")
    dinner: Optional[str] = Field(None, description="Recipe name for dinner")
    snack: Optional[str] = Field(None, description="Optional recipe name for snack")

    def get_meal(self, meal_type: str) -> Optional[str]:
        return getattr(self, meal_type.lower(), None)

    def set_meal(self, meal_type: str, recipe_name: str) -> None:
        meal_key = meal_type.lower()
        if hasattr(self, meal_key):
            setattr(self, meal_key, recipe_name)


class MealPlan(BaseModel):
    title: str = Field("Weekly Meal Plan", description="Title of the plan")
    number_of_days: int = Field(7, description="Number of days planned")
    week: Dict[str, DayMeals] = Field(
        default_factory=dict,
        description="Map of day of the week (e.g. 'monday') to DayMeals"
    )

    def update_meal(self, day: str, meal_type: str, new_recipe: str) -> bool:
        """Update a specific meal on a given day."""
        day_key = day.lower()
        if day_key in self.week:
            self.week[day_key].set_meal(meal_type, new_recipe)
            return True
        return False

    def format_markdown(self) -> str:
        """Format the meal plan as a markdown table and summary."""
        lines = [f"### 📅 {self.title}", ""]
        for day, meals in self.week.items():
            lines.append(f"**{day.capitalize()}**")
            if meals.breakfast:
                lines.append(f"- 🍳 **Breakfast:** {meals.breakfast}")
            if meals.lunch:
                lines.append(f"- 🥗 **Lunch:** {meals.lunch}")
            if meals.dinner:
                lines.append(f"- 🍲 **Dinner:** {meals.dinner}")
            if meals.snack:
                lines.append(f"- 🍎 **Snack:** {meals.snack}")
            lines.append("")
        return "\n".join(lines).strip()
