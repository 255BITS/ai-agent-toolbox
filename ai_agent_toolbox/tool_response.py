from dataclasses import dataclass
from typing import Any, Optional
from .parser_event import ToolUse

@dataclass
class ToolResponse:
    tool: ToolUse
    result: Optional[Any] = None
    error: Optional[Exception] = None
    message: Optional[str] = None # Optional message for more context
