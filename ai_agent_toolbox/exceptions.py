"""Custom exceptions for the ai_agent_toolbox package."""

class ToolConflictError(Exception):
    """Raised when trying to register a tool name that already exists."""

    pass


__all__ = ["ToolConflictError"]
