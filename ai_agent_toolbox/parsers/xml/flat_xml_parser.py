import uuid
from ai_agent_toolbox.parser_event import ParserEvent, ToolUse

class FlatXMLParser:
    """
    A simple, flat parser that scans for one or more specific XML-style tags
    (e.g. <think>...</think>, <action>...</action>) within a string,
    and emits ParserEvent objects (text/tool, create/append/close).
    
    No regex is used. This does not handle nesting but supports a streaming-
    friendly sequence of events for each text or recognized tag.
    """

    def __init__(self, *tags):
        """
        :param tags: the tags (strings) you want to capture, e.g. "think", "action"
        """
        self.tags = list(tags)

    def parse(self, text: str):
        """
        Parses the entire text in one go, yielding ParserEvent objects.
        
        Yields:
          - For each contiguous run of *outside* text, a sequence of:
              1) text create
              2) text append (with the chunk of text)
              3) text close
          - For recognized tags: 
              1) tool create
              2) tool append (with the text inside the tag in 'content')
              3) tool close (with ParserEvent.tool=ToolUse(name=<tag>))
                
          Unknown tags are treated as plain text.
        """
        i = 0
        length = len(text)

        # Accumulate outside text to flush later
        text_buffer = []

        def flush_text_buffer():
            """If there's buffered text, emit create/append/close events for it."""
            if not text_buffer:
                return
            chunk = "".join(text_buffer)
            text_buffer.clear()

            text_id = str(uuid.uuid4())
            yield ParserEvent(
                type="text",
                mode="create",
                id=text_id,
                is_tool_call=False
            )
            yield ParserEvent(
                type="text",
                mode="append",
                id=text_id,
                is_tool_call=False,
                content=chunk
            )
            yield ParserEvent(
                type="text",
                mode="close",
                id=text_id,
                is_tool_call=False
            )

        while i < length:
            # Find the next recognized <tag> from our list
            next_tag_start = None
            next_tag_name = None

            for tag in self.tags:
                open_tag = f"<{tag}>"
                pos = text.find(open_tag, i)
                if pos != -1 and (next_tag_start is None or pos < next_tag_start):
                    next_tag_start = pos
                    next_tag_name = tag

            # If no recognized tag is found, everything left is outside text
            if next_tag_start is None:
                text_buffer.append(text[i:])
                i = length
                break

            # Otherwise, flush any text we have accumulated *before* the tag
            if next_tag_start > i:
                text_buffer.append(text[i:next_tag_start])

            # Start of recognized tag
            open_tag_str = f"<{next_tag_name}>"
            close_tag_str = f"</{next_tag_name}>"
            content_start = next_tag_start + len(open_tag_str)
            
            # Search for its closing tag
            close_idx = text.find(close_tag_str, content_start)
            if close_idx == -1:
                # No close tag found, so everything after is "inside" this recognized tag
                tag_content = text[content_start:]
                i = length
            else:
                tag_content = text[content_start:close_idx]
                i = close_idx + len(close_tag_str)

            # Flush any outside text before we yield new tool events
            yield from flush_text_buffer()

            # For this recognized tag, yield tool create / append / close
            tool_id = str(uuid.uuid4())
            yield ParserEvent(
                type="tool",
                mode="create",
                id=tool_id,
                is_tool_call=False  # becomes True only upon 'close' if you like
            )
            # The entire text in the recognized tag is appended
            if tag_content:
                yield ParserEvent(
                    type="tool",
                    mode="append",
                    id=tool_id,
                    content=tag_content,
                    is_tool_call=False
                )
            # On close, we can attach a final ToolUse with the recognized tag name
            yield ParserEvent(
                type="tool",
                mode="close",
                id=tool_id,
                is_tool_call=True,  # Mark as a tool call on the close
                tool=ToolUse(name=next_tag_name, args={}),
                content=tag_content
            )

        # End of string. Flush any remaining text as text events
        yield from flush_text_buffer()
