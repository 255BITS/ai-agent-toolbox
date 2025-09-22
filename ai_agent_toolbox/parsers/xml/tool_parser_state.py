"""Tool parser state definitions."""

from enum import Enum


class ToolParserState(str, Enum):
    """States for :class:`ToolParser`."""

    WAITING_FOR_NAME = "waiting_for_name"
    HAS_NAME = "has_name"
    DONE = "done"
