from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    fallback_used: bool = False
    retry_count: int = 0
    message: Optional[str] = None


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Executes the tool with arguments and returns a standardized ToolResult."""
        pass

    def run_with_retry(self, max_retries: int = 2, **kwargs) -> ToolResult:
        """
        Executes the tool with automatic retry and error recovery 
        conforming to PRD Section 14.
        """
        retries = 0
        last_error = None

        while retries <= max_retries:
            try:
                res = self.execute(**kwargs)
                if res.success:
                    res.retry_count = retries
                    return res
                last_error = res.error
            except Exception as e:
                last_error = str(e)
            
            retries += 1

        # If retries exhausted, attempt alternative approach / fallback if implemented
        fallback_res = self.fallback(**kwargs)
        if fallback_res:
            fallback_res.fallback_used = True
            fallback_res.retry_count = retries - 1
            return fallback_res

        return ToolResult(
            success=False,
            error=f"Tool '{self.name}' failed after {max_retries} retries: {last_error}",
            retry_count=retries - 1
        )

    def fallback(self, **kwargs) -> Optional[ToolResult]:
        """Optional fallback or alternative approach when primary execution fails."""
        return None
