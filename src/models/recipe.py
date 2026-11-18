from typing import List, Optional
from pydantic import BaseModel, Field
from src.models.ingredient import Ingredient


class Recipe(BaseModel):
    id: Optional[str] = Field(None, description="Unique recipe identifier")
    name: str = Field(..., description="Recipe title")
    servings: int = Field(2, description="Number of portions/servings", ge=1)
    prep_time: int = Field(..., description="Preparation time in minutes", ge=0)
    cook_time: int = Field(..., description="Cooking time in minutes", ge=0)
    difficulty: str = Field("Easy", description="Difficulty: Easy, Medium, or Hard")
    cuisine: Optional[str] = Field("Global", description="Cuisine style (e.g. Italian, Asian, Indian)")
    meal_type: Optional[str] = Field("dinner", description="Meal category: breakfast, lunch, dinner, snack")
    diet: List[str] = Field(default_factory=list, description="Dietary and lifestyle tags (e.g. vegetarian, vegan, spicy)")
    ingredients: List[Ingredient] = Field(default_factory=list, description="List of recipe ingredients with quantities")
    instructions: List[str] = Field(default_factory=list, description="Step-by-step cooking procedures")
    tips: Optional[str] = Field(None, description="Chef tips, variations, or spice notes")

    @property
    def total_time(self) -> int:
        return self.prep_time + self.cook_time

    def scale_servings(self, target_servings: int) -> "Recipe":
        """Returns a cloned Recipe scaled proportionally to target_servings."""
        if target_servings <= 0:
            raise ValueError("Target servings must be greater than 0.")
        factor = target_servings / self.servings
        scaled_ingredients = [ing.scale(factor) for ing in self.ingredients]
        
        return Recipe(
            id=self.id,
            name=self.name,
            servings=target_servings,
            prep_time=self.prep_time,
            cook_time=self.cook_time,
            difficulty=self.difficulty,
            cuisine=self.cuisine,
            meal_type=self.meal_type,
            diet=list(self.diet),
            ingredients=scaled_ingredients,
            instructions=list(self.instructions),
            tips=self.tips
        )

    def format_markdown(self) -> str:
        """Formats the recipe strictly as specified in PRD Section 11."""
        lines = [
            f"## {self.name}",
            "",
            f"**Servings:** {self.servings}",
            f"**Prep time:** {self.prep_time} minutes",
            f"**Cooking time:** {self.cook_time} minutes",
            f"**Difficulty:** {self.difficulty}",
            "",
            "### Ingredients"
        ]
        for ing in self.ingredients:
            notes_str = f" ({ing.notes})" if ing.notes else ""
            qty = int(ing.quantity) if ing.quantity == int(ing.quantity) else ing.quantity
            lines.append(f"- {qty} {ing.unit} {ing.name}{notes_str}")
        
        lines.append("")
        lines.append("### Instructions")
        for i, step in enumerate(self.instructions, 1):
            lines.append(f"{i}. {step}")
            
        if self.tips:
            lines.append("")
            lines.append("### Tips")
            lines.append(self.tips)
            
        return "\n".join(lines)
