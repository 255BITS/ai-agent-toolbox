import uuid
from ai_agent_toolbox.parsers.parser import Parser
from ai_agent_toolbox.parser_event import ParserEvent, ToolUse

class MarkdownParser(Parser):
    """
    A streaming parser for Markdown code fences that treats code blocks as tool calls.
    It supports code fences with an optional language identifier (e.g. "```python").
    Everything outside a code fence is treated as plain text.
    """
    STATE_OUTSIDE = "outside"
    STATE_INSIDE = "inside"

    OPEN_FENCE = "```"
    CLOSE_FENCE = "```"

    def __init__(self):
        self.state = self.STATE_OUTSIDE
        self.buffer = ""
        self.outside_text_buffer = []  # Accumulates plain text segments

        # When inside a code fence, we track the tool call.
        self.current_tool_id = None
        self.current_tool_name = None  # from language identifier; default "code"
        self.tool_content_buffer = []

    def parse(self, text: str):
        """Convenience method for one-shot parsing."""
        events = []
        events.extend(self.parse_chunk(text))
        events.extend(self.flush())
        return events

    def parse_chunk(self, chunk: str):
        """Process an incoming chunk of text and emit ParserEvent objects."""
        events = []
        self.buffer += chunk

        while True:
            before = len(self.buffer)
            if self.state == self.STATE_OUTSIDE:
                events.extend(self._parse_outside())
            else:  # STATE_INSIDE
                events.extend(self._parse_inside())
            after = len(self.buffer)
            if after == before:
                break

        return events

    def flush(self):
        """
        Called when no more data is expected. If there is a partially open code fence,
        force-close it. Also flushes any remaining outside text.
        """
        events = []
        # If inside a code fence, force-close the tool block.
        if self.state == self.STATE_INSIDE:
            if self.buffer:
                self.tool_content_buffer.append(self.buffer)
                events.append(ParserEvent(
                    type="tool",
                    mode="append",
                    id=self.current_tool_id,
                    content=self.buffer,
                    is_tool_call=False
                ))
                self.buffer = ""
            full_content = "".join(self.tool_content_buffer)
            events.append(ParserEvent(
                type="tool",
                mode="close",
                id=self.current_tool_id,
                is_tool_call=True,
                tool=ToolUse(name=self.current_tool_name, args={"content": full_content}),
                content=full_content
            ))
            self.current_tool_id = None
            self.current_tool_name = None
            self.tool_content_buffer = []
            self.state = self.STATE_OUTSIDE

        # If outside, flush any leftover text.
        if self.state == self.STATE_OUTSIDE and self.buffer:
            self.outside_text_buffer.append(self.buffer)
            self.buffer = ""
        events.extend(self._flush_outside_text())
        return events

    def _parse_outside(self):
        """
        In the OUTSIDE state, search for the next complete opening code fence.
        If found, flush any preceding text and then transition into INSIDE state.
        """
        events = []
        idx = self.buffer.find(self.OPEN_FENCE)
        if idx == -1:
            # No complete opening fence found. Check if the end of the buffer
            # is a partial fence.
            partial_len = self._longest_prefix_at_end(self.buffer, self.OPEN_FENCE)
            if partial_len:
                if len(self.buffer) > partial_len:
                    self.outside_text_buffer.append(self.buffer[:-partial_len])
                    self.buffer = self.buffer[-partial_len:]
            else:
                self.outside_text_buffer.append(self.buffer)
                self.buffer = ""
            return events

        # Found an opening fence at index idx.
        if idx > 0:
            self.outside_text_buffer.append(self.buffer[:idx])
        events.extend(self._flush_outside_text())

        # Remove the opening fence from the buffer.
        self.buffer = self.buffer[idx + len(self.OPEN_FENCE):]

        # After the fence, there might be an optional language identifier.
        lang = ""
        if self.buffer.startswith("\n"):
            # No language identifier provided.
            self.buffer = self.buffer[1:]
        else:
            newline_idx = self.buffer.find("\n")
            if newline_idx != -1:
                lang = self.buffer[:newline_idx].strip()
                self.buffer = self.buffer[newline_idx+1:]
            else:
                # Incomplete language line; wait for more data.
                return events

        if not lang:
            lang = "code"
        self.current_tool_name = lang
        self.current_tool_id = str(uuid.uuid4())
        self.tool_content_buffer = []
        events.append(ParserEvent(
            type="tool",
            mode="create",
            id=self.current_tool_id,
            is_tool_call=False
        ))
        self.state = self.STATE_INSIDE
        return events

    def _find_closing_fence_index(self, buf: str) -> int:
        """
        Finds the index of a valid closing fence in buf.
        A valid closing fence must appear at the start of a line (or at index 0).
        """
        pos = 0
        while True:
            idx = buf.find(self.CLOSE_FENCE, pos)
            if idx == -1:
                return -1
            # Only consider as a fence if at start of buffer or preceded by a newline.
            if idx == 0 or buf[idx - 1] == "\n":
                return idx
            pos = idx + 1

    def _parse_inside(self):
        """
        In the INSIDE state, search for a closing fence that is at the start of a line.
        Content up to the fence is appended to the current tool call.
        """
        events = []
        idx = self._find_closing_fence_index(self.buffer)
        if idx == -1:
            # No valid closing fence found.
            partial_len = self._longest_prefix_at_end(self.buffer, self.CLOSE_FENCE)
            if partial_len:
                if len(self.buffer) > partial_len:
                    content = self.buffer[:-partial_len]
                    if content:
                        self.tool_content_buffer.append(content)
                        events.append(ParserEvent(
                            type="tool",
                            mode="append",
                            id=self.current_tool_id,
                            content=content,
                            is_tool_call=False
                        ))
                    self.buffer = self.buffer[-partial_len:]
                # Else: only a partial fence exists; wait for more data.
            else:
                if self.buffer:
                    content = self.buffer
                    self.tool_content_buffer.append(content)
                    events.append(ParserEvent(
                        type="tool",
                        mode="append",
                        id=self.current_tool_id,
                        content=content,
                        is_tool_call=False
                    ))
                    self.buffer = ""
            return events

        # Found a valid closing fence.
        content = self.buffer[:idx]
        if content:
            self.tool_content_buffer.append(content)
            events.append(ParserEvent(
                type="tool",
                mode="append",
                id=self.current_tool_id,
                content=content,
                is_tool_call=False
            ))
        full_content = "".join(self.tool_content_buffer)
        events.append(ParserEvent(
            type="tool",
            mode="close",
            id=self.current_tool_id,
            is_tool_call=True,
            tool=ToolUse(name=self.current_tool_name, args={"content": full_content}),
            content=full_content
        ))
        # Remove the closing fence from the buffer.
        self.buffer = self.buffer[idx + len(self.CLOSE_FENCE):]
        if self.buffer.startswith("\n"):
            self.buffer = self.buffer[1:]
        self.current_tool_id = None
        self.current_tool_name = None
        self.tool_content_buffer = []
        self.state = self.STATE_OUTSIDE
        return events

    def _flush_outside_text(self):
        """
        If there is accumulated outside text, emit a full text block as create/append/close.
        """
        events = []
        if self.outside_text_buffer:
            text = "".join(self.outside_text_buffer)
            if text:
                text_id = str(uuid.uuid4())
                events.append(ParserEvent(
                    type="text",
                    mode="create",
                    id=text_id,
                    is_tool_call=False
                ))
                events.append(ParserEvent(
                    type="text",
                    mode="append",
                    id=text_id,
                    content=text,
                    is_tool_call=False
                ))
                events.append(ParserEvent(
                    type="text",
                    mode="close",
                    id=text_id,
                    is_tool_call=False
                ))
            self.outside_text_buffer = []
        return events

    @staticmethod
    def _longest_prefix_at_end(buf: str, full_str: str) -> int:
        """
        Determines if the end of `buf` is a prefix of `full_str`. This is used
        to preserve partial code fences across chunks.
        """
        max_len = min(len(buf), len(full_str) - 1)
        for length in range(max_len, 0, -1):
            if buf.endswith(full_str[:length]):
                return length
        return 0