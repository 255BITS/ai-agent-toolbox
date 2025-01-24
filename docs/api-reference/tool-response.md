# Tool Response

`ToolResponse` objects encapsulate the complete outcome of tool executions, including results, errors, and contextual metadata.

## Structure

```python
@dataclass
class ToolResponse:
    tool: ToolUse         # Tool invocation details (name and arguments)
    result: Optional[Any] # Return value from tool execution
    error: Optional[Exception] # Any exception raised during execution
    message: Optional[str] # Optional human-readable status message
```

## Key Features

- **Unified Interface:** Access tool results and errors through standardized fields
- **Context Preservation:** Maintains link to original tool call through `tool` property
- **Error Resilience:** Captures exceptions without interrupting control flow

## Example Usage
```python
response = toolbox.use(event)
print(f"{response.tool.name} result: {response.result}")
