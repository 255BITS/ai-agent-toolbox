"""Utility helpers shared by parser implementations."""

from __future__ import annotations

import uuid
from typing import Callable, List, Optional
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


class TextEventStream:
    """Helper that manages streaming text events into an event sequence.

    The class centralizes the common logic shared by parsers that emit text
    events interleaved with other parser events. It tracks the current text
    block identifier, lazily opens a block on demand, and ensures the expected
    ``create``/``append``/``close`` sequence is emitted.
    """

    def __init__(self, emit_event: Callable[[ParserEvent], None]):
        """Create a :class:`TextEventStream`.

        Args:
            emit_event: A callable used to emit :class:`ParserEvent` objects.
                The callable is invoked every time the helper needs to emit an
                event, allowing the owning parser to control how events are
                collected.
        """

        self._emit_event = emit_event
        self._current_text_id: Optional[str] = None

    @property
    def current_text_id(self) -> Optional[str]:
        """Return the identifier for the currently open text block, if any."""

        return self._current_text_id

    def stream(self, text: str) -> None:
        """Append text to the active text block, creating one if needed."""

        if not text:
            return
        self.open()
        self._emit_event(
            ParserEvent(
                type="text",
                mode="append",
                id=self._current_text_id,
                is_tool_call=False,
                content=text,
            )
        )

    def open(self) -> None:
        """Emit a ``create`` event if no text block is currently open."""

        if self._current_text_id is not None:
            return
        text_id = str(uuid.uuid4())
        self._current_text_id = text_id
        self._emit_event(
            ParserEvent(type="text", mode="create", id=text_id, is_tool_call=False)
        )

    def close(self) -> None:
        """Emit a ``close`` event for the active text block, if present."""

        if self._current_text_id is None:
            return
        self._emit_event(
            ParserEvent(
                type="text",
                mode="close",
                id=self._current_text_id,
                is_tool_call=False,
            )
        )
        self._current_text_id = None
