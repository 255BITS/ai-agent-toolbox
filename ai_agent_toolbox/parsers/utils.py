"""Utility helpers shared by parser implementations."""

from __future__ import annotations

import uuid
from typing import List
from collections.abc import MutableSequence

from ai_agent_toolbox.parser_event import ParserEvent


def emit_text_block_events(text_buffer: MutableSequence[str]) -> List[ParserEvent]:
    """Convert buffered text into create/append/close events.

    Args:
        text_buffer: A mutable sequence accumulating pieces of text that should
            be emitted together as a single text block.

    Returns:
        A list of ``ParserEvent`` objects representing the standard
        create/append/close sequence for the concatenated text. If the
        concatenated text is empty, an empty list is returned.

    Side Effects:
        The provided buffer is cleared in-place regardless of whether any
        events were produced.
    """

    if not text_buffer:
        return []

    text = "".join(text_buffer)

    # Always clear the buffer, even if the joined text is empty. This mirrors
    # the previous behaviour in the parsers that accumulate the buffered text.
    text_buffer.clear()

    if not text:
        return []

    text_id = str(uuid.uuid4())
    return [
        ParserEvent(type="text", mode="create", id=text_id, is_tool_call=False),
        ParserEvent(
            type="text",
            mode="append",
            id=text_id,
            content=text,
            is_tool_call=False,
        ),
        ParserEvent(type="text", mode="close", id=text_id, is_tool_call=False),
    ]
