import uuid
from typing import List, Optional

from .tool_parser import ToolParser, ToolParserState
from ai_agent_toolbox.parser_event import ParserEvent

class ParserState:
    """
    Enumeration for the XMLParser's top-level states.
    """
    OUTSIDE = "outside"
    INSIDE_TOOL = "inside_tool"

class XMLParser:
    """
    The XMLParser only handles text outside any <use_tool> block. It accumulates
    text until it encounters a <use_tool>, then delegates parsing to ToolParser
    until it sees </use_tool>.
    """

    def __init__(self, tag="tool"):
        self.state = ParserState.OUTSIDE
        self.events: List[ParserEvent] = []

        self.current_text_id: Optional[str] = None
        self.outside_buffer: str = ""
        self.tool_parser = ToolParser(tag=tag)

    def parse(self, text: str) -> List[ParserEvent]:
        return self.parse_chunk(text) + self.flush()

    def parse_chunk(self, chunk: str) -> List[ParserEvent]:
        """
        Parse a chunk of text, returning a list of ParserEvent objects. 
        """
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
            use_idx = combined.find("<use_tool>")
            if use_idx == -1:
                # No complete <use_tool> in `combined`.
                partial_prefix = self._partial_prefix(combined, "<use_tool>")
                if partial_prefix:
                    # Emit everything except that partial prefix as text
                    text_before_partial = combined[:-len(partial_prefix)]
                    self._stream_outside_text(text_before_partial)
                    # Keep the partial prefix for next parse call
                    self.outside_buffer = partial_prefix
                else:
                    # No partial prefix => all is outside text
                    self._stream_outside_text(combined)
                break

            # We found a <use_tool>; everything before it is outside text
            text_before = combined[:use_idx]
            self._stream_outside_text(text_before)

            # Close the current text block
            self._close_text_block()

            # Advance past <use_tool>, parse the remainder with ToolParser
            combined = combined[use_idx + len("<use_tool>"):]
            new_events, done, leftover = self.tool_parser.parse(combined)
            self.events.extend(new_events)

            if done:
                # ToolParser reached </use_tool>.
                self.tool_parser = None
                self.state = ParserState.OUTSIDE
                combined = leftover
            else:
                # ToolParser needs more data
                self.state = ParserState.INSIDE_TOOL
                self.outside_buffer = leftover
                return

    def _partial_prefix(self, text: str, pattern: str) -> str:
        """
        Returns the longest trailing substring of `text` that is a prefix
        of `pattern`. For instance:
          text="... <us" and pattern="<use_tool>" => returns "<us"
          text="... foo" and pattern="<use_tool>" => returns ""
          text="... <use_to" => returns "<use_to"
        """
        max_len = min(len(text), len(pattern) - 1)
        for size in range(max_len, 0, -1):
            if pattern.startswith(text[-size:]):
                return text[-size:]
        return ""

    def _handle_inside_tool(self, chunk: str):
        if not self.tool_parser:
            return

        new_events, done, leftover = self.tool_parser.parse(chunk)
        self.events.extend(new_events)

        if done:
            self.tool_parser = None
            self.state = ParserState.OUTSIDE
            self._handle_outside(leftover)
        else:
            self.outside_buffer = leftover

    def _stream_outside_text(self, text: str):
        """
        Convert raw text into a series of ParserEvent objects marking its creation
        and content. We continue appending to the same text block until we decide
        to close it.
        """
        if not text:
            return
        self._open_text_block()
        self.events.append(ParserEvent(
            type="text",
            is_tool_call=False,
            mode="append",
            id=self.current_text_id,
            content=text
        ))

    def _open_text_block(self):
        """
        Starts a new text block if there isn't one already open.
        """
        if self.current_text_id is None:
            new_id = str(uuid.uuid4())
            self.current_text_id = new_id
            self.events.append(ParserEvent(
                type="text",
                is_tool_call=False,
                mode="create",
                id=new_id
            ))

    def _close_text_block(self):
        """
        Closes the current text block if one is open.
        """
        if self.current_text_id:
            self.events.append(ParserEvent(
                type="text",
                is_tool_call=False,
                mode="close",
                id=self.current_text_id
            ))
            self.current_text_id = None

    def flush(self) -> List[ParserEvent]:
        """
        Called when no more data remains. This should finalize any open blocks,
        flush any partial text, and close any partially parsed tool calls.
        """
        flush_events: List[ParserEvent] = []

        # If we're outside, flush leftover outside text
        if self.state == ParserState.OUTSIDE and self.outside_buffer.strip():
            self._stream_outside_text(self.outside_buffer)
            self.outside_buffer = ""

        # Close any open outside text block
        if self.current_text_id is not None:
            flush_events.append(ParserEvent(
                type="text",
                is_tool_call=False,
                mode="close",
                id=self.current_text_id
            ))
            self.current_text_id = None

        # If there's a partially open ToolParser, forcibly finalize it
        if self.state == ParserState.INSIDE_TOOL and self.tool_parser:
            events, done, leftover = self.tool_parser.parse("")
            flush_events.extend(events)
            if not done:
                self._finalize_tool_parser(flush_events)
            self.tool_parser = None
            self.state = ParserState.OUTSIDE

            # Any leftover after forcibly closing tool content is outside text
            if leftover.strip():
                self._handle_outside(leftover)
                # If _handle_outside started a new text block, close it
                if self.current_text_id is not None:
                    flush_events.append(ParserEvent(
                        type="text",
                        is_tool_call=False,
                        mode="close",
                        id=self.current_text_id
                    ))
                    self.current_text_id = None

        return flush_events

    def _finalize_tool_parser(self, flush_events: List[ParserEvent]):
        """
        Force any final events from a partially parsed tool block if we couldn't
        properly see its closing tag.
        """
        if self.tool_parser and not self.tool_parser.is_done():
            if self.tool_parser.current_tool_id:
                # If there's an open arg, close it
                if self.tool_parser.current_arg_name is not None:
                    self.tool_parser._close_tool_arg()
                # Emit the tool close
                flush_events.append(ParserEvent(
                    type="tool",
                    is_tool_call=True,
                    mode="close",
                    id=self.tool_parser.current_tool_id
                ))
            self.tool_parser.state = ToolParserState.DONE
