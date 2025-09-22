# Tool Response

`ToolResponse` objects encapsulate both successful outcomes and structured failures from tool executions alongside contextual metadata.

## Structure

```python
@dataclass
class ToolResponse:
    tool: ToolUse         # Tool invocation details (name and arguments)
    result: Optional[Any] # Return value from tool execution
    error: Optional[Any]  # Structured error payload when execution is skipped
```

## Key Features

- **Unified Interface:** Access tool results and errors through standardized fields
- **Context Preservation:** Maintains link to original tool call through `tool` property
- **Direct Exception Propagation:** Tool exceptions are not swallowed; they surface to the caller so you can decide how to respond.

## Example Usage
```python
response = toolbox.use(event)
if response and response.error:
    # Example: validation errors include the failing field and reason
    print("Tool call rejected:", response.error)
elif response:
    print(f"{response.tool.name} result: {response.result}")
```

## Error Handling

`Toolbox.use()` and `Toolbox.use_async()` do not wrap tool exceptions. If a registered tool raises an error, the exception propagates to the caller and no `ToolResponse` is produced. Use standard Python error handling (e.g., `try`/`except`) around tool invocation when you need to intercept or recover from failures.

Schema validation issues and missing tools do not raise; instead the toolbox returns a `ToolResponse` whose `error` field contains a machine-readable payload (e.g., `{"type": "validation_error", ...}`). Forward this back to the LLM to request corrected arguments.
