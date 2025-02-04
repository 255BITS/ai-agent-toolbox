# Parsers

AI Agent Toolbox parsers are fast and support streaming.

## XMLParser

Note that this is not a strict XML parser. The parser is very open with what it expects. For example, React snippets work without the need for CDATA.

```python
class XMLParser:
    """
    Streaming XML parser for structured tool invocations
    
    Parameters:
        tag (str): Root XML tag to parse (default: 'use_tool')
    
    Methods:
        parse(text: str) -> List[ParserEvent]
            Parse complete text and return all events
            
        parse_chunk(chunk: str) -> List[ParserEvent]
            Process partial text in streaming scenarios
            
        flush() -> List[ParserEvent]
            Finalize parsing and return remaining events
    """
```

### Example Input
```python
    from ai_agent_toolbox import XMLParser
    parser = XMLParser(tag="tool")
    events = parser.parse("Searching... <tool><name>search</name><query>AI news</query></tool>")
```
### Example Output

```python
[
    ParserEvent(type='text', mode='create', id='04a5e0b5-3c06-4a53-859e-90f8f28d400b', tool=None, is_tool_call=False, content=None),
    ParserEvent(type='text', mode='append', id='04a5e0b5-3c06-4a53-859e-90f8f28d400b', tool=None, is_tool_call=False, content='Searching... '),
    ParserEvent(type='text', mode='close', id='04a5e0b5-3c06-4a53-859e-90f8f28d400b', tool=None, is_tool_call=False, content=None),
    ParserEvent(type='tool', mode='create', id='0ebfb6ac-98d0-4d01-9228-08a1826fce32', tool=None, is_tool_call=False, content='search'),
    ParserEvent(type='tool', mode='append', id='0ebfb6ac-98d0-4d01-9228-08a1826fce32', tool=None, is_tool_call=False, content='AI news'),
    ParserEvent(type='tool', mode='close', id='0ebfb6ac-98d0-4d01-9228-08a1826fce32', tool=ToolUse(name='search', args={'query': 'AI news'}), is_tool_call=True, content=None)
]
```

## FlatXMLParser

```python
class FlatXMLParser:
    """
    Fast parser for simple XML tags without nesting
    
    Parameters:
        *tags (str): Variable list of tags to capture (e.g. "think", "action")
    
    Methods:
        parse(text: str) -> List[ParserEvent]
            Parse complete text with recognized tags
    """
```

### Example Usage
```python
from ai_agent_toolbox import FlatXMLParser
parser = FlatXMLParser("search")
events = parser.parse("<search>AI news</search>")
```

### Example Output
```python
[
    ParserEvent(type='tool', mode='create', id='8b62426a-9bca-40e0-a9da-b2a57c6e3ba3', tool=None, is_tool_call=False, content=None),
    ParserEvent(type='tool', mode='append', id='8b62426a-9bca-40e0-a9da-b2a57c6e3ba3', tool=None, is_tool_call=False, content='AI news'),
    ParserEvent(type='tool', mode='close', id='8b62426a-9bca-40e0-a9da-b2a57c6e3ba3', tool=ToolUse(name='search', args={'content': 'AI news'}), is_tool_call=True, content='AI news')
]
```

## MarkdownParser

The `MarkdownParser` is a streaming parser for Markdown code fences that treats code blocks as tool calls.
It supports code fences with an optional language identifier (e.g. ```python) and treats all text outside
the code fences as plain text.

### Methods

* `parse(text: str) -> List[ParserEvent]`: Parses the complete Markdown text.
* `parse_chunk(chunk: str) -> List[ParserEvent]`: Processes a chunk of Markdown text in streaming scenarios.
* `flush() -> List[ParserEvent]`: Finalizes parsing by forcing the closure of any open code fence.

### Example Usage

```python
from ai_agent_toolbox.parsers.markdown.markdown_parser import MarkdownParser

parser = MarkdownParser()
markdown_text = "Hello world.\n```python\nprint('Hi')\n```"
events = parser.parse(markdown_text)
for event in events:
    print(event)
```

The parser emits `ParserEvent` objects with `type` set to `"text"` for regular content and `"tool"` for code blocks.

## ParserEvent

```python
class ParserEvent:
    """
    Represents parsing events during stream processing.
    """

    type: str  # Specifies the type of event, either 'text' or 'tool'.
    mode: str  # The mode of the event, which can be 'create', 'append', or 'close'.
    id: str  # A unique identifier for the event.
    tool: Optional[ToolUse]  # Details of the tool invocation, if applicable.
    is_tool_call: bool  # Indicates whether this is the final closure of a tool.
    content: Optional[str]  # The content of the text or tool.
```
