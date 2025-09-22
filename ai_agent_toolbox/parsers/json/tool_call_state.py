"""Tool call state tracking for JSON parsers."""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


@dataclass
class ToolCallState:
    """Tracks state for an in-flight JSON tool call."""

    internal_id: str
    name: Optional[str] = None
    argument_buffer: str = ""
    created: bool = False
    closed: bool = False
    keys: List[Tuple[str, Any]] = field(default_factory=list)
