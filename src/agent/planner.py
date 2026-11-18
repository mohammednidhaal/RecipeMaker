from typing import List, Optional
from src.models import TaskPlan, AgentState


class AgentPlanner:
    """
    Generates and updates sequential task plans before tool execution
    conforming to PRD Section 7.
    """

    @staticmethod
    def create_plan_for_request(user_input: str, state: AgentState) -> Optional[TaskPlan]:
        text = user_input.lower().strip()

        # Complex meal plan requests (e.g. 7-day dinner plan)
        if any(term in text for term in ["meal plan", "dinner plan", "plan my week", "7-day", "weekly plan"]):
            return TaskPlan(
                goal="Generate personalized multi-day meal plan",
                steps=[
                    "Identify dietary requirements and day count",
                    "Query recipe database for matching recipes",
                    "Balance meals across requested schedule",
                    "Assemble structured meal plan",
                    "Present final meal plan to user"
                ]
            )

        # Recipe scaling request
        elif any(term in text for term in ["for ", "people", "servings", "scale"]) and state.current_recipe:
            return TaskPlan(
                goal=f"Scale recipe '{state.current_recipe.name}' to requested servings",
                steps=[
                    "Extract target serving size",
                    "Calculate proportional scaling factor",
                    "Update ingredient quantities using Recipe Calculator",
                    "Present modified recipe"
                ]
            )

        # Missing ingredient substitution request
        elif any(term in text for term in ["don't have", "dont have", "no ", "substitute", "replace", "out of"]):
            return TaskPlan(
                goal="Find and suggest culinary ingredient substitutes",
                steps=[
                    "Identify unavailable ingredient",
                    "Lookup flavor/texture culinary substitutes",
                    "Warn about taste and texture alterations",
                    "Suggest best options to user"
                ]
            )

        # Recipe search from ingredients
        elif any(term in text for term in ["have", "cook", "make", "suggest", "recipe", "ingredients"]):
            return TaskPlan(
                goal="Suggest recipes based on available ingredients and user preferences",
                steps=[
                    "Extract available ingredients from input",
                    "Apply user preferences and dietary constraints",
                    "Search recipe database",
                    "Rank and present top matching recipes"
                ]
            )

        # Direct simple questions or greetings do not require a multi-step plan
        return None
