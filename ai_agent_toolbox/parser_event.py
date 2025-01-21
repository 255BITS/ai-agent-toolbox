from dataclasses import dataclass, field
from typing import Optional, Any, Dict

@dataclass
class ToolUse:
    name: str
    args: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParserEvent:
    # 'type' will be either "text" or "tool"
    type: str

    # 'mode' is "create", "append", or "close"
    mode: str

    # Unique ID for the text or tool being tracked
    id: str

    # If this event is for a tool, store the final ToolUse object when closing.
    tool: Optional[ToolUse] = None
    
    # For convenience, also store is_tool_call (True if type=="tool")
    is_tool_call: bool = False

    # Free-form content (e.g. a snippet of text or partial argument text)
    content: Optional[str] = None
