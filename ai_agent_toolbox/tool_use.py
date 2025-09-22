from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class ToolUse:
    name: str
    args: Dict[str, Any] = field(default_factory=dict)
