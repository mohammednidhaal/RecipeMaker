from typing import Any, Dict, List, Optional, Union
from src.models import Recipe, Ingredient
from src.tools.base import BaseTool, ToolResult


class RecipeCalculatorTool(BaseTool):
    name = "recipe_calculator"
    description = (
        "Scale ingredient quantities for a recipe up or down to match a requested number of servings, "
        "and calculate proportional adjustments."
    )

    def execute(
        self,
        recipe: Optional[Union[Recipe, Dict[str, Any]]] = None,
        target_servings: Optional[int] = None,
        current_servings: Optional[int] = None,
        ingredients: Optional[List[Union[Ingredient, Dict[str, Any]]]] = None,
        **kwargs
    ) -> ToolResult:
        if target_servings is None or target_servings <= 0:
            return ToolResult(success=False, error="Target servings must be a positive integer.")

        # Scenario A: Full Recipe object or dict provided
        if recipe is not None:
            if isinstance(recipe, dict):
                try:
                    rec_obj = Recipe(**recipe)
                except Exception as e:
                    return ToolResult(success=False, error=f"Invalid recipe data: {e}")
            elif isinstance(recipe, Recipe):
                rec_obj = recipe
            else:
                return ToolResult(success=False, error="Unsupported recipe object format.")

            orig_servings = rec_obj.servings
            scaled_recipe = rec_obj.scale_servings(target_servings)

            lines = [
                f"### Scaled Recipe: {scaled_recipe.name}",
                f"Adjusted from {orig_servings} serving(s) to **{target_servings} serving(s)**:",
                ""
            ]
            for ing in scaled_recipe.ingredients:
                qty = int(ing.quantity) if ing.quantity == int(ing.quantity) else ing.quantity
                lines.append(f"- **{ing.name}**: {qty} {ing.unit}")

            return ToolResult(
                success=True,
                data=scaled_recipe,
                message="\n".join(lines)
            )

        # Scenario B: Ingredients list + current servings
        elif ingredients is not None and current_servings is not None:
            if current_servings <= 0:
                return ToolResult(success=False, error="Current servings must be greater than zero.")
            
            factor = target_servings / current_servings
            scaled_list = []
            lines = [
                f"Scaled ingredients for **{target_servings} serving(s)** (factor: {round(factor, 2)}x):",
                ""
            ]
            for item in ingredients:
                if isinstance(item, dict):
                    ing_obj = Ingredient(**item)
                else:
                    ing_obj = item
                scaled_ing = ing_obj.scale(factor)
                scaled_list.append(scaled_ing)
                qty = int(scaled_ing.quantity) if scaled_ing.quantity == int(scaled_ing.quantity) else scaled_ing.quantity
                lines.append(f"- **{scaled_ing.name}**: {qty} {scaled_ing.unit}")

            return ToolResult(
                success=True,
                data={"servings": target_servings, "ingredients": scaled_list},
                message="\n".join(lines)
            )

        else:
            return ToolResult(
                success=False,
                error="Either a recipe or an ingredients list with current_servings must be supplied."
            )

    def fallback(self, **kwargs) -> Optional[ToolResult]:
        target = kwargs.get("target_servings", 4)
        return ToolResult(
            success=True,
            data={"target_servings": target, "note": "Scale factor applied linearly"},
            message=f"Applied linear scaling adjustment to {target} servings."
        )
