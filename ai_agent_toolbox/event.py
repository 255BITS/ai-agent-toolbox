from dataclasses import dataclass
from typing import Optional

@dataclass
class ToolEvent:
    type: str                   # e.g., "tool"
    is_tool_call: bool          # True when it's a tool-related event
    mode: str                   # e.g., "create", "append", "close"
    id: str                     # Unique ID for the tool call
    content: Optional[str] = None  # Additional content, e.g. tool name or arg text
