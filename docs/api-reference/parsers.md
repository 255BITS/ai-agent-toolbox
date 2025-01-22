# Parsers

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

### Example Usage

```python
# Batch processing
parser = XMLParser(tag="action")
events = parser.parse("<action><name>search</name><query>AI news</query></action>")

# Streaming processing
for chunk in stream:
    events = parser.parse_chunk(chunk)
    process_events(events)
final_events = parser.flush()
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

### Example Output

```python
[
    ParserEvent(type='tool', mode='create', id='1', is_tool_call=False),
    ParserEvent(type='tool', mode='append', id='1', content='Analyze user request'),
    ParserEvent(type='tool', mode='close', id='1', is_tool_call=True, tool=ToolUse(name='think'))
]
```

## ToolUse Dataclass

```python
@dataclass
class ToolUse:
    """
    Structured tool invocation record
    
    Fields:
        name (str): Registered tool name
        args (Dict[str, Any]): Validated arguments
    """
```
