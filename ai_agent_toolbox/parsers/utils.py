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


def longest_prefix_at_end(buffer: str, full_str: str, *, allow_full_match: bool = False) -> int:
    """Return the length of the longest suffix of ``buffer`` that matches a
    prefix of ``full_str``.

    This helper is used by streaming parsers to detect when an incoming chunk
    ends with a *partial* sentinel (e.g., the start of a Markdown fence or XML
    tag) so that the parser can retain the incomplete fragment for the next
    chunk instead of emitting it as plain text.

    Args:
        buffer: The current accumulated text.
        full_str: The string to match against (such as an opening/closing tag).
        allow_full_match: Whether a complete match of ``full_str`` should be
            reported. Parsers typically only care about partial matches, so the
            default is ``False``.

    Returns:
        The length of the matching suffix/prefix overlap. ``0`` indicates that
        no overlap was found.
    """

    if not full_str:
        return 0

    if allow_full_match:
        max_len = min(len(buffer), len(full_str))
    else:
        max_len = min(len(buffer), max(len(full_str) - 1, 0))

    if max_len <= 0:
        return 0

    for length in range(max_len, 0, -1):
        if buffer.endswith(full_str[:length]):
            return length
    return 0
