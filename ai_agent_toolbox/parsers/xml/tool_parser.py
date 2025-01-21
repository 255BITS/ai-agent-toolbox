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

        # 1. Find <name>
        start_idx = self.buffer.find(start_tag)
        if start_idx == -1:
            # Possibly partial or no <name> present yet
            # See if there's a partial prefix that might match <name> eventually
            partial = self._partial_prefix(self.buffer, start_tag)
            # We do not discard anything yet; wait for more data
            return

        # 2. Find </name> after that
        close_idx = self.buffer.find(end_tag, start_idx + len(start_tag))
        if close_idx == -1:
            # Not complete yet. Possibly partial.
            partial = self._partial_prefix(self.buffer[start_idx:], end_tag)
            return

        # If we got here, we have a complete <name>...</name>.
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
        # See if we can find the tool's end tag
        close_pos = self.buffer.find(self.end_tag)
        if close_pos == -1:
            # No complete end tag found yet. We'll parse what we can of arguments.
            # Attempt to parse arguments from the entire buffer or partial.
            self._parse_tool_arguments(self.buffer)
            # after parse_tool_arguments, we keep the entire buffer if partial
            # so just return now (we only remove fully parsed text inside that method).
            return
        else:
            # We found the end tag. Everything before that belongs to argument content.
            inside_text = self.buffer[:close_pos]
            self._parse_tool_arguments(inside_text)
            # Now remove the end tag from the buffer
            end_of_tag = close_pos + len(self.end_tag)
            self.buffer = self.buffer[end_of_tag:]
            # Finalize
            self._finalize_tool()
            self.state = ToolParserState.DONE

    def _parse_tool_arguments(self, text: str):
        """
        Parse argument data in `text`. We'll look for <argName>...</argName> pairs,
        or treat untagged content as literal argument text if inside an arg.
        We stop when we can't parse further (partial).
        
        This function does NOT remove from self.buffer itself; it processes `text`
        and decides how many characters were fully parsed. For partially parsed 
        tags, it leaves them in the parser's buffer for the next round.
        """
        i = 0
        length = len(text)

        while i < length:
            lt_index = text.find("<", i)
            if lt_index == -1:
                # No more '<' => remainder is argument text
                remainder = text[i:]
                self._append_tool_arg(remainder)
                i = length
                break

            # The chunk up to the next '<' is literal text for the current arg
            if lt_index > i:
                literal = text[i:lt_index]
                self._append_tool_arg(literal)
                i = lt_index

            # Attempt to parse a full tag. We need a '>' to complete it.
            gt_index = text.find(">", lt_index + 1)
            if gt_index == -1:
                # We have a partial tag "<something" with no closing '>' yet.
                # We'll wait for more data. Nothing is consumed from self.buffer.
                break

            # We have a complete tag from lt_index..gt_index
            full_tag = text[lt_index + 1:gt_index].strip()  # what's inside < ... >
            i = gt_index + 1  # advance past '>'
            
            if full_tag.startswith("/"):
                # It's a closing tag, e.g. </thoughts>
                tag_name = full_tag[1:].strip()
                # If it matches the current arg, close it
                if self.current_arg_name == tag_name:
                    self._close_tool_arg()
                else:
                    # Possibly a mismatched or unknown closing tag
                    # For safety, you could treat it as literal text or ignore,
                    # but we'll just close any open arg to avoid confusion:
                    if self.current_arg_name:
                        self._close_tool_arg()
                continue
            else:
                # It's an opening tag, e.g. <thoughts>
                # If there's an arg already open, we close it before opening a new one
                if self.current_arg_name:
                    self._close_tool_arg()
                arg_name = full_tag
                self._start_tool_arg(arg_name)

    def _partial_prefix(self, text: str, pattern: str) -> str:
        """
        Check if the end of 'text' is a prefix of 'pattern'. 
        This helps us detect partial tags so we don't consume them prematurely.
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
