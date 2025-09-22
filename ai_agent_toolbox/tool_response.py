from dataclasses import dataclass
from typing import Any, Optional
from .tool_use import ToolUse

@dataclass
class ToolResponse:
    tool: ToolUse
    result: Optional[Any] = None
