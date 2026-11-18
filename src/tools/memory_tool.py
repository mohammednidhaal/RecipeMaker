import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.tools.base import BaseTool, ToolResult


class MemoryTool(BaseTool):
    name = "memory_tool"
    description = (
        "Store, recall, search, and manage persistent user preferences, "
        "dietary restrictions, and cooking habits with safety controls."
    )

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.file_path = Path(storage_path)
        else:
            self.file_path = Path(__file__).parent.parent.parent / "data" / "user_preferences.json"
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({"users": {}}, f, indent=2)

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"users": {}}

    def _save(self, data: Dict[str, Any]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def execute(
        self,
        action: str,  # "remember", "recall", "list", "forget", "clear"
        user_id: str = "default_user",
        preference: Optional[str] = None,
        query: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        data = self._load()
        users = data.setdefault("users", {})
        user_profile = users.setdefault(user_id, {
            "preferences": [],
            "allergies": [],
            "disliked_ingredients": [],
            "default_servings": 2,
            "updated_at": datetime.now().isoformat()
        })

        act = action.lower()

        if act == "remember":
            if not preference or not preference.strip():
                return ToolResult(success=False, error="Preference text is required to remember.")
            pref_clean = preference.strip()
            if pref_clean not in user_profile["preferences"]:
                user_profile["preferences"].append(pref_clean)
                user_profile["updated_at"] = datetime.now().isoformat()
                self._save(data)
                return ToolResult(
                    success=True,
                    data=user_profile["preferences"],
                    message=f"Saved preference: '{pref_clean}'."
                )
            return ToolResult(
                success=True,
                data=user_profile["preferences"],
                message=f"Preference '{pref_clean}' is already saved."
            )

        elif act == "recall" or act == "list":
            prefs = user_profile.get("preferences", [])
            if query and query.strip():
                q = query.strip().lower()
                matched = [p for p in prefs if q in p.lower()]
            else:
                matched = prefs

            if not matched:
                return ToolResult(
                    success=True,
                    data=[],
                    message="No matching user preferences found."
                )

            lines = ["Saved preferences:"] + [f"- {p}" for p in matched]
            return ToolResult(
                success=True,
                data=matched,
                message="\n".join(lines)
            )

        elif act == "forget":
            if not preference:
                return ToolResult(success=False, error="Specify which preference to forget.")
            pref_target = preference.strip().lower()
            original_len = len(user_profile["preferences"])
            user_profile["preferences"] = [
                p for p in user_profile["preferences"] if pref_target not in p.lower()
            ]
            if len(user_profile["preferences"]) < original_len:
                user_profile["updated_at"] = datetime.now().isoformat()
                self._save(data)
                return ToolResult(
                    success=True,
                    data=user_profile["preferences"],
                    message=f"Removed preferences matching '{preference}'."
                )
            return ToolResult(
                success=False,
                error=f"No preference found matching '{preference}'."
            )

        elif act == "clear":
            user_profile["preferences"] = []
            user_profile["updated_at"] = datetime.now().isoformat()
            self._save(data)
            return ToolResult(
                success=True,
                data=[],
                message="Cleared all saved preferences for user."
            )

        else:
            return ToolResult(
                success=False,
                error=f"Unsupported memory action '{action}'. Use remember, recall, list, forget, or clear."
            )
