from typing import List

from .tool_parser import ToolParser
from .tool_parser_state import ToolParserState
from ai_agent_toolbox.parsers import Parser
from ai_agent_toolbox.parser_event import ParserEvent
from ai_agent_toolbox.tool_use import ToolUse
from ai_agent_toolbox.parsers.utils import TextEventStream

class ParserState:
    OUTSIDE = "outside"
    INSIDE_TOOL = "inside_tool"

class XMLParser(Parser):
    """
    Accumulates text until <use_tool>, then delegates to ToolParser.
    Once we detect <use_tool>, we shift into INSIDE_TOOL state and feed 
    chunks to our ToolParser until it signals completion or we run out of data.
    """

    def __init__(self, tag="tool"):
        self.state = ParserState.OUTSIDE
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

        if self.state == ParserState.OUTSIDE:
            self._handle_outside(chunk)
        elif self.state == ParserState.INSIDE_TOOL:
            self._handle_inside_tool(chunk)

        return self.events

    def _handle_outside(self, chunk: str):
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
                # If the tool parser is done, we reset it and remain OUTSIDE
                self.tool_parser = ToolParser(tag=self.tag)
                self.state = ParserState.OUTSIDE
                combined = leftover
            else:
                # If the tool parser isn't done, it means we have a partial tool block
                self.state = ParserState.INSIDE_TOOL
                self.outside_buffer = leftover
                return

    def _handle_inside_tool(self, chunk: str):
        # We are in the middle of a tool parse
        if not self.tool_parser:
            return

        new_events, done, leftover = self.tool_parser.parse(chunk)
        self.events.extend(new_events)

        if done:
            # Tool is done, revert to OUTSIDE
            self.tool_parser = ToolParser(tag=self.tag)
            self.state = ParserState.OUTSIDE
            # The leftover might contain more outside text or new tools
            self._handle_outside(leftover)
        else:
            # Still not done, accumulate leftover for the next chunk
            self.outside_buffer = leftover

    def _partial_prefix(self, text: str, pattern: str) -> str:
        """
        Check if the end of 'text' is a prefix of 'pattern'.
        E.g. if text ends with "<us" and pattern is "<use_tool>", 
        we return "<us" to keep it in buffer as a partial match.
        """
        max_len = min(len(text), len(pattern) - 1)
        for size in range(max_len, 0, -1):
            if pattern.startswith(text[-size:]):
                return text[-size:]
        return ""

    def _stream_outside_text(self, text: str):
        self.text_stream.stream(text)

    def _open_text_block(self):
        self.text_stream.open()

    def _close_text_block(self):
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
            # If we are outside the tool and have leftover text
            if self.state == ParserState.OUTSIDE and self.outside_buffer.strip():
                self._stream_outside_text(self.outside_buffer)
                self.outside_buffer = ""

            # Close any open text block
            self._close_text_block()

            # If we are in the middle of a tool parse
            if self.state == ParserState.INSIDE_TOOL:
                events, done, leftover = self.tool_parser.parse("")
                flush_events.extend(events)
                if not done:
                    # If no valid tool was created (i.e. no <name> found), discard the tool block
                    if not self.tool_parser.current_tool_id:
                        # Open a new text block to resume normal parsing; do not emit any tool events.
                        self._open_text_block()
                    else:
                        self._finalize_tool_parser(flush_events)
                self.tool_parser = ToolParser(tag=self.tag)
                self.state = ParserState.OUTSIDE

                # If leftover text remains after closing the tool, handle it
                if leftover.strip():
                    self._handle_outside(leftover)
                    self._close_text_block()

            return flush_events
        finally:
            self.events = previous_events

    def _finalize_tool_parser(self, flush_events: List[ParserEvent]):
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
