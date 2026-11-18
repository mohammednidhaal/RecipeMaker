import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agent import AgentExecutor, RealLLMBrain
from src.tools.recipe_search import RecipeSearchTool
from src.tools.memory_tool import MemoryTool

app = FastAPI(
    title="RecipeMate AI",
    description="Conversational AI Recipe Planning and Cooking Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active user sessions store
sessions: Dict[str, AgentExecutor] = {}


def get_or_create_agent(session_id: str, user_id: str = "default_user") -> AgentExecutor:
    key = f"{user_id}:{session_id}"
    if key not in sessions:
        brain = RealLLMBrain()
        sessions[key] = AgentExecutor(
            user_id=user_id,
            conversation_id=session_id,
            brain=brain
        )
    return sessions[key]


class ChatRequest(BaseModel):
    message: str = Field(..., description="User chat input")
    user_id: str = Field("default_user", description="User identifier")
    session_id: str = Field("default_session", description="Conversation session ID")


class ChatResponse(BaseModel):
    response: str
    state: Dict[str, Any]
    plan: Optional[Dict[str, Any]] = None
    action_logs: List[Dict[str, Any]] = []


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    agent = get_or_create_agent(req.session_id, req.user_id)
    response_text = agent.process_turn(req.message)

    state_dict = {
        "current_goal": agent.state.current_goal,
        "current_recipe": agent.state.current_recipe.model_dump() if agent.state.current_recipe else None,
        "current_meal_plan": agent.state.current_meal_plan.model_dump() if agent.state.current_meal_plan else None,
        "servings": agent.state.servings,
        "preferences": agent.state.preferences,
        "excluded_ingredients": agent.state.excluded_ingredients,
        "pending_confirmation": agent.state.pending_confirmation.model_dump() if agent.state.pending_confirmation else None,
        "step_count": agent.state.step_count,
        "max_steps": agent.state.max_steps
    }

    plan_dict = agent.state.plan.model_dump() if agent.state.plan else None
    logs_list = [log.model_dump() for log in agent.state.action_logs[-8:]]

    return ChatResponse(
        response=response_text,
        state=state_dict,
        plan=plan_dict,
        action_logs=logs_list
    )


@app.get("/api/state")
def get_state(session_id: str = "default_session", user_id: str = "default_user"):
    agent = get_or_create_agent(session_id, user_id)
    return {
        "current_recipe": agent.state.current_recipe.model_dump() if agent.state.current_recipe else None,
        "current_meal_plan": agent.state.current_meal_plan.model_dump() if agent.state.current_meal_plan else None,
        "servings": agent.state.servings,
        "preferences": agent.state.preferences,
        "excluded_ingredients": agent.state.excluded_ingredients,
        "pending_confirmation": agent.state.pending_confirmation.model_dump() if agent.state.pending_confirmation else None
    }


@app.post("/api/reset")
def reset_session(session_id: str = "default_session", user_id: str = "default_user"):
    key = f"{user_id}:{session_id}"
    if key in sessions:
        del sessions[key]
    return {"status": "success", "message": "Session reset successfully."}


@app.get("/api/recipes")
def list_recipes():
    tool = RecipeSearchTool()
    return [r.model_dump() for r in tool._recipes]


@app.get("/api/preferences")
def get_user_preferences(user_id: str = "default_user"):
    tool = MemoryTool()
    res = tool.execute(action="recall", user_id=user_id)
    return {"preferences": res.data or []}


@app.post("/api/preferences/clear")
def clear_user_preferences(user_id: str = "default_user"):
    tool = MemoryTool()
    tool.execute(action="clear", user_id=user_id)
    return {"status": "success", "message": "Preferences cleared."}


class ApiKeySettingsRequest(BaseModel):
    api_key: str = Field(..., description="Gemini or OpenAI API key")
    provider: str = Field("gemini", description="'gemini' or 'openai'")
    model: Optional[str] = Field(None, description="Optional custom model name")


@app.post("/api/settings/api-key")
def configure_api_key(req: ApiKeySettingsRequest):
    key = req.api_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="API key cannot be empty.")

    # Update all active sessions
    for agent in sessions.values():
        if isinstance(agent.brain, RealLLMBrain):
            agent.brain.update_key(key, provider=req.provider, model=req.model)

    # Persist in .env
    env_file = Path(__file__).parent.parent.parent / ".env"
    env_var_name = "GEMINI_API_KEY" if req.provider.lower() == "gemini" else "OPENAI_API_KEY"
    try:
        with open(env_file, "a", encoding="utf-8") as f:
            f.write(f"\n{env_var_name}={key}\n")
    except Exception:
        pass

    return {
        "status": "success",
        "provider": req.provider,
        "message": f"Successfully activated live {req.provider.upper()} integration!"
    }


@app.get("/api/settings")
def get_settings():
    has_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or any(
        isinstance(a.brain, RealLLMBrain) and a.brain.is_configured for a in sessions.values()
    ))
    return {
        "live_llm_active": has_key,
        "default_provider": "gemini" if os.getenv("GEMINI_API_KEY") else ("openai" if os.getenv("OPENAI_API_KEY") else "mock/synthesizer")
    }


# Mount static files
static_dir = Path(__file__).parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
