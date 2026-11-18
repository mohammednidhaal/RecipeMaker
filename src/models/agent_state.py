from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.models.recipe import Recipe
from src.models.meal_plan import MealPlan


class ActionEventType(str, Enum):
    TASK_STARTED = "Task started"
    PLAN_CREATED = "Plan created"
    PLAN_UPDATED = "Plan updated"
    TOOL_CALLED = "Tool called"
    TOOL_COMPLETED = "Tool completed"
    TOOL_FAILED = "Tool failed"
    TOOL_RETRY = "Tool retried"
    RECIPE_SEARCH_CALLED = "Recipe search called"
    RECIPE_SEARCH_COMPLETED = "Recipe search completed"
    RECIPE_CALCULATOR_CALLED = "Recipe calculator called"
    RECIPE_MODIFIED = "Recipe modified"
    SAFETY_CONFIRMATION_REQUESTED = "Safety confirmation requested"
    SAFETY_CONFIRMED = "Safety confirmed"
    SAFETY_REJECTED = "Safety rejected"
    RESPONSE_GENERATED = "Response generated"
    TASK_COMPLETED = "Task completed"
    LIMIT_EXCEEDED = "Action limit exceeded"


class ActionLog(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    event_type: str = Field(..., description="Action log event name conforming to PRD Section 15.3")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event payload or context")


class TaskPlan(BaseModel):
    goal: str = Field(..., description="High level user objective")
    steps: List[str] = Field(default_factory=list, description="Planned sequential steps")
    current_step_index: int = Field(0, description="Pointer to active step in the plan")
    completed: bool = Field(False, description="Whether the plan has concluded")

    def mark_step_done(self) -> None:
        self.current_step_index += 1
        if self.current_step_index >= len(self.steps):
            self.completed = True


class PendingConfirmation(BaseModel):
    action_type: str = Field(..., description="E.g., 'save_preference' or 'delete_memory'")
    prompt: str = Field(..., description="Question posed to the user for confirmation")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Data to commit upon approval")


class AgentState(BaseModel):
    user_id: str = Field("default_user", description="Identifier of the user")
    conversation_id: str = Field("default_conv", description="Session identifier")
    current_goal: str = Field("General Assistance", description="Active user request or task objective")
    current_recipe: Optional[Recipe] = Field(None, description="Currently active recipe in context")
    current_meal_plan: Optional[MealPlan] = Field(None, description="Currently active meal plan in context")
    servings: int = Field(2, description="Target serving size", ge=1)
    preferences: List[str] = Field(default_factory=list, description="Active user preferences for this session")
    excluded_ingredients: List[str] = Field(default_factory=list, description="Ingredients to avoid")
    current_step: str = Field("Idle", description="Current execution stage description")
    previous_tool: Optional[str] = Field(None, description="Most recently invoked tool name")
    last_result: Optional[Any] = Field(None, description="Output returned by the last tool execution")
    step_count: int = Field(0, description="Counter of agent actions taken in current task")
    max_steps: int = Field(10, description="Safety limit for maximum actions per task (PRD Section 15.2)")
    plan: Optional[TaskPlan] = Field(None, description="Task plan created prior to tool usage")
    pending_confirmation: Optional[PendingConfirmation] = Field(None, description="Awaiting user confirmation")
    action_logs: List[ActionLog] = Field(default_factory=list, description="Audit log of agent execution")

    def log_action(self, event_type: str, details: Optional[Dict[str, Any]] = None) -> ActionLog:
        """Appends a new action log entry conforming to PRD Section 15.3."""
        entry = ActionLog(event_type=event_type, details=details or {})
        self.action_logs.append(entry)
        return entry

    def increment_step(self) -> bool:
        """Increments action step count and checks against max_steps."""
        self.step_count += 1
        if self.step_count > self.max_steps:
            self.log_action(ActionEventType.LIMIT_EXCEEDED, {"step_count": self.step_count, "max": self.max_steps})
            return False
        return True

    def reset_step_count(self) -> None:
        self.step_count = 0
