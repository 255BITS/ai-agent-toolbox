# Tool Use

`ToolUse` objects represent invocations of tools by an AI agent.

- **Tool Name**: Identifier for the registered tool
- **Arguments**: Key-value pairs of parameters

## Structure

```python
@dataclass
class ToolUse:
    name: str
    args: Dict[str, Any]
```

## Creation Flow

1. **Detection**: Parsers identify tool invocation patterns in LLM output
2. **Validation**: Toolbox verifies the tool exists and arguments match schema
3. **Execution**: Registered tool function is called with processed arguments

## Example Usage

```python
event = ParserEvent(
    type="tool",
    mode="close",
    id="123",
    tool=ToolUse(
        name="search",
        args={"query": "AI safety papers"}
    ),
    is_tool_call=True
)

response = toolbox.use(event)
print(f"Search results: {response.result}")
```
