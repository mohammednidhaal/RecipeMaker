import re
from typing import Any, Dict, List, Optional
from src.models import AgentState


class MockLLMBrain:
    """
    Stage 1 Fake/Mock LLM conforming to PRD Section 22.
    Parses conversational intents into structured tool action plans and decisions.
    """

    def decide_action(self, user_input: str, state: AgentState) -> Dict[str, Any]:
        text = user_input.strip().lower()

        # 1. Pending confirmation handling (Yes/No response)
        if state.pending_confirmation:
            if text in ["yes", "y", "sure", "please do", "yep", "ok", "confirm"]:
                return {
                    "action": "confirm_safety",
                    "confirmed": True,
                    "payload": state.pending_confirmation.payload
                }
            elif text in ["no", "n", "dont", "don't", "cancel", "nevermind"]:
                return {
                    "action": "confirm_safety",
                    "confirmed": False,
                    "payload": state.pending_confirmation.payload
                }

        # 2. Memory Requests: "Remember that I like spicy food"
        if "remember" in text:
            # Extract preference
            pref = user_input
            for prefix in ["remember that", "remember i", "remember"]:
                if prefix in text:
                    idx = text.find(prefix) + len(prefix)
                    pref = user_input[idx:].strip(" .!:")
                    break
            return {
                "action": "request_save_preference",
                "preference": pref,
                "prompt": f"Would you like me to remember that you prefer {pref} for future recipes?"
            }

        # 3. Forgetting Memory: "Forget my preferences"
        if any(term in text for term in ["forget", "delete memory", "clear memory"]):
            return {
                "action": "request_forget_preference",
                "prompt": "Are you sure you want to delete your saved food preferences?"
            }

        # 4. Serving adjustments / Recipe Calculator: "Make it for 6 people" or "For 4 people"
        serving_match = re.search(r'(?:make it for|for|servings?|people)\s*(\d+)', text)
        if serving_match and state.current_recipe:
            target_servings = int(serving_match.group(1))
            return {
                "action": "scale_recipe",
                "target_servings": target_servings
            }

        # 5. Missing ingredient / Substitution: "I don't have butter", "replace soy sauce"
        sub_match = re.search(r"(?:don'?t have|dont have|no|without|replace|substitute for?)\s+([a-zA-Z\s]+)", text)
        if sub_match:
            raw_ing = sub_match.group(1).split(".")[0].split(",")[0].strip()
            # Clean common filler words
            for filler in ["any", "a", "some", "the", "much"]:
                if raw_ing.startswith(filler + " "):
                    raw_ing = raw_ing[len(filler) + 1:]
            return {
                "action": "find_substitute",
                "ingredient": raw_ing
            }

        # 6. Recipe Modifications: "Make it spicy", "Make it vegetarian", "Remove onions"
        if state.current_recipe:
            if "spicy" in text:
                return {
                    "action": "modify_recipe",
                    "modification": "spicy"
                }
            if "vegetarian" in text or "veg" in text:
                return {
                    "action": "modify_recipe",
                    "modification": "vegetarian"
                }
            if "remove" in text or "without" in text:
                removed_match = re.search(r'(?:remove|without)\s+([a-zA-Z\s]+)', text)
                ing_to_remove = removed_match.group(1).strip() if removed_match else ""
                return {
                    "action": "modify_recipe",
                    "modification": "remove_ingredient",
                    "ingredient": ing_to_remove
                }

        # 7. Meal Planning: "Make a 7-day dinner plan" or "Plan my week"
        if any(term in text for term in ["meal plan", "dinner plan", "plan my week", "plan", "weekly"]):
            days = 7
            days_match = re.search(r'(\d+)[ -]day', text)
            if days_match:
                days = int(days_match.group(1))
            
            meals = ["breakfast", "lunch", "dinner"]
            if "dinner" in text and "lunch" not in text and "breakfast" not in text:
                meals = ["dinner"]

            veg_days = 0
            veg_match = re.search(r'(\d+)\s*(?:vegetarian|veg)\s*days?', text)
            if veg_match:
                veg_days = int(veg_match.group(1))

            diet = "vegetarian" if "vegetarian" in text and not veg_days else None

            return {
                "action": "create_meal_plan",
                "days": days,
                "meals": meals,
                "diet": diet,
                "vegetarian_days": veg_days
            }

        # 8. Modify specific meal in existing plan: "Change Wednesday dinner to..."
        if state.current_meal_plan and any(day in text for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
            day_match = re.search(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', text)
            day = day_match.group(1) if day_match else "wednesday"
            meal_type = "dinner"
            for mt in ["breakfast", "lunch", "dinner", "snack"]:
                if mt in text:
                    meal_type = mt
                    break
            
            return {
                "action": "modify_meal_plan",
                "day": day,
                "meal_type": meal_type,
                "new_recipe": "Vegetable Pasta"  # default substitution
            }

        # 9. Recipe Search / Generation: Extract food items, dishes, or ingredients
        # Check if user asked for a specific dish
        dish_query = None
        for prefix in [
            "give me a recipe for", "give me recipe for", "give me the recipe of", "give me the recipe for",
            "give me a", "give me", "recipe of", "recipe for", "recipes for",
            "how to make", "how do i make", "how to cook",
            "make a", "cook a", "suggest a"
        ]:
            if prefix in text:
                dish_part = text.split(prefix)[-1].strip(" .!?:")
                dish_part = re.sub(r'^(recipe|dinner|lunch|breakfast|meal|full recipe)\s*(for|of)?\s*', '', dish_part).strip()
                if dish_part and len(dish_part) > 2 and not any(w in dish_part for w in ["i have", "we have"]):
                    dish_query = dish_part
                    break

        ingredients = []
        # If user explicitly states available ingredients: "I have X, Y and Z"
        has_ingredients_cue = any(cue in text for cue in ["i have", "we have", "with my", "using", "available", "got"])
        
        common_ingredients = [
            "chicken", "rice", "eggs", "egg", "bread", "tomato", "tomatoes",
            "onion", "onions", "garlic", "pasta", "butter", "milk", "lentils",
            "tofu", "beans", "yogurt", "banana", "oats", "salmon", "asparagus",
            "lemon", "beef", "chocolate", "flour", "paneer", "cheese", "potato",
            "potatoes", "spinach", "mushrooms", "shrimp", "noodles"
        ]
        
        if has_ingredients_cue or not dish_query:
            for ing in common_ingredients:
                if re.search(r'\b' + re.escape(ing) + r'\b', text):
                    norm = ing.rstrip("s") if ing in ["eggs", "tomatoes", "onions", "potatoes", "mushrooms", "noodles"] else ing
                    if norm not in ingredients:
                        ingredients.append(norm)

        # Check for dietary cues in search
        search_diet = []
        if "vegetarian" in text or "veg" in text:
            search_diet.append("vegetarian")
        if "vegan" in text:
            search_diet.append("vegan")

        for pref in state.preferences:
            if "spicy" in pref.lower() and "spicy" not in search_diet:
                search_diet.append("spicy")
            if "vegetarian" in pref.lower() and "vegetarian" not in search_diet:
                search_diet.append("vegetarian")

        max_time = None
        time_match = re.search(r'(?:under|in|less than)\s*(\d+)\s*(?:min|minutes)', text)
        if time_match:
            max_time = int(time_match.group(1))

        if dish_query or ingredients or any(word in text for word in ["recipe", "cook", "make", "suggest", "dinner", "lunch", "food", "dish", "breakfast"]):
            return {
                "action": "search_recipes",
                "query": dish_query or user_input,
                "ingredients": ingredients,
                "is_dish_request": bool(dish_query),
                "diet": search_diet,
                "max_cooking_time": max_time
            }

        # 10. Direct conversational greeting / fallback
        return {
            "action": "direct_response",
            "message": "Hello! I'm RecipeMate AI, your live cooking assistant. Tell me what ingredients you have in your kitchen or what you'd like to cook today!"
        }
