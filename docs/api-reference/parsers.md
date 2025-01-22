# Parsers

AI Agent Toolbox parsers are fast and support streaming.

## XMLParser

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
    events = parser.parse("<tool><name>search</name><query>AI news</query></tool>")
```
### Example Output

```python
[
    ParserEvent(type='tool', name='search', mode='create', id='1', is_tool_call=False),
    ParserEvent(type='tool', name='search', mode='append', id='1', content='Analyze user request'), TODO
    ParserEvent(type='tool', name='search', mode='close', id='1', is_tool_call=True, tool=ToolUse(name='think'))
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
events = parser.parse("<search>AI news</action>")
```

### Example Output

```python
[
    ParserEvent(type='tool', name='action', mode='create', id='1', is_tool_call=False),
    ParserEvent(type='tool', name='action', mode='append', id='1', content='AI news'),
    ParserEvent(type='tool', name='action', mode='close', id='1', is_tool_call=True, content='AI news')
]
```
