import uuid
from typing import Optional, List, Dict
from ai_agent_toolbox.parser_event import ParserEvent, ToolUse

class ToolParserState:
    WAITING_FOR_NAME = "waiting_for_name"
    HAS_NAME = "has_name"
    DONE = "done"

class ToolParser:
    """
    A parser for a <use_tool>...</use_tool> block that:
      - Extracts the <name>...</name> for a tool
      - Then captures zero or more <argName>...</argName> pairs
      - Concludes when it finds </use_tool>.

    This implementation does NOT use regex. It processes data chunk by chunk,
    storing partial content in self.buffer until enough data arrives to
    continue parsing.

    The parse(...) method returns:
      - a list of ParserEvents
      - a boolean indicating if the tool parsing is done (i.e., we've parsed </use_tool>)
      - leftover text not consumed in this parse
    """

    def __init__(self, tag: str):
        self.state = ToolParserState.WAITING_FOR_NAME
        self.buffer: str = ""
        self.events: List[ParserEvent] = []

        self.tag = tag
        self.end_tag = f"</{tag}>"
        self.start_tag = f"<{tag}>"

        # Current tool info
        self.current_tool_id: Optional[str] = None
        self.current_tool_name: Optional[str] = None
        self.current_arg_name: Optional[str] = None
        self.current_tool_args: Dict[str, str] = {}

    def parse(self, chunk: str) -> (List[ParserEvent], bool, str):
        """
        Parse the incoming chunk of text according to our current state.
        Returns (events, done, leftover).
        """
        self.events = []  # reset each parse call
        self.buffer += chunk

        # Continue parsing until we can no longer make progress
        while True:
            before = len(self.buffer)

            if self.state == ToolParserState.WAITING_FOR_NAME:
                self._parse_waiting_for_name()
            elif self.state == ToolParserState.HAS_NAME:
                self._parse_has_name()
            elif self.state == ToolParserState.DONE:
                break

            after = len(self.buffer)
            # If no progress was made, we stop to wait for more data
            if after == before:
                break

        # If we are DONE, anything left in buffer is leftover
        done = (self.state == ToolParserState.DONE)
        if done and self.buffer:
            leftover = self.buffer
            self.buffer = ""
        else:
            leftover = ""

        return self.events, done, leftover

    def _parse_waiting_for_name(self):
        """
        Look for a complete <name>...</name> block. If not found, do nothing;
        if partially found, keep the partial buffer for the next chunk.
        Once we have the name, move to HAS_NAME state.
        """
        start_tag = "<name>"
        end_tag = "</name>"

        start_idx = self.buffer.find(start_tag)
        if start_idx == -1:
            # Possibly partial or no <name> yet; do nothing.
            return

        close_idx = self.buffer.find(end_tag, start_idx + len(start_tag))
        if close_idx == -1:
            # Not complete yet. Possibly partial.
            return

        # We have a complete <name>...</name>.
        name_text_start = start_idx + len(start_tag)
        name_text = self.buffer[name_text_start:close_idx].strip()

        # Remove this block from the buffer
        end_of_block = close_idx + len(end_tag)
        self.buffer = self.buffer[end_of_block:]

        # Create the tool
        self._create_tool(name_text)
        self.state = ToolParserState.HAS_NAME

    def _parse_has_name(self):
        """
        We have the tool's name. We now look for either:
          - argument tags: <argName>...</argName>
          - the end of the tool: </{self.tag}>
        We'll parse as much as possible. If we cannot find a complete tag, we wait for more data.
        """
        close_pos = self.buffer.find(self.end_tag)
        if close_pos == -1:
            # No tool end tag found; parse arguments from entire buffer
            consumed = self._parse_tool_arguments(self.buffer)
            # Remove consumed portion from buffer
            self.buffer = self.buffer[consumed:]
        else:
            # We found the tool end tag, so parse arguments up to that point
            inside_text = self.buffer[:close_pos]
            consumed = self._parse_tool_arguments(inside_text)
            if consumed == len(inside_text):
                # We fully consumed the inside text => remove end tag as well
                self.buffer = self.buffer[close_pos + len(self.end_tag):]
                self._finalize_tool()
                self.state = ToolParserState.DONE
            else:
                # Partial parse; only consumed `consumed` chars from inside_text
                leftover = inside_text[consumed:]
                # Put back the leftover + the end tag portion
                self.buffer = leftover + self.buffer[close_pos:]

    def _parse_tool_arguments(self, text: str) -> int:
        """
        Parse argument data in `text` and return how many characters we fully consumed.
        Once we see <argName>, we read all text (including nested '<') until </argName>.
        If we see a closing tag </argName>, that ends the current argument.
        We do partial parsing if we don't yet have a closing tag.
        """
        i = 0
        length = len(text)

        while i < length:
            # Look for a '<'
            lt_index = text.find("<", i)
            if lt_index == -1:
                # No more angle brackets -> treat the remainder as text for the current arg
                remainder = text[i:]
                self._append_tool_arg(remainder)
                i = length
                break

            # Up to the next '<' is literal text for the current arg
            if lt_index > i:
                literal = text[i:lt_index]
                self._append_tool_arg(literal)
                i = lt_index

            # Try to parse a full tag <...>
            gt_index = text.find(">", lt_index + 1)
            if gt_index == -1:
                # We have a partial "<..." with no closing '>', so stop here
                break

            # Extract what's inside <...> (strip whitespace)
            full_tag = text[lt_index + 1:gt_index].strip()
            i = gt_index + 1  # move past '>'

            if full_tag.startswith("/"):
                # It's a closing tag, e.g. </content>
                tag_name = full_tag[1:].strip()
                # If it matches the current arg, close it
                if self.current_arg_name == tag_name:
                    self._close_tool_arg()
                else:
                    # Possibly mismatched tag; just close whatever we had open
                    if self.current_arg_name:
                        self._close_tool_arg()
            else:
                # It's an opening tag, e.g. <content>
                arg_name = full_tag

                # If we already had an arg open, close it first
                if self.current_arg_name:
                    self._close_tool_arg()

                # Start a new argument
                self._start_tool_arg(arg_name)

                # Now we want to read everything until we find the matching </arg_name>.
                end_tag = f"</{arg_name}>"
                end_pos = text.find(end_tag, i)
                if end_pos == -1:
                    # We don't yet have the closing tag -> partial parse
                    # Everything from i to the end is argument text
                    inner_text = text[i:]
                    self._append_tool_arg(inner_text)
                    i = length  # done reading this chunk
                    break
                else:
                    # We found the matching closing tag.
                    # Everything from i up to end_pos is the argument content.
                    inner_text = text[i:end_pos]
                    self._append_tool_arg(inner_text)
                    # Now move past `</arg_name>` 
                    i = end_pos + len(end_tag)
                    # And close the argument
                    self._close_tool_arg()

        return i

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
                is_tool_call=False,
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
                    is_tool_call=False,
                    content=text
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
                    )
                )
            )
        self.current_tool_id = None
        self.current_tool_name = None
        self.current_tool_args = {}

    def is_done(self) -> bool:
        return self.state == ToolParserState.DONE
