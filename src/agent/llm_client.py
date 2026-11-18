import os
import json
import logging
import re
import httpx
from typing import Any, Dict, Optional
from src.models import AgentState
from src.agent.prompt import SYSTEM_PROMPT
from src.agent.llm_mock import MockLLMBrain

logger = logging.getLogger("RecipeMate")


class RealLLMBrain:
    """
    Stage 2 Real LLM client supporting Google Gemini API, OpenAI, Groq, 
    and local endpoints with graceful fallback to MockLLMBrain.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        fallback_brain: Optional[MockLLMBrain] = None
    ):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")
        self.provider = provider or ("gemini" if (os.getenv("GEMINI_API_KEY") or (self.api_key and self.api_key.startswith("AIza"))) else "openai")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.model_name = model_name or os.getenv("LLM_MODEL", "gemini-1.5-flash" if self.provider == "gemini" else "gpt-4o-mini")
        self.fallback_brain = fallback_brain or MockLLMBrain()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def update_key(self, key: str, provider: str = "gemini", model: Optional[str] = None) -> None:
        self.api_key = key.strip()
        self.provider = provider.lower()
        if model:
            self.model_name = model
        elif self.provider == "gemini":
            self.model_name = "gemini-1.5-flash"

    def decide_action(self, user_input: str, state: AgentState) -> Dict[str, Any]:
        """
        Queries the real LLM to decide on an action and generate natural conversational responses.
        Falls back to MockLLMBrain if not configured or in case of error.
        """
        if not self.is_configured:
            return self.fallback_brain.decide_action(user_input, state)

        if self.provider == "gemini":
            return self._call_gemini(user_input, state)
        else:
            return self._call_openai_compatible(user_input, state)

    def _call_gemini(self, user_input: str, state: AgentState) -> Dict[str, Any]:
        models_to_try = [self.model_name, "gemini-3-flash-preview", "gemini-3.1-flash-lite-preview", "gemini-flash-latest"]
        models_to_try = list(dict.fromkeys([m for m in models_to_try if m]))

        context_data = {
            "current_goal": state.current_goal,
            "current_recipe": state.current_recipe.name if state.current_recipe else None,
            "current_servings": state.servings,
            "preferences": state.preferences,
            "excluded_ingredients": state.excluded_ingredients,
            "pending_confirmation": state.pending_confirmation.model_dump() if state.pending_confirmation else None
        }

        instructions = (
            f"{SYSTEM_PROMPT}\n\n"
            f"You are the brain of RecipeMate AI. Decide the next action and return ONLY a valid JSON object.\n"
            f"Conversation Context: {json.dumps(context_data)}\n"
            f"Available Actions:\n"
            f"- 'search_recipes': with parameters 'query' (exact dish name or query terms), 'ingredients' (list of ingredients), 'is_dish_request' (boolean: true if user asked for a dish name, false if user gave pantry ingredients).\n"
            f"- 'scale_recipe': with parameter 'target_servings' (int).\n"
            f"- 'find_substitute': with parameter 'ingredient' (str).\n"
            f"- 'modify_recipe': with parameter 'modification' ('spicy', 'vegetarian', or 'remove_ingredient').\n"
            f"- 'create_meal_plan': with parameter 'days' (int), 'meals' (list).\n"
            f"- 'request_save_preference': with parameters 'preference', 'prompt'.\n"
            f"- 'confirm_safety': with parameter 'confirmed' (bool).\n"
            f"- 'direct_response': with parameter 'message' (conversational text or culinary guidance).\n"
            f"User input: {user_input}\n"
            f"Output strictly a JSON object with 'action' and parameters."
        )

        payload = {
            "contents": [{
                "parts": [{"text": instructions}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        last_error = None
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        # Clean code fence if present
                        text = re.sub(r'^```json\s*', '', text)
                        text = re.sub(r'\s*```$', '', text)
                        return json.loads(text.strip())
                    else:
                        last_error = f"{model} returned status {resp.status_code}: {resp.text}"
                        continue
            except Exception as e:
                last_error = str(e)
                continue

        logger.warning(f"All Gemini models failed: {last_error}. Falling back to mock brain.")
        return self.fallback_brain.decide_action(user_input, state)

    def _call_openai_compatible(self, user_input: str, state: AgentState) -> Dict[str, Any]:
        base = self.base_url or "https://api.openai.com/v1"
        url = f"{base}/chat/completions"

        context_data = {
            "current_goal": state.current_goal,
            "current_recipe": state.current_recipe.name if state.current_recipe else None,
            "current_servings": state.servings,
            "preferences": state.preferences,
            "excluded_ingredients": state.excluded_ingredients,
            "pending_confirmation": state.pending_confirmation.model_dump() if state.pending_confirmation else None
        }

        messages = [
            {
                "role": "system",
                "content": f"{SYSTEM_PROMPT}\n\nCurrent Conversation State:\n{json.dumps(context_data)}\nRespond with JSON only indicating the action and parameters."
            },
            {"role": "user", "content": user_input}
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    raw_content = resp.json()["choices"][0]["message"]["content"]
                    return json.loads(raw_content)
                else:
                    logger.warning(f"OpenAI API status {resp.status_code}. Falling back.")
                    return self.fallback_brain.decide_action(user_input, state)
        except Exception as e:
            logger.warning(f"OpenAI API request failed: {e}. Falling back.")
            return self.fallback_brain.decide_action(user_input, state)
