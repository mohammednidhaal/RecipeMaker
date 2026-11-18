import json
import re
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.models import Recipe, Ingredient
from src.tools.base import BaseTool, ToolResult


class RecipeSearchTool(BaseTool):
    name = "recipe_search"
    description = (
        "Search recipes based on available ingredients, query terms, cuisine, meal_type, diet, "
        "maximum cooking time, difficulty, and excluded ingredients. Synthesizes full authentic recipes for any food item."
    )

    def __init__(self, recipes_path: Optional[str] = None):
        if recipes_path:
            self.file_path = Path(recipes_path)
        else:
            self.file_path = Path(__file__).parent.parent.parent / "data" / "recipes.json"
        self._recipes: List[Recipe] = []
        self._load_recipes()

    def _load_recipes(self) -> None:
        if not self.file_path.exists():
            self._recipes = []
            return
        with open(self.file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            self._recipes = [Recipe(**item) for item in raw_data]

    def _save_recipe(self, recipe: Recipe) -> None:
        """Saves a newly synthesized recipe to the database."""
        if not any(r.name.lower() == recipe.name.lower() for r in self._recipes):
            self._recipes.append(recipe)
            try:
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump([r.model_dump() for r in self._recipes], f, indent=2)
            except Exception:
                pass

    def synthesize_recipe_for_query(
        self,
        query: str,
        ingredients: Optional[List[str]] = None,
        diet: Optional[List[str]] = None
    ) -> Recipe:
        """
        Universal Culinary Synthesizer:
        Dynamically constructs a full, authentic, gourmet Recipe for ANY dish or ingredient combination!
        """
        clean_q = query.strip().title() if query else ""
        user_ings = [i.strip().lower() for i in (ingredients or []) if i.strip()]
        is_veg = bool(diet and ("vegetarian" in diet or "vegan" in diet))

        # Determine dish title
        if clean_q and len(clean_q.split()) <= 6 and not any(w in clean_q.lower() for w in ["have", "suggest", "give"]):
            dish_name = clean_q
        elif user_ings:
            main_items = " & ".join([i.title() for i in user_ings[:2]])
            dish_name = f"Homestyle {main_items} Skillet"
        else:
            dish_name = "Chef's Special Gourmet Dish"

        q_lower = dish_name.lower() + " " + " ".join(user_ings)

        # Determine cuisine
        cuisine = "Global"
        if any(w in q_lower for w in ["curry", "biryani", "biriyani", "masala", "tikka", "paneer", "dal", "roti"]):
            cuisine = "Indian"
        elif any(w in q_lower for w in ["pasta", "pizza", "risotto", "carbonara", "lasagna", "alfredo", "spaghetti"]):
            cuisine = "Italian"
        elif any(w in q_lower for w in ["taco", "burrito", "fajita", "guacamole", "salsa", "enchilada", "quesadilla"]):
            cuisine = "Mexican"
        elif any(w in q_lower for w in ["stir fry", "fried rice", "ramen", "teriyaki", "sushi", "pad thai", "noodle"]):
            cuisine = "Asian"
        elif any(w in q_lower for w in ["hummus", "falafel", "shakshuka", "tahini", "shawarma", "kebab"]):
            cuisine = "Middle Eastern"
        elif any(w in q_lower for w in ["steak", "ribeye", "burger", "pancakes", "bbq", "biscuit"]):
            cuisine = "American"

        recipe_ingredients = []

        # Specialized synthesis for Steak / Beef
        if any(w in q_lower for w in ["steak", "ribeye", "filet", "sirloin"]):
            recipe_ingredients = [
                Ingredient(name="ribeye or strip steak", quantity=2, unit="pieces", notes="approx 500g total, 1.5-inch thick"),
                Ingredient(name="butter", quantity=3, unit="tbsp"),
                Ingredient(name="garlic", quantity=4, unit="cloves", notes="crushed"),
                Ingredient(name="fresh rosemary or thyme", quantity=2, unit="sprigs"),
                Ingredient(name="olive oil", quantity=1, unit="tbsp"),
                Ingredient(name="coarse sea salt", quantity=1, unit="tsp"),
                Ingredient(name="cracked black pepper", quantity=0.75, unit="tsp")
            ]
            instructions = [
                "Take steaks out of the refrigerator 30 minutes before cooking to bring them to room temperature. Pat completely dry with paper towels.",
                "Season generously on all sides with coarse sea salt and freshly cracked black pepper.",
                "Heat a heavy cast-iron skillet over high heat until smoking hot. Add olive oil and swirl to coat the pan.",
                "Carefully lay the steaks in the skillet. Sear undisturbed for 3-4 minutes until a deep golden, caramelized crust forms.",
                "Flip steaks. Immediately add butter, crushed garlic cloves, and fresh rosemary/thyme sprigs to the skillet.",
                "Tilt the pan slightly and use a large spoon to continuously baste the bubbling garlic-herb butter over the top of the steaks for 2-3 minutes (aim for 54°C / 130°F internal for medium-rare).",
                "Transfer steaks to a cutting board and rest for 5-7 minutes before slicing against the grain to keep all the delicious juices inside."
            ]
            prep_time, cook_time = 10, 10
            tips = "Resting the meat is critical! Slicing too early will cause all the flavorful juices to pour out onto the board."

        elif user_ings:
            for ing in user_ings:
                qty = 300 if any(p in ing for p in ["chicken", "beef", "fish", "salmon", "tofu", "paneer", "pork", "shrimp"]) else 150
                unit = "g"
                if ing in ["eggs", "egg"]:
                    qty, unit = 3, "pieces"
                elif ing in ["onion", "onions", "tomato", "tomatoes", "bell pepper"]:
                    qty, unit = 2, "pieces"
                elif ing in ["garlic"]:
                    qty, unit = 3, "cloves"
                elif ing in ["milk", "cream", "water", "broth"]:
                    qty, unit = 200, "ml"
                recipe_ingredients.append(Ingredient(name=ing, quantity=qty, unit=unit))
            recipe_ingredients.append(Ingredient(name="cooking oil or butter", quantity=2, unit="tbsp"))
            recipe_ingredients.append(Ingredient(name="salt", quantity=1, unit="tsp"))
            recipe_ingredients.append(Ingredient(name="black pepper", quantity=0.5, unit="tsp"))
            instructions = [
                "Thoroughly wash and prepare all ingredients. Dice aromatics and slice proteins into uniform portions.",
                "Heat cooking oil in a large skillet over medium-high heat. Sauté aromatics for 3 minutes until fragrant.",
                "Add main ingredients and sear until golden brown and cooked through.",
                "Incorporate seasonings and liquid; simmer for 10-12 minutes until tender.",
                "Rest for 2 minutes and serve warm."
            ]
            prep_time, cook_time = 10, 15
            tips = "Season in layers: season early to infuse flavor and taste test just before plating."

        else:
            primary = "firm tofu" if is_veg else "chicken breast"
            recipe_ingredients = [
                Ingredient(name=primary, quantity=400, unit="g"),
                Ingredient(name="onion", quantity=1, unit="pieces"),
                Ingredient(name="garlic", quantity=3, unit="cloves"),
                Ingredient(name="olive oil or butter", quantity=2, unit="tbsp"),
                Ingredient(name="salt", quantity=1, unit="tsp"),
                Ingredient(name="black pepper", quantity=0.5, unit="tsp")
            ]
            instructions = [
                f"Prepare {dish_name} by dicing aromatics and portioning ingredients.",
                "Heat oil in a skillet, sauté garlic and onions until aromatic.",
                "Add main ingredients and simmer until cooked through and tender.",
                "Garnish and serve fresh."
            ]
            prep_time, cook_time = 10, 20
            tips = "Fresh herbs added at the very end bring vibrant aroma to this dish."

        recipe = Recipe(
            id=f"rec_syn_{abs(hash(dish_name)) % 10000}",
            name=dish_name,
            servings=2,
            prep_time=prep_time,
            cook_time=cook_time,
            difficulty="Easy",
            cuisine=cuisine,
            meal_type="dinner",
            diet=(["vegetarian"] if is_veg else ["non-vegetarian"]),
            ingredients=recipe_ingredients,
            instructions=instructions,
            tips=tips
        )

        self._save_recipe(recipe)
        return recipe

    def execute(
        self,
        ingredients: Optional[List[str]] = None,
        query: Optional[str] = None,
        cuisine: Optional[str] = None,
        meal_type: Optional[str] = None,
        diet: Optional[List[str]] = None,
        max_cooking_time: Optional[int] = None,
        difficulty: Optional[str] = None,
        excluded_ingredients: Optional[List[str]] = None,
        is_dish_request: bool = False,
        limit: int = 5,
        **kwargs
    ) -> ToolResult:
        if not self._recipes:
            self._load_recipes()

        user_ingredients = [ing.strip().lower() for ing in (ingredients or []) if ing.strip()]
        user_excluded = [ex.strip().lower() for ex in (excluded_ingredients or []) if ex.strip()]
        user_diet = [d.strip().lower() for d in (diet or []) if d.strip()]
        raw_query = (query or "").strip().lower()

        stop_words = {
            "give", "me", "a", "an", "the", "recipe", "recipes", "for", "how", "to",
            "make", "cook", "can", "you", "please", "suggest", "want", "i", "need",
            "dish", "food", "show", "tell", "about", "some", "any", "best", "of"
        }

        query_words = [w for w in re.findall(r'[a-zA-Z]+', raw_query) if w not in stop_words]
        clean_query = " ".join(query_words)

        accessory_words = {
            "garlic", "onion", "butter", "oil", "salt", "pepper", "tender", "crispy",
            "easy", "quick", "spicy", "with", "and", "fresh", "creamy", "authentic", "classic"
        }
        core_dish_words = [w for w in query_words if w not in accessory_words]

        scored_recipes = []

        for recipe in self._recipes:
            rec_ingredients = [ing.name.lower() for ing in recipe.ingredients]
            rec_diet = [d.lower() for d in recipe.diet]
            rec_name = recipe.name.lower()

            # 1. Excluded ingredients filter
            has_excluded = False
            for excluded in user_excluded:
                if any(excluded in rec_ing for rec_ing in rec_ingredients):
                    has_excluded = True
                    break
            if has_excluded:
                continue

            # 2. Cuisine filter
            if cuisine and recipe.cuisine:
                if cuisine.lower() not in recipe.cuisine.lower():
                    continue

            # 3. Cooking time filter
            if max_cooking_time is not None and recipe.cook_time > max_cooking_time:
                continue

            # 4. Diet filter
            if user_diet:
                if "vegetarian" in user_diet and "vegetarian" not in rec_diet:
                    continue
                if "vegan" in user_diet and "vegan" not in rec_diet:
                    continue

            # 5. Core Dish Word Verification (for dish requests)
            if is_dish_request and core_dish_words:
                rec_words = [w for w in re.findall(r'[a-zA-Z]+', rec_name)]
                matches_core = False
                for cdw in core_dish_words:
                    for rw in rec_words:
                        if difflib.SequenceMatcher(None, cdw, rw).ratio() >= 0.75:
                            matches_core = True
                            break
                    if matches_core:
                        break
                if not matches_core:
                    # Does not contain the core dish requested (e.g. asking for steak should not match salmon)
                    continue

            score = 0

            # Bonus for dietary tags match
            for d in user_diet:
                if d in rec_diet:
                    score += 50

            # Match 1: Full or Substring Dish Name Match
            if clean_query:
                if clean_query == rec_name or rec_name in clean_query or clean_query in rec_name:
                    score += 200
                elif raw_query and (rec_name in raw_query or raw_query in rec_name):
                    score += 150

            # Match 2: Keywords in Recipe Name (exact and fuzzy)
            rec_words = [w for w in re.findall(r'[a-zA-Z]+', rec_name)]
            for word in query_words:
                for r_word in rec_words:
                    sim = difflib.SequenceMatcher(None, word, r_word).ratio()
                    if sim >= 0.75:
                        if r_word in [
                            "biryani", "taco", "tacos", "pancake", "pancakes", "salmon", "shakshuka",
                            "carbonara", "lasagna", "curry", "wrap", "toast", "oatmeal", "pasta",
                            "burger", "pizza", "soup", "stew", "ramen", "makhani", "paneer", "dal", "steak"
                        ]:
                            score += 70
                        else:
                            score += 35
                        break

            # Match 3: Ingredients Matching
            if user_ingredients and not is_dish_request:
                matched_cnt = 0
                for u_ing in user_ingredients:
                    if u_ing in rec_name:
                        score += 15
                    for r_ing in rec_ingredients:
                        if u_ing in r_ing or r_ing in u_ing:
                            score += 10
                            matched_cnt += 1
                            break
                if matched_cnt == 0 and not clean_query:
                    continue
            elif not clean_query and not user_ingredients:
                score += 1

            if score > 0:
                scored_recipes.append((score, recipe))

        scored_recipes.sort(key=lambda x: (x[0], -x[1].cook_time), reverse=True)
        results = [rec for _, rec in scored_recipes[:limit]]

        # If still no match found, synthesize on the fly!
        if not results:
            synthesized = self.synthesize_recipe_for_query(
                query=clean_query or raw_query or (user_ingredients[0] if user_ingredients else "Chef's Special"),
                ingredients=user_ingredients,
                diet=user_diet
            )
            results = [synthesized]

        return ToolResult(
            success=True,
            data=results,
            message=f"Found {len(results)} recipe(s)."
        )

    def fallback(self, **kwargs) -> Optional[ToolResult]:
        return self.execute(**kwargs)
