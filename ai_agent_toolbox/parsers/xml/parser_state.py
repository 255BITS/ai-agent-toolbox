"""Parser state definitions for XML parsing."""
from __future__ import annotations

from enum import Enum


class ParserState(str, Enum):
    """Possible states for the :class:`XMLParser`."""

    OUTSIDE = "outside"
    INSIDE_TOOL = "inside_tool"


__all__ = ["ParserState"]
