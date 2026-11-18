import pytest
from src.api.server import (
    chat_endpoint,
    get_state,
    reset_session,
    list_recipes,
    get_user_preferences,
    clear_user_preferences,
    ChatRequest
)
from fastapi import HTTPException


def test_api_chat_success():
    req = ChatRequest(
        message="I have chicken and rice",
        user_id="test_api_user",
        session_id="sess_1"
    )
    res = chat_endpoint(req)
    assert res.response
    assert res.state["current_recipe"] is not None
    assert len(res.action_logs) > 0


def test_api_chat_empty_validation():
    req = ChatRequest(
        message="   ",
        user_id="test_api_user",
        session_id="sess_1"
    )
    with pytest.raises(HTTPException) as excinfo:
        chat_endpoint(req)
    assert excinfo.value.status_code == 400


def test_api_get_state():
    state = get_state(session_id="sess_1", user_id="test_api_user")
    assert "servings" in state
    assert "current_recipe" in state


def test_api_recipes_list():
    recipes = list_recipes()
    assert len(recipes) >= 10
    assert any(r["name"] == "Chicken Tomato Rice" for r in recipes)


def test_api_reset():
    res = reset_session(session_id="sess_1", user_id="test_api_user")
    assert res["status"] == "success"


def test_api_preferences():
    clear_user_preferences(user_id="test_pref_user")
    res = get_user_preferences(user_id="test_pref_user")
    assert res["preferences"] == []
