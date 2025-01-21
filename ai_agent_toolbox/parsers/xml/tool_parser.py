import re
import uuid
from typing import Optional, List, Dict
from ai_agent_toolbox.parser_event import ParserEvent, ToolUse

class ToolParserState:
    WAITING_FOR_NAME = "waiting_for_name"
    HAS_NAME = "has_name"
    DONE = "done"

class ToolParser:
    NAME_BLOCK_REGEX = re.compile(r"<name>(.*?)</name>", flags=re.DOTALL)
    ARG_OPEN_REGEX = re.compile(r"<(\w+)>")
    ARG_CLOSE_REGEX = re.compile(r"</(\w+)>")

    def __init__(self, tag: str):
        self.state = ToolParserState.WAITING_FOR_NAME
        self.buffer: str = ""
        self.events: List[ParserEvent] = []

        self.tag = tag
        self.end_tag = "</" + tag + ">"
        self.start_tag = "<" + tag + ">"

        # Current tool info
        self.current_tool_id: Optional[str] = None
        self.current_tool_name: Optional[str] = None
        self.current_arg_name: Optional[str] = None
        self.current_tool_args: Dict[str, str] = {}

    def parse(self, chunk: str) -> (List[ParserEvent], bool, str):
        self.events = []  # reset each parse
        self.buffer += chunk

        while True:
            before = len(self.buffer)

            if self.state == ToolParserState.WAITING_FOR_NAME:
                self._parse_waiting_for_name()
            elif self.state == ToolParserState.HAS_NAME:
                self._parse_has_name()
            elif self.state == ToolParserState.DONE:
                break

            after = len(self.buffer)
            if after == before:
                break

        done = (self.state == ToolParserState.DONE)
        if done and self.buffer:
            leftover = self.buffer
            self.buffer = ""
        else:
            leftover = ""

        return self.events, done, leftover

    def _parse_waiting_for_name(self):
        match = self.NAME_BLOCK_REGEX.search(self.buffer)
        if not match:
            # Not enough data to extract <name>...</name>
            return

        name_text = match.group(1).strip()
        end_idx = match.end()
        self.buffer = self.buffer[end_idx:]

        self._create_tool(name_text)
        self.state = ToolParserState.HAS_NAME

    def _parse_has_name(self):
        close_pos = self.buffer.find(self.end_tag)
        if close_pos == -1:
            # Possibly partial
            partial_prefix = self._partial_prefix(self.buffer, self.end_tag)
            if partial_prefix:
                text_before_partial = self.buffer[:-len(partial_prefix)]
                self._parse_tool_arguments(text_before_partial)
                self.buffer = partial_prefix
            else:
                self._parse_tool_arguments(self.buffer)
                self.buffer = ""
        else:
            # Found the full </use_tool>
            inside_text = self.buffer[:close_pos]
            self._parse_tool_arguments(inside_text)
            end_of_tag = close_pos + len(self.end_tag)
            self.buffer = self.buffer[end_of_tag:]
            self._finalize_tool()
            self.state = ToolParserState.DONE

    def _parse_tool_arguments(self, text: str):
        current_pos = 0
        length = len(text)

        while current_pos < length:
            lt_index = text.find("<", current_pos)
            if lt_index == -1:
                # No more tags => treat all as argument text
                self._append_tool_arg(text[current_pos:])
                break

            # If there's plain text before the next '<', append it
            if lt_index > current_pos:
                self._append_tool_arg(text[current_pos:lt_index])
                current_pos = lt_index

            # Now see if we have <argName> or </argName>
            maybe_tag = text[current_pos:]
            close_m = self.ARG_CLOSE_REGEX.match(maybe_tag)
            if close_m:
                arg_name = close_m.group(1)
                if self.current_arg_name == arg_name:
                    self._close_tool_arg()
                current_pos += len(close_m.group(0))
                continue

            open_m = self.ARG_OPEN_REGEX.match(maybe_tag)
            if open_m:
                arg_name = open_m.group(1)
                self._start_tool_arg(arg_name)
                current_pos += len(open_m.group(0))
                continue

            # If it's our end tag (</use_tool>), let higher logic handle it
            if maybe_tag.startswith(self.end_tag):
                break

            # Unknown tag => treat "<" literally
            self._append_tool_arg("<")
            current_pos += 1

    def _partial_prefix(self, text: str, pattern: str) -> str:
        max_len = min(len(text), len(pattern) - 1)
        for size in range(max_len, 0, -1):
            if pattern.startswith(text[-size:]):
                return text[-size:]
        return ""

    # --------------------------------------------------------------------------
    # Tool methods
    # --------------------------------------------------------------------------
    def _create_tool(self, name: str):
        if not name:
            raise ValueError("Tool name is required")

        self.current_tool_id = str(uuid.uuid4())
        self.current_tool_name = name
        self.current_tool_args = {}

        # "Create" event
        self.events.append(
            ParserEvent(
                type="tool",
                mode="create",
                id=self.current_tool_id,
                is_tool_call=True,
                content=name
            )
        )

    def _start_tool_arg(self, arg_name: str):
        # Close any prior arg
        self._close_tool_arg()
        self.current_arg_name = arg_name

    def _append_tool_arg(self, text: str):
        if self.current_tool_id and self.current_arg_name and text:
            # Accumulate in our dictionary
            if self.current_arg_name not in self.current_tool_args:
                self.current_tool_args[self.current_arg_name] = text
            else:
                self.current_tool_args[self.current_arg_name] += text

            # Also emit an append event showing the partial chunk
            self.events.append(
                ParserEvent(
                    type="tool",
                    mode="append",
                    id=self.current_tool_id,
                    is_tool_call=True,
                    content=text,
                    args={self.current_arg_name: text}
                )
            )

    def _close_tool_arg(self):
        self.current_arg_name = None

    def _finalize_tool(self):
        """Emit a close event with the final tool usage."""
        self._close_tool_arg()
        if self.current_tool_id:
            self.events.append(
                ParserEvent(
                    type="tool",
                    mode="close",
                    id=self.current_tool_id,
                    is_tool_call=True,
                    tool=ToolUse(
                        name=self.current_tool_name,
                        args=self.current_tool_args.copy()
                    ),
                    # Also store the args dict at the top level for easy testing:
                    args=self.current_tool_args.copy()
                )
            )
        self.current_tool_id = None
        self.current_tool_name = None
        self.current_tool_args = {}

    def is_done(self) -> bool:
        return self.state == ToolParserState.DONE
