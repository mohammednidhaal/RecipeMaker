import copy
from typing import Any, Dict, List, Optional
from src.models import (
    AgentState,
    Recipe,
    Ingredient,
    MealPlan,
    TaskPlan,
    ActionEventType,
    PendingConfirmation
)
from src.tools import (
    RecipeSearchTool,
    IngredientSubstitutionTool,
    RecipeCalculatorTool,
    MealPlannerTool,
    MemoryTool
)
from src.agent.planner import AgentPlanner
from src.agent.llm_mock import MockLLMBrain
from src.utils.logger import log_step


class AgentExecutor:
    """
    Implements the complete AI Agent Loop:
    Think → Act → Look → Learn → Respond
    Conforming to PRD Sections 6, 7, 10, 14, 15, 17, and 21.
    """

    def __init__(
        self,
        user_id: str = "default_user",
        conversation_id: str = "default_session",
        max_steps: int = 10,
        brain: Optional[Any] = None
    ):
        self.state = AgentState(
            user_id=user_id,
            conversation_id=conversation_id,
            max_steps=max_steps
        )
        self.search_tool = RecipeSearchTool()
        self.substitution_tool = IngredientSubstitutionTool()
        self.calculator_tool = RecipeCalculatorTool()
        self.planner_tool = MealPlannerTool(self.search_tool)
        self.memory_tool = MemoryTool()
        self.brain = brain or MockLLMBrain()

        # Load persisted preferences into state
        self._load_memory()

    def _load_memory(self) -> None:
        mem_res = self.memory_tool.execute(action="recall", user_id=self.state.user_id)
        if mem_res.success and mem_res.data:
            self.state.preferences = list(mem_res.data)

    def process_turn(self, user_input: str, reset_steps: bool = True) -> str:
        """
        Executes a single conversational agent turn through the Think-Act-Look-Learn-Respond loop.
        """
        if reset_steps:
            self.state.reset_step_count()
        self.state.log_action(ActionEventType.TASK_STARTED, {"user_input": user_input})
        log_step("Think", f"Starting turn for user input: '{user_input}'")

        # 1. THINK: Generate or update plan
        plan = AgentPlanner.create_plan_for_request(user_input, self.state)
        if plan:
            self.state.plan = plan
            self.state.log_action(ActionEventType.PLAN_CREATED, {"goal": plan.goal, "steps": plan.steps})
            log_step("Plan", f"Created plan: {plan.goal}")

        decision = self.brain.decide_action(user_input, self.state)
        # Flatten parameters or arguments if nested by LLM
        params = decision.get("parameters") or decision.get("arguments") or {}
        if isinstance(params, dict):
            for k, v in params.items():
                if k not in decision:
                    decision[k] = v

        action_name = decision.get("action")
        self.state.current_step = f"Executing {action_name}"

        # 2. ACT: Check step limits and invoke tool or handler
        if not self.state.increment_step():
            return "I've reached the action limit for this request. I'll stop here rather than continuing unexpectedly."

        response_text = ""

        # Action: Direct Response
        if action_name == "direct_response":
            response_text = decision.get("message", "How can I assist you with cooking today?")

        # Action: Safety Confirmation response (handling Yes/No for pending confirmation)
        elif action_name == "confirm_safety":
            response_text = self._handle_safety_confirmation(decision)

        # Action: Request to save preference (Triggers Safety confirmation before saving)
        elif action_name == "request_save_preference":
            pref = decision["preference"]
            prompt = decision["prompt"]
            self.state.pending_confirmation = PendingConfirmation(
                action_type="save_preference",
                prompt=prompt,
                payload={"preference": pref}
            )
            self.state.log_action(ActionEventType.SAFETY_CONFIRMATION_REQUESTED, {"prompt": prompt})
            response_text = prompt

        # Action: Request to forget memory (Triggers Safety confirmation before deletion)
        elif action_name == "request_forget_preference":
            prompt = decision["prompt"]
            self.state.pending_confirmation = PendingConfirmation(
                action_type="clear_memory",
                prompt=prompt,
                payload={}
            )
            self.state.log_action(ActionEventType.SAFETY_CONFIRMATION_REQUESTED, {"prompt": prompt})
            response_text = prompt

        # Action: Recipe Search
        elif action_name == "search_recipes":
            response_text = self._handle_recipe_search(decision)

        # Action: Recipe Scaling
        elif action_name == "scale_recipe":
            response_text = self._handle_recipe_scaling(decision)

        # Action: Ingredient Substitution
        elif action_name == "find_substitute":
            response_text = self._handle_substitution(decision)

        # Action: Recipe Modification (spicy, veg, remove ingredient)
        elif action_name == "modify_recipe":
            response_text = self._handle_recipe_modification(decision)

        # Action: Meal Planning
        elif action_name == "create_meal_plan":
            response_text = self._handle_meal_planning(decision)

        # Action: Meal Plan Modification
        elif action_name == "modify_meal_plan":
            response_text = self._handle_meal_plan_modification(decision)

        else:
            response_text = f"I understood your request, but cannot process action '{action_name}'."

        # 5. RESPOND: Finalize response and log completion
        self.state.current_step = "Idle"
        self.state.log_action(ActionEventType.RESPONSE_GENERATED, {"response_preview": response_text[:120]})
        self.state.log_action(ActionEventType.TASK_COMPLETED, {})
        log_step("Respond", f"Finished turn. Response length: {len(response_text)}")

        return response_text

    def _handle_safety_confirmation(self, decision: Dict[str, Any]) -> str:
        confirmed = decision.get("confirmed", False)
        pending = self.state.pending_confirmation

        if not pending:
            return "No action was pending confirmation."

        self.state.pending_confirmation = None

        if confirmed:
            self.state.log_action(ActionEventType.SAFETY_CONFIRMED, {"action_type": pending.action_type})
            if pending.action_type == "save_preference":
                pref = pending.payload["preference"]
                res = self.memory_tool.execute(action="remember", user_id=self.state.user_id, preference=pref)
                self._load_memory()
                return f"Saved. I'll remember that you prefer {pref} and prioritize it in future suggestions."
            elif pending.action_type == "clear_memory":
                self.memory_tool.execute(action="clear", user_id=self.state.user_id)
                self.state.preferences = []
                return "Cleared. I've deleted your saved preferences."
        else:
            self.state.log_action(ActionEventType.SAFETY_REJECTED, {"action_type": pending.action_type})
            return "Understood. I will not save that preference."

    def _handle_recipe_search(self, decision: Dict[str, Any]) -> str:
        self.state.log_action(ActionEventType.RECIPE_SEARCH_CALLED, decision)
        self.state.previous_tool = "recipe_search"

        # Check step limit
        if not self.state.increment_step():
            return "I've reached the action limit for this request."

        # ACT: Call RecipeSearchTool with error retry and universal synthesis
        res = self.search_tool.run_with_retry(
            query=decision.get("query"),
            ingredients=decision.get("ingredients"),
            is_dish_request=decision.get("is_dish_request", False),
            diet=decision.get("diet"),
            max_cooking_time=decision.get("max_cooking_time"),
            excluded_ingredients=self.state.excluded_ingredients
        )

        # LOOK: Inspect tool result
        self.state.last_result = res.data
        if not res.success or not res.data:
            self.state.log_action(ActionEventType.TOOL_FAILED, {"tool": "recipe_search", "error": res.error})
            return "I couldn't find recipes matching your exact request. Tell me another dish or ingredients you'd like to cook!"

        self.state.log_action(ActionEventType.RECIPE_SEARCH_COMPLETED, {"count": len(res.data)})

        # LEARN: Store active recipe and target servings
        recipes: List[Recipe] = res.data
        top_recipe = recipes[0]
        self.state.current_recipe = top_recipe
        self.state.servings = top_recipe.servings

        # RESPOND: Deliver the FULL recipe immediately as requested by user
        response_parts = [
            f"Here is a complete, chef-curated recipe for **{top_recipe.name}**:",
            "",
            top_recipe.format_markdown()
        ]

        # Only mention alternatives if user provided ingredients rather than asking for a specific dish
        if not decision.get("is_dish_request") and len(recipes) > 1:
            other_names = ", ".join([f"*{r.name}* ({r.cook_time}m)" for r in recipes[1:4]])
            response_parts.append("")
            response_parts.append(f"💡 **Other dishes you can make with these ingredients:** {other_names}")

        response_parts.append("")
        response_parts.append("✨ *Would you like me to scale this for more people, make it spicier, make it vegetarian, or swap any ingredients?*")

        return "\n".join(response_parts)

    def _handle_recipe_scaling(self, decision: Dict[str, Any]) -> str:
        target_servings = decision.get("target_servings", 4)
        if not self.state.current_recipe:
            return "Please select a recipe first before scaling servings."

        self.state.log_action(ActionEventType.RECIPE_CALCULATOR_CALLED, {"target_servings": target_servings})
        self.state.previous_tool = "recipe_calculator"

        if not self.state.increment_step():
            return "I've reached the action limit for this request."

        # ACT: Scale recipe
        res = self.calculator_tool.run_with_retry(
            recipe=self.state.current_recipe,
            target_servings=target_servings
        )

        # LOOK & LEARN:
        if res.success and isinstance(res.data, Recipe):
            self.state.current_recipe = res.data
            self.state.servings = target_servings
            self.state.last_result = "Ingredients successfully scaled."
            return (
                f"I've adjusted the recipe for **{target_servings} people**.\n\n"
                f"{self.state.current_recipe.format_markdown()}"
            )
        else:
            return f"Failed to scale recipe: {res.error}"

    def _handle_substitution(self, decision: Dict[str, Any]) -> str:
        ingredient = decision.get("ingredient", "")
        self.state.previous_tool = "ingredient_substitution"

        if not self.state.increment_step():
            return "I've reached the action limit for this request."

        # ACT: Find substitute
        res = self.substitution_tool.run_with_retry(ingredient=ingredient)
        self.state.last_result = res.data

        # LOOK & LEARN:
        # If user has an active recipe containing this ingredient, offer to modify it
        extra_note = ""
        if self.state.current_recipe:
            rec_ing_names = [i.name.lower() for i in self.state.current_recipe.ingredients]
            if any(ingredient.lower() in name for name in rec_ing_names):
                extra_note = f"\n\nWould you like me to update **{self.state.current_recipe.name}** to use one of these substitutes?"

        return f"{res.message}{extra_note}"

    def _handle_recipe_modification(self, decision: Dict[str, Any]) -> str:
        if not self.state.current_recipe:
            return "Please select or search for a recipe before making modifications."

        mod_type = decision.get("modification")
        rec = copy.deepcopy(self.state.current_recipe)

        if mod_type == "spicy":
            if not rec.name.startswith("Spicy"):
                rec.name = f"Spicy {rec.name}"
            if "spicy" not in rec.diet:
                rec.diet.append("spicy")
            # Increase chili / pepper or add chili flakes
            has_chili = False
            for ing in rec.ingredients:
                if any(k in ing.name.lower() for k in ["chili", "pepper"]):
                    ing.quantity *= 1.5
                    has_chili = True
            if not has_chili:
                rec.ingredients.append(Ingredient(name="chili powder or chili flakes", quantity=1.5, unit="tsp"))

            rec.tips = (rec.tips or "") + " Increased spice level with extra chili."
            self.state.current_recipe = rec
            self.state.log_action(ActionEventType.RECIPE_MODIFIED, {"type": "spicy"})

            # PRD Section 13 / 27: Ask if user wants this remembered
            ask_remember = ""
            if "spicy" not in [p.lower() for p in self.state.preferences]:
                self.state.pending_confirmation = PendingConfirmation(
                    action_type="save_preference",
                    prompt="Would you like me to remember that you prefer spicy food for future recipes?",
                    payload={"preference": "spicy food"}
                )
                ask_remember = "\n\nWould you like me to remember that you prefer spicy food for future recipes?"

            return (
                f"Sure! I've modified **{rec.name}** to make it spicier.\n\n"
                f"{rec.format_markdown()}{ask_remember}"
            )

        elif mod_type == "vegetarian":
            if not rec.name.startswith("Vegetarian"):
                rec.name = f"Vegetarian {rec.name}"
            if "vegetarian" not in rec.diet:
                rec.diet.append("vegetarian")

            # Replace any meats (chicken, beef, pork, etc.) with tofu or chickpeas
            new_ingredients = []
            for ing in rec.ingredients:
                if any(m in ing.name.lower() for m in ["chicken", "beef", "pork", "meat"]):
                    new_ingredients.append(Ingredient(
                        name="firm tofu or chickpeas",
                        quantity=ing.quantity,
                        unit=ing.unit,
                        notes="vegetarian substitute"
                    ))
                else:
                    new_ingredients.append(ing)
            rec.ingredients = new_ingredients
            rec.tips = (rec.tips or "") + " Made 100% vegetarian by substituting plant-based protein."
            self.state.current_recipe = rec
            self.state.log_action(ActionEventType.RECIPE_MODIFIED, {"type": "vegetarian"})

            return (
                f"Sure! I've replaced meat with plant-based protein to make **{rec.name}** vegetarian.\n\n"
                f"{rec.format_markdown()}"
            )

        elif mod_type == "remove_ingredient":
            ing_to_remove = decision.get("ingredient", "").lower()
            rec.ingredients = [i for i in rec.ingredients if ing_to_remove not in i.name.lower()]
            if ing_to_remove not in self.state.excluded_ingredients:
                self.state.excluded_ingredients.append(ing_to_remove)
            self.state.current_recipe = rec
            self.state.log_action(ActionEventType.RECIPE_MODIFIED, {"type": f"remove_{ing_to_remove}"})

            return (
                f"Sure! I've removed **{ing_to_remove}** from the recipe.\n\n"
                f"{rec.format_markdown()}"
            )

        return "Recipe modified according to your specifications."

    def _handle_meal_planning(self, decision: Dict[str, Any]) -> str:
        self.state.previous_tool = "meal_planner"
        if not self.state.increment_step():
            return "I've reached the action limit for this request."

        res = self.planner_tool.run_with_retry(
            number_of_days=decision.get("days", 7),
            meals_per_day=decision.get("meals"),
            diet=decision.get("diet"),
            vegetarian_days=decision.get("vegetarian_days"),
            excluded_foods=self.state.excluded_ingredients
        )

        if res.success and isinstance(res.data, MealPlan):
            self.state.current_meal_plan = res.data
            self.state.last_result = "Meal plan generated successfully."
            return (
                f"Here is your personalized {decision.get('days', 7)}-day meal plan:\n\n"
                f"{res.message}\n\n"
                f"You can modify any meal (e.g., 'Change Wednesday dinner')."
            )
        else:
            return f"Failed to generate meal plan: {res.error}"

    def _handle_meal_plan_modification(self, decision: Dict[str, Any]) -> str:
        if not self.state.current_meal_plan:
            return "No active meal plan found to modify. Please ask to generate a meal plan first."

        day = decision.get("day", "wednesday")
        meal_type = decision.get("meal_type", "dinner")
        new_recipe = decision.get("new_recipe", "Vegetarian Pasta")

        res = self.planner_tool.execute(
            existing_plan=self.state.current_meal_plan,
            modify_day=day,
            modify_meal_type=meal_type,
            new_recipe_name=new_recipe
        )

        if res.success:
            return (
                f"Sure. I've updated **{day.capitalize()} {meal_type.capitalize()}**.\n\n"
                f"{self.state.current_meal_plan.format_markdown()}"
            )
        else:
            return f"Could not update meal: {res.error}"
