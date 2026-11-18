import os
import pytest
from src.agent import RealLLMBrain, AgentExecutor
from src.models import AgentState


def test_real_llm_brain_fallback_when_unconfigured():
    brain = RealLLMBrain(api_key="")
    assert brain.is_configured is False
    
    state = AgentState(user_id="test_user")
    decision = brain.decide_action("I have eggs and bread", state)
    assert decision["action"] == "search_recipes"
    assert "eggs" in decision["ingredients"] or "bread" in decision["ingredients"]


def test_executor_with_real_llm_brain():
    brain = RealLLMBrain(api_key=None)
    agent = AgentExecutor(brain=brain)
    response = agent.process_turn("I have chicken and rice")
    assert "recipe" in response.lower()
    assert agent.state.current_recipe is not None
