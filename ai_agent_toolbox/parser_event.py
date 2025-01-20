from dataclasses import dataclass
from typing import Optional, Any, Dict

@dataclass
class ToolUse:
    name: str                   # e.g., "thinking"
    args: Dict[str, Any]        # e.g., {"thoughts": "Cogito, ergo sum"}

@dataclass
class ParserEvent:
    type: str                   # e.g., "tool"
    mode: str                   # e.g., "create", "append", "close"
    id: str                     # Unique ID for the tool call
    tool: ToolUse = None        # e.g., "thinking"
    is_tool_call: bool = False  # True when it's a tool-related event
    content: Optional[str] = None  # Additional content, e.g. tool name or arg text
