class FlatXMLParser:
    """
    A simple, flat parser that scans for one or more specific XML-style tags
    (e.g. <think>...</think>, <action>...</action>) within a string,
    and extracts their contents. Non-tag text is returned as a separate
    text event.

    No regex is used. This does not handle nesting or streaming.
    """

    def __init__(self, *tags):
        """
        :param tags: the tags (strings) you want to capture, e.g. "think", "action"
        """
        self.tags = list(tags)

    def parse(self, text: str):
        """
        Parse the given text and return a list of event dictionaries:
          - For outside text, returns: { "type": "text", "content": <string> }
          - For recognized tags, returns: { "type": <tag>, "content": <tag_inner_text> }

        :param text: the entire text to parse
        :return: list of event dicts, e.g.
                 [
                   {"type": "text", "content": "hello "},
                   {"type": "think", "content": "I should say be enthusiastic"},
                   {"type": "action", "content": "wave hello"}
                 ]
        """
        events = []
        i = 0
        length = len(text)

        while i < length:
            # Find the next <tag> among all allowed tags
            next_tag_start = None
            next_tag_name = None

            for tag in self.tags:
                open_tag = f"<{tag}>"
                pos = text.find(open_tag, i)
                # Keep track of the earliest occurrence across all recognized tags
                if pos != -1 and (next_tag_start is None or pos < next_tag_start):
                    next_tag_start = pos
                    next_tag_name = tag

            # If no further tags are found, everything left is text
            if next_tag_start is None:
                if i < length:
                    events.append({
                        "type": "text",
                        "content": text[i:]
                    })
                break

            # Emit a text event if there's text before the next tag
            if next_tag_start > i:
                events.append({
                    "type": "text",
                    "content": text[i:next_tag_start]
                })

            # Now handle the found tag
            open_tag_str = f"<{next_tag_name}>"
            close_tag_str = f"</{next_tag_name}>"
            open_tag_len = len(open_tag_str)

            # Search for the corresponding closing tag
            content_start = next_tag_start + open_tag_len
            close_idx = text.find(close_tag_str, content_start)
            if close_idx == -1:
                # If there's no closing tag, treat everything as content after <tag>
                tag_content = text[content_start:]
                events.append({
                    "type": next_tag_name,
                    "content": tag_content
                })
                # Then we're done (no more text to parse)
                i = length
            else:
                # Extract the text inside the tag
                tag_content = text[content_start:close_idx]
                events.append({
                    "type": next_tag_name,
                    "content": tag_content
                })
                i = close_idx + len(close_tag_str)

        return events
