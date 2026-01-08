from __future__ import annotations

from typing import List

from ai_agent_toolbox.tool_parser import ToolParser
from ai_agent_toolbox.tool_parser_state import ToolParserState
from ai_agent_toolbox.parser import Parser
from ai_agent_toolbox.parser_event import ParserEvent
from ai_agent_toolbox.tool_use import ToolUse
from ai_agent_toolbox.parser_utils import TextEventStream


class XMLParser(Parser):
    """
    Accumulates text until <use_tool>, then delegates to ToolParser.
    Once we detect <use_tool>, we shift into INSIDE_TOOL state and feed
    chunks to our ToolParser until it signals completion or we run out of data.
    """

    def __init__(self, tag: str = "tool") -> None:
        self._inside_tool: bool = False
        self.events: List[ParserEvent] = []
        self.text_stream: TextEventStream = TextEventStream(
            lambda event: self.events.append(event)
        )
        self.outside_buffer: str = ""
        self.tool_parser = ToolParser(tag=tag)

        # We define the strings for scanning the outside buffer.
        self.tag = tag
        self.start_tag = f"<{tag}>"

    def parse_chunk(self, chunk: str) -> List[ParserEvent]:
        self.events = []
        if self._inside_tool:
            self._handle_inside_tool(chunk)
        else:
            self._handle_outside(chunk)
        return self.events

    def _handle_outside(self, chunk: str) -> None:
        combined = self.outside_buffer + chunk
        self.outside_buffer = ""

        while True:
            use_idx = combined.find(self.start_tag)
            if use_idx == -1:
                # No <use_tool> found
                partial_prefix = self._partial_prefix(combined, self.start_tag)
                if partial_prefix:
                    # There's a partial match at the end of combined 
                    text_before_partial = combined[:-len(partial_prefix)]
                    self._stream_outside_text(text_before_partial)
                    self.outside_buffer = partial_prefix
                else:
                    # No partial match, all is just outside text
                    self._stream_outside_text(combined)
                break

            # We found <use_tool>. Everything before that is outside text
            text_before = combined[:use_idx]
            self._stream_outside_text(text_before)
            self._close_text_block()

            # Prepare to feed the rest into the tool parser
            combined = combined[use_idx + len(self.start_tag):]
            new_events, done, leftover = self.tool_parser.parse(combined)
            self.events.extend(new_events)

            if done:
                # Tool parser done, reset and remain outside
                self.tool_parser = ToolParser(tag=self.tag)
                self._inside_tool = False
                combined = leftover
            else:
                # Partial tool block, switch to inside state
                self._inside_tool = True
                self.outside_buffer = leftover
                return

    def _handle_inside_tool(self, chunk: str) -> None:
        new_events, done, leftover = self.tool_parser.parse(chunk)
        self.events.extend(new_events)

        if done:
            # Tool done, revert to outside and process leftover
            self.tool_parser = ToolParser(tag=self.tag)
            self._inside_tool = False
            self._handle_outside(leftover)
        else:
            # Still not done, accumulate leftover for the next chunk
            self.outside_buffer = leftover

    @staticmethod
    def _partial_prefix(text: str, pattern: str) -> str:
        """Return suffix of text that is a prefix of pattern."""
        max_len = min(len(text), len(pattern) - 1)
        for size in range(max_len, 0, -1):
            if text.endswith(pattern[:size]):
                return pattern[:size]
        return ""

    def _stream_outside_text(self, text: str) -> None:
        self.text_stream.stream(text)

    def _open_text_block(self) -> None:
        self.text_stream.open()

    def _close_text_block(self) -> None:
        self.text_stream.close()

    def flush(self) -> List[ParserEvent]:
        """
        Called when no more data is expected.
        Closes any open text block or partial tool parse.
        """
        flush_events: List[ParserEvent] = []

        previous_events = self.events
        self.events = flush_events

        try:
            # Flush leftover outside text
            if not self._inside_tool and self.outside_buffer.strip():
                self._stream_outside_text(self.outside_buffer)
                self.outside_buffer = ""

            self._close_text_block()

            # Handle partial tool parse
            if self._inside_tool:
                events, done, leftover = self.tool_parser.parse("")
                flush_events.extend(events)
                if not done:
                    if not self.tool_parser.current_tool_id:
                        self._open_text_block()
                    else:
                        self._finalize_tool_parser(flush_events)
                self.tool_parser = ToolParser(tag=self.tag)
                self._inside_tool = False

                if leftover.strip():
                    self._handle_outside(leftover)
                    self._close_text_block()

            return flush_events
        finally:
            self.events = previous_events

    def _finalize_tool_parser(self, flush_events: List[ParserEvent]) -> None:
        # Force-close partial tool usage if it's not fully done
        if self.tool_parser and not self.tool_parser.is_done():
            # Manually finalize
            if self.tool_parser.current_tool_id:
                # If there's an open arg, close it
                if self.tool_parser.current_arg_name is not None:
                    self.tool_parser._close_tool_arg()
                # Emit the final close
                flush_events.append(
                    ParserEvent(
                        type="tool",
                        is_tool_call=True,
                        mode="close",
                        id=self.tool_parser.current_tool_id,
                        tool=ToolUse(
                            name=self.tool_parser.current_tool_name or "",
                            args=self.tool_parser.current_tool_args.copy()
                        ),
                    )
                )
            self.tool_parser.state = ToolParserState.DONE
