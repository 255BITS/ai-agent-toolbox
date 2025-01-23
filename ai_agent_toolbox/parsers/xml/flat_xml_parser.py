import uuid
from ai_agent_toolbox.parser_event import ParserEvent, ToolUse
from ai_agent_toolbox.parsers import Parser

class FlatXMLParser(Parser):
    """
    A simple, flat parser that scans for one or more specific XML-style tags
    (e.g. <think>...</think>, <action>...</action>) within a stream of text,
    and emits ParserEvent objects (text/tool, create/append/close).

    It supports streaming partial chunks of text:
      - If a recognized open tag is partially in one chunk and finishes in the next,
        we wait until the tag is complete to start tool events.
      - Similarly for closing tags.
      - Unknown tags are treated as literal text.

    No nesting is handled. We assume "flat" usage: <tag>some content</tag>.
    """

    STATE_OUTSIDE = "outside"
    STATE_INSIDE = "inside"

    def __init__(self, *tags):
        """
        :param tags: the tags (strings) you want to capture, e.g. "think", "action"
        """
        self.tags = list(tags)

        # Streaming state
        self._state = self.STATE_OUTSIDE
        self._buffer = ""  # Accumulate incoming text across parse_chunk calls

        # For outside text
        self._outside_text_id = None
        self._outside_text_buffer = []

        # For inside a recognized tag
        self._current_tag_name = None
        self._tool_id = None
        self._tool_content_buffer = []

    def parse(self, text: str):
        """
        Convenience method for parsing all text at once.
        Returns all events in a single list (non-streaming usage).
        """
        events = []
        events.extend(self.parse_chunk(text))
        events.extend(self.flush())
        return events

    def parse_chunk(self, chunk: str):
        """
        Consume `chunk` in a streaming-friendly way.
        Returns a list of ParserEvent objects that can be appended to a running log.
        """
        events = []
        self._buffer += chunk

        # Keep parsing as long as we can find something to do.
        while True:
            before = len(self._buffer)
            if self._state == self.STATE_OUTSIDE:
                events.extend(self._parse_outside())
            else:  # self._state == self.STATE_INSIDE
                events.extend(self._parse_inside())

            # If no progress was made, break to await more data
            after = len(self._buffer)
            if after == before:
                break

        return events

    def flush(self):
        """
        Called when no more data is expected.
        - If we have leftover outside text, emit it.
        - If we are inside a recognized tag but never closed it, force-close it.
        """
        events = []

        # If we are inside a recognized tag, forcibly close it
        if self._state == self.STATE_INSIDE:
            # Everything left in _buffer is part of the recognized tag content
            self._tool_content_buffer.append(self._buffer)
            self._buffer = ""

            # We do NOT emit another "append" event here for _tool_content_buffer,
            # because parse_chunk() has already appended partial contents for us.
            # Just close the tag with the full content we have.
            events.append(
                ParserEvent(
                    type="tool",
                    mode="close",
                    id=self._tool_id,
                    is_tool_call=True,
                    tool=ToolUse(
                        name=self._current_tag_name,
                        args={"content": "".join(self._tool_content_buffer)}
                    ),
                    content="".join(self._tool_content_buffer)
                )
            )

            # Reset
            self._tool_id = None
            self._current_tag_name = None
            self._tool_content_buffer = []
            self._state = self.STATE_OUTSIDE
            # Now we'll handle any leftover in _buffer (if any) as outside text.

        # If there's leftover text in the buffer while outside, treat it as text
        if self._state == self.STATE_OUTSIDE and self._buffer.strip():
            self._outside_text_buffer.append(self._buffer)
            self._buffer = ""

        # Flush any accumulated outside text
        events.extend(self._flush_outside_text())

        # Clear buffer entirely, no partial prefix to keep anymore
        self._buffer = ""
        return events

    #
    # Internal Helpers
    #
    def _parse_outside(self):
        """
        We are outside of a recognized tag. Look for the earliest recognized open tag <tag>.
        If found:
          - everything before that becomes text events
          - we open the tool (create) event
          - remove the open tag from buffer
          - switch to inside state
        If not found or only partially found, we do as much as possible and return.
        """
        events = []

        # Attempt to find the earliest open tag among recognized tags
        first_open_idx = None
        first_tag_name = None
        for t in self.tags:
            ot = f"<{t}>"
            idx = self._buffer.find(ot)
            if idx != -1:
                if first_open_idx is None or idx < first_open_idx:
                    first_open_idx = idx
                    first_tag_name = t

        if first_open_idx is None:
            # No recognized open tag found
            partial_len = self._longest_tag_prefix_at_end(self._buffer, self.tags)
            if partial_len == 0:
                # No partial prefix. Everything is pure text. We can flush it out
                self._outside_text_buffer.append(self._buffer)
                self._buffer = ""
            else:
                # We keep that partial prefix in _buffer for next chunk
                # Move everything except that partial prefix to text
                cut_point = len(self._buffer) - partial_len
                if cut_point > 0:
                    self._outside_text_buffer.append(self._buffer[:cut_point])
                self._buffer = self._buffer[cut_point:]
            return events

        # Found a recognized tag <first_tag_name> at first_open_idx
        outside_part = self._buffer[:first_open_idx]
        if outside_part:
            self._outside_text_buffer.append(outside_part)

        # Flush the outside text now that we are about to enter a recognized tag
        events.extend(self._flush_outside_text())

        # Remove the open tag from the buffer
        open_tag_str = f"<{first_tag_name}>"
        self._buffer = self._buffer[first_open_idx + len(open_tag_str):]

        # Emit tool create
        self._current_tag_name = first_tag_name
        self._tool_id = str(uuid.uuid4())
        self._tool_content_buffer = []
        events.append(
            ParserEvent(
                type="tool",
                mode="create",
                id=self._tool_id,
                is_tool_call=False
            )
        )

        # Switch state
        self._state = self.STATE_INSIDE
        return events

    def _parse_inside(self):
        """
        We are inside a recognized tag (self._current_tag_name).
        Look for its close tag </tag>. If found, yield the full content,
        then close. Otherwise, store partial content and wait.
        """
        events = []

        if not self._current_tag_name:
            # If we have no current tag name, do nothing
            return events

        close_tag = f"</{self._current_tag_name}>"
        close_idx = self._buffer.find(close_tag)
        if close_idx == -1:
            # Possibly partial close tag or no close tag yet
            partial_len = self._longest_prefix_at_end(self._buffer, close_tag)
            if partial_len == 0:
                # No partial prefix, so the entire buffer is content
                if self._buffer:
                    chunk = self._buffer
                    self._tool_content_buffer.append(chunk)
                    events.append(
                        ParserEvent(
                            type="tool",
                            mode="append",
                            id=self._tool_id,
                            content=chunk,
                            is_tool_call=False
                        )
                    )
                self._buffer = ""
            else:
                # Keep that partial prefix in the buffer, remove the rest as content
                cut_point = len(self._buffer) - partial_len
                if cut_point > 0:
                    chunk = self._buffer[:cut_point]
                    self._tool_content_buffer.append(chunk)
                    events.append(
                        ParserEvent(
                            type="tool",
                            mode="append",
                            id=self._tool_id,
                            content=chunk,
                            is_tool_call=False
                        )
                    )
                self._buffer = self._buffer[cut_point:]
            return events

        # We found the close tag
        inside_content = self._buffer[:close_idx]
        if inside_content:
            self._tool_content_buffer.append(inside_content)
            events.append(
                ParserEvent(
                    type="tool",
                    mode="append",
                    id=self._tool_id,
                    content=inside_content,
                    is_tool_call=False
                )
            )

        # Now close the tool
        events.append(
            ParserEvent(
                type="tool",
                mode="close",
                id=self._tool_id,
                is_tool_call=True,
                tool=ToolUse(name=self._current_tag_name, args={"content": "".join(self._tool_content_buffer)}),
                content="".join(self._tool_content_buffer)
            )
        )

        # Remove the close tag from buffer
        self._buffer = self._buffer[close_idx + len(close_tag):]

        # Reset
        self._tool_id = None
        self._current_tag_name = None
        self._tool_content_buffer = []
        self._state = self.STATE_OUTSIDE

        return events

    def _flush_outside_text(self):
        """
        Closes out a block of outside text, emitting create/append/close if there's content.
        """
        events = []
        if not self._outside_text_buffer:
            return events
        full_text = "".join(self._outside_text_buffer)
        if not full_text:
            self._outside_text_buffer = []
            return events

        text_id = str(uuid.uuid4())
        events.append(
            ParserEvent(
                type="text",
                mode="create",
                id=text_id,
                is_tool_call=False
            )
        )
        events.append(
            ParserEvent(
                type="text",
                mode="append",
                id=text_id,
                content=full_text,
                is_tool_call=False
            )
        )
        events.append(
            ParserEvent(
                type="text",
                mode="close",
                id=text_id,
                is_tool_call=False
            )
        )
        self._outside_text_buffer = []
        return events

    @staticmethod
    def _longest_tag_prefix_at_end(buf: str, tags) -> int:
        """
        Check if the end of buf is a prefix of any recognized <tag> string.
        Return the length of the largest matching prefix (which can be up to len(<tag>)-1).
        E.g. if tags=["think"], and buf ends with "<thi", we return 4 because "<thi" is
        a prefix of "<think>".
        """
        longest = 0
        for t in tags:
            open_tag = f"<{t}>"
            prefix_len = FlatXMLParser._longest_prefix_at_end(buf, open_tag)
            if prefix_len > longest:
                longest = prefix_len
        return longest

    @staticmethod
    def _longest_prefix_at_end(buf: str, full_str: str) -> int:
        """
        If the end of `buf` matches a prefix of `full_str` of length L,
        return L. Otherwise 0. E.g. if buf ends with "<thi" and full_str is "<think>",
        return 4.
        """
        max_len = min(len(buf), len(full_str) - 1)
        # We never consider a full match as "partial prefix"—that’s an actual find.
        # So we only check up to len(full_str) - 1
        for length in range(max_len, 0, -1):
            if buf.endswith(full_str[:length]):
                return length
        return 0