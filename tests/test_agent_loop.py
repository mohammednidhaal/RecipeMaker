import pytest
from src.agent import AgentExecutor, MockLLMBrain
from src.tools.base import ToolResult


def test_scenario_1_basic_recipe():
    agent = AgentExecutor(user_id="test_user_1")
    response = agent.process_turn("I have eggs and bread.")
    assert "recipe" in response.lower()
    assert any(dish in response for dish in ["Egg", "French Toast", "Sandwich"])
    assert "Ingredients" in response
    assert "Instructions" in response
    assert agent.state.current_recipe is not None
    assert agent.state.action_logs[0].event_type == "Task started"


def test_scenario_2_recipe_modification():
    agent = AgentExecutor(user_id="test_user_2")
    agent.process_turn("I have chicken and rice.")
    assert agent.state.current_recipe is not None
    
    # Modify recipe to be spicy
    response = agent.process_turn("Make it spicy.")
    assert "modified" in response.lower() or "spicier" in response.lower()
    assert "Spicy" in agent.state.current_recipe.name
    assert "spicy" in [d.lower() for d in agent.state.current_recipe.diet]


def test_scenario_3_serving_adjustment():
    agent = AgentExecutor(user_id="test_user_3")
    agent.process_turn("I have chicken and rice.")
    initial_servings = agent.state.current_recipe.servings

    # Scale for 6 people
    response = agent.process_turn("Make it for 6 people.")
    assert "6 people" in response or "6" in response
    assert agent.state.current_recipe.servings == 6
    assert agent.state.servings == 6


def test_scenario_4_missing_ingredient():
    agent = AgentExecutor(user_id="test_user_4")
    agent.process_turn("I have eggs and bread.")
    
    # Missing butter
    response = agent.process_turn("I don't have butter.")
    assert "Substitutes for 'Butter'" in response or "oil" in response.lower()
    assert "alter the flavor or texture" in response


def test_scenario_5_meal_plan():
    agent = AgentExecutor(user_id="test_user_5")
    response = agent.process_turn("Make a 7-day dinner plan.")
    assert "7-Day Meal Plan" in response or "Meal Plan" in response
    assert "Monday" in response
    assert agent.state.current_meal_plan is not None

    # Test modifying Wednesday dinner
    mod_response = agent.process_turn("Change Wednesday dinner to Vegetable Pasta")
    assert "Wednesday" in mod_response
    assert "Vegetable Pasta" in mod_response


def test_scenario_6_memory_and_personalization(tmp_path):
    storage_file = tmp_path / "memory_test.json"
    agent = AgentExecutor(user_id="pref_user")
    agent.memory_tool.file_path = storage_file

    # Step 1: User says "Remember that I like spicy food."
    resp1 = agent.process_turn("Remember that I like spicy food.")
    assert "Would you like me to remember" in resp1
    assert agent.state.pending_confirmation is not None

    # Step 2: Confirmation "Yes"
    resp2 = agent.process_turn("Yes")
    assert "Saved" in resp2
    assert any("spicy" in p.lower() for p in agent.state.preferences)

    # Step 3: Later session, user asks for chicken recipe
    agent2 = AgentExecutor(user_id="pref_user")
    agent2.memory_tool.file_path = storage_file
    agent2._load_memory()
    resp3 = agent2.process_turn("Suggest a chicken recipe.")
    assert "Spicy" in resp3 or "spicy" in resp3.lower()


def test_scenario_7_tool_failure_recovery():
    agent = AgentExecutor(user_id="test_user_7")
    
    # Mock search tool to fail initially
    original_execute = agent.search_tool.execute
    call_count = {"count": 0}

    def failing_execute(**kwargs):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return ToolResult(success=False, error="Simulated network error")
        return original_execute(**kwargs)

    agent.search_tool.execute = failing_execute

    response = agent.process_turn("Suggest a chicken recipe.")
    # Should recover via retry mechanism
    assert call_count["count"] > 1
    assert "recipe" in response.lower() or "Chicken" in response


def test_scenario_8_step_limit():
    agent = AgentExecutor(user_id="test_user_8", max_steps=2)
    # Simulate a running task where actions accumulate and exceed step limit
    agent.state.step_count = 2
    res = agent.process_turn("Suggest a recipe", reset_steps=False)
    assert "reached the action limit" in res


def test_any_food_item_returns_full_recipe():
    agent = AgentExecutor(user_id="test_any_food")
    
    # 1. Ask for Biryani
    resp_biryani = agent.process_turn("Give me a recipe for Biryani")
    assert "Biryani" in resp_biryani
    assert "### Ingredients" in resp_biryani
    assert "### Instructions" in resp_biryani
    assert agent.state.current_recipe.name == "Authentic Chicken Biryani"

    # 2. Ask for a dish synthesized dynamically (e.g., Avocado Toast)
    resp_tacos = agent.process_turn("How to make Tacos")
    assert "Taco" in resp_tacos
    assert "### Ingredients" in resp_tacos
    assert "### Instructions" in resp_tacos

    # 3. Ask with arbitrary ingredients
    resp_custom = agent.process_turn("I have salmon and asparagus")
    assert "Salmon" in resp_custom
    assert "### Ingredients" in resp_custom
    assert "### Instructions" in resp_custom
