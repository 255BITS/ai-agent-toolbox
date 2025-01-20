import re
import uuid
from typing import Optional, List
from ai_agent_toolbox.parser_event import ParserEvent

class ToolParserState:
    """
    Enumeration for parsing states within <tag> content.
    """
    WAITING_FOR_NAME = "waiting_for_name"
    HAS_NAME = "has_name"
    DONE = "done"

class ToolParser:
    """
    Dedicated parser for <tag>...</tag> blocks. It:
      - Grabs the <name>...</name> to identify which tool is invoked
      - Handles arbitrary <argName>...</argName> tags
      - Stops after </tag> is found, returning leftover text
    """

    NAME_BLOCK_REGEX = re.compile(r"<name>(.*?)</name>", flags=re.DOTALL)
    ARG_OPEN_REGEX = re.compile(r"<(\w+)>")
    ARG_CLOSE_REGEX = re.compile(r"</(\w+)>")

    def __init__(self, tag: str):
        self.state = ToolParserState.WAITING_FOR_NAME

        # Buffer to accumulate everything that belongs inside this single <tag> block
        self.buffer: str = ""
        self.events: List[ParserEvent] = []

        # Current tool info
        self.current_tool_id: Optional[str] = None
        self.current_tool_name: Optional[str] = None
        self.current_arg_name: Optional[str] = None

        self.tag = tag
        self.end_tag = "</" + tag + ">"
        self.start_tag = "<" + tag + ">"

    def parse(self, chunk: str) -> (List[ParserEvent], bool, str):
        """
        Parse incoming chunk for a single <tag> block.
        Returns (events, done, leftover):
          - events: newly generated ParserEvent objects
          - done: True if we found </tag> and finalized
          - leftover: text after </tag>, which belongs outside this tool
        """
        self.events = []  # reset for each parse call
        self.buffer += chunk

        while True:
            before = len(self.buffer)

            if self.state == ToolParserState.WAITING_FOR_NAME:
                self._parse_waiting_for_name()
            elif self.state == ToolParserState.HAS_NAME:
                self._parse_has_name()
            elif self.state == ToolParserState.DONE:
                # Once done, we don't parse further in this parser.
                break

            after = len(self.buffer)
            if after == before:
                # No progress => partial data or nothing left to parse
                break

        done = (self.state == ToolParserState.DONE)

        # If we’re done, everything left in self.buffer is *outside* text
        if done and self.buffer:
            leftover = self.buffer
            self.buffer = ""
        else:
            leftover = ""

        return self.events, done, leftover

    # --------------------------------------------------------------------------
    # State: WAITING_FOR_NAME
    # --------------------------------------------------------------------------
    def _parse_waiting_for_name(self):
        """
        Look for a complete <name>...</name> block. If found, create the tool.
        Otherwise, wait for more data.
        """
        match = self.NAME_BLOCK_REGEX.search(self.buffer)
        if not match:
            return  # partial data, no full <name> block yet

        # Extract the tool name
        name_text = match.group(1).strip()

        # Discard everything up through </name>
        end_idx = match.end()
        self.buffer = self.buffer[end_idx:]

        self._create_tool(name_text)
        self.state = ToolParserState.HAS_NAME

    # --------------------------------------------------------------------------
    # State: HAS_NAME
    # --------------------------------------------------------------------------
    def _parse_has_name(self):
        """
        We have a tool. Now look for arguments or the </tag> close tag.
        If we see partial </tag> (like '</us'), store it in the buffer.
        """
        close_pos = self.buffer.find(self.end_tag)
        if close_pos == -1:
            # Check if we have a partial prefix of </tag>
            partial_prefix = self._partial_prefix(self.buffer, self.end_tag)
            if partial_prefix:
                # Everything before that partial prefix is valid tool-arg text
                text_before_partial = self.buffer[:-len(partial_prefix)]
                self._parse_tool_arguments(text_before_partial)
                # Keep the partial prefix; wait for more data
                self.buffer = partial_prefix
            else:
                # No sign of </tag> => treat entire buffer as arg text
                self._parse_tool_arguments(self.buffer)
                self.buffer = ""
        else:
            # We found a full </tag>
            inside_text = self.buffer[:close_pos]
            self._parse_tool_arguments(inside_text)

            # Remove the </tag> tag
            end_of_tag = close_pos + len(self.end_tag)
            self.buffer = self.buffer[end_of_tag:]

            # Finalize
            self._finalize_tool()
            self.state = ToolParserState.DONE

    def _parse_tool_arguments(self, text: str):
        """
        Parse argument data in `text`. We'll look for <argName>...</argName> pairs,
        or treat untagged content as literal argument text if inside an arg.
        """
        current_pos = 0
        length = len(text)

        while current_pos < length:
            lt_index = text.find("<", current_pos)
            if lt_index == -1:
                # No more '<' => all remainder is argument text
                self._append_tool_arg(text[current_pos:])
                break

            # If there's non-tag text before this '<', treat it as argument text
            if lt_index > current_pos:
                self._append_tool_arg(text[current_pos:lt_index])
                current_pos = lt_index

            # Now examine the tag
            maybe_tag = text[current_pos:]
            close_m = self.ARG_CLOSE_REGEX.match(maybe_tag)
            if close_m:
                # e.g. </argName>
                arg_name = close_m.group(1)
                if self.current_arg_name == arg_name:
                    self._close_tool_arg()
                current_pos += len(close_m.group(0))
                continue

            open_m = self.ARG_OPEN_REGEX.match(maybe_tag)
            if open_m:
                # e.g. <argName>
                arg_name = open_m.group(1)
                self._start_tool_arg(arg_name)
                current_pos += len(open_m.group(0))
                continue

            # If it's </tag>, we ignore it here, _parse_has_name handles it
            if maybe_tag.startswith("</tag>"):
                break

            # Unknown tag => treat the first '<' as literal
            self._append_tool_arg("<")
            current_pos += 1

    # --------------------------------------------------------------------------
    # Partial prefix helper
    # --------------------------------------------------------------------------
    def _partial_prefix(self, text: str, pattern: str) -> str:
        """
        Returns the longest trailing substring of `text` that is a prefix
        of `pattern`. For instance:
          text="...</us" and pattern="</tag>" => returns "</us"
          text="...</use_to" => returns "</use_to"
        """
        max_len = min(len(text), len(pattern) - 1)
        for size in range(max_len, 0, -1):
            if pattern.startswith(text[-size:]):
                return text[-size:]
        return ""

    # --------------------------------------------------------------------------
    # Tool methods
    # --------------------------------------------------------------------------
    def _create_tool(self, name: str):
        self.current_tool_id = str(uuid.uuid4())
        self.current_tool_name = name
        self.events.append(ParserEvent(
            type="tool",
            is_tool_call=True,
            mode="create",
            id=self.current_tool_id,
            content=name
        ))

    def _start_tool_arg(self, arg_name: str):
        """Open a new argument, closing any previous one."""
        self._close_tool_arg()
        self.current_arg_name = arg_name

    def _append_tool_arg(self, text: str):
        """Emit partial argument text for the currently open arg (if any)."""
        if self.current_tool_id and self.current_arg_name and text:
            # Combine arg name + text into the content field.
            content_str = f"[{self.current_arg_name}] {text}"
            self.events.append(ParserEvent(
                type="tool",
                is_tool_call=True,
                mode="append",
                id=self.current_tool_id,
                content=content_str
            ))

    def _close_tool_arg(self):
        """Close the currently open arg."""
        self.current_arg_name = None

    def _finalize_tool(self):
        """Emit a close event and reset tool state."""
        self._close_tool_arg()
        if self.current_tool_id:
            self.events.append(ParserEvent(
                type="tool",
                is_tool_call=True,
                mode="close",
                id=self.current_tool_id
            ))
        self.current_tool_id = None
        self.current_tool_name = None

    def is_done(self) -> bool:
        """True if we've encountered </tag>."""
        return self.state == ToolParserState.DONE
