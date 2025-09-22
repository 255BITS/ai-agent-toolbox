# Tool Response

`ToolResponse` objects encapsulate the successful outcome of tool executions and contextual metadata.

## Structure

```python
@dataclass
class ToolResponse:
    tool: ToolUse         # Tool invocation details (name and arguments)
    result: Optional[Any] # Return value from tool execution
```

## Key Features

- **Unified Interface:** Access tool results and errors through standardized fields
- **Context Preservation:** Maintains link to original tool call through `tool` property
- **Direct Exception Propagation:** Tool exceptions are not swallowed; they surface to the caller so you can decide how to respond.

## Example Usage
```python
try:
    response = toolbox.use(event)
except Exception as exc:
    handle_tool_failure(exc)
else:
    print(f"{response.tool.name} result: {response.result}")
```

## Error Handling

`Toolbox.use()` and `Toolbox.use_async()` do not wrap tool exceptions. If a registered tool raises an error, the exception propagates to the caller and no `ToolResponse` is produced. Use standard Python error handling (e.g., `try`/`except`) around tool invocation when you need to intercept or recover from failures.
