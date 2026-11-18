import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.tools.base import BaseTool, ToolResult


class IngredientSubstitutionTool(BaseTool):
    name = "ingredient_substitution"
    description = (
        "Find suitable substitutes for unavailable ingredients, including conversion ratios, "
        "culinary recommendations, and flavor/texture impacts."
    )

    def __init__(self, substitutions_path: Optional[str] = None):
        if substitutions_path:
            self.file_path = Path(substitutions_path)
        else:
            self.file_path = Path(__file__).parent.parent.parent / "data" / "substitutions.json"
        self._substitutions: Dict[str, Any] = {}
        self._load_substitutions()

    def _load_substitutions(self) -> None:
        if not self.file_path.exists():
            self._substitutions = {}
            return
        with open(self.file_path, "r", encoding="utf-8") as f:
            self._substitutions = json.load(f)

    def execute(self, ingredient: str, **kwargs) -> ToolResult:
        if not ingredient or not ingredient.strip():
            return ToolResult(success=False, error="Ingredient name cannot be empty.")

        query = ingredient.strip().lower()

        # Direct match or substring match
        matched_key = None
        if query in self._substitutions:
            matched_key = query
        else:
            for key in self._substitutions.keys():
                if key in query or query in key:
                    matched_key = key
                    break

        if not matched_key:
            return ToolResult(
                success=False,
                error=f"No direct substitution found in database for '{ingredient}'."
            )

        data = self._substitutions[matched_key]
        substitutes = data.get("substitutes", [])

        lines = [
            f"### Substitutes for '{matched_key.title()}':",
            "*Note: Substitutions will alter the flavor or texture profile of the finished dish.*",
            ""
        ]
        for sub in substitutes:
            lines.append(f"• **{sub['name']}**")
            lines.append(f"  - Ratio: {sub['ratio']}")
            lines.append(f"  - Culinary Impact: {sub['impact']}")
            if "best_for" in sub:
                lines.append(f"  - Best for: {', '.join(sub['best_for'])}")
            lines.append("")

        return ToolResult(
            success=True,
            data={"ingredient": matched_key, "substitutes": substitutes},
            message="\n".join(lines).strip()
        )

    def fallback(self, **kwargs) -> Optional[ToolResult]:
        ingredient = kwargs.get("ingredient", "that ingredient")
        general_advice = (
            f"Culinary guidance for '{ingredient}':\n"
            f"If '{ingredient}' is an aromatic (like spices or herbs), you can often omit it or substitute a similar dried herb at 1/3 the quantity. "
            f"If it provides acidity (like lemon or vinegar), substitute a mild citrus juice or cider vinegar. "
            f"If it provides moisture or fat, neutral cooking oil or vegetable broth can serve as a quick alternative."
        )
        return ToolResult(
            success=True,
            data={"ingredient": ingredient, "substitutes": [{"name": "General culinary alternative", "ratio": "To taste", "impact": "Flavor balance may change"}]},
            message=general_advice
        )
