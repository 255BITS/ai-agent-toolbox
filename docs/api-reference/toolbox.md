# Toolbox

## Toolbox Class

```python
class Toolbox:
    """
    Central registry for tool management
    
    Methods:
        add_tool(name: str, fn: Callable, args: Dict, description: str = "")
            Register tool with schema validation
            
        use(event: ParserEvent) -> Optional[Any]
            Execute tool from parsed event
        use_async(event: ParserEvent) -> Optional[Any]
            Execute tool from parsed event, for async tools
    """
```

### Types

When adding a tool, `args` can have any of the following type:

* "int" - integer value
* "float" - floating point value
* "bool" - boolean(true or false)
* "string" - text
* "list" - JSON array that will be parsed into a Python list
* "dict" - JSON object that will be parsed into a Python dict
* "enum" - string/number/boolean where valid values are restricted via `choices`

List and dict values are parsed from JSON strings emitted by the model. If the
model already emits structured JSON objects (e.g. via OpenAI responses), the
toolbox accepts those directly.

### Schema Options

Each argument definition can declare additional schema metadata:

* `parser`: Callable that receives the converted value and returns the final
  value (e.g. convert a parsed dict into a dataclass).
* `choices`: Iterable of allowed values. Commonly used with `enum` to restrict
  options.
* `min` / `max`: Numeric bounds that are validated after conversion.

Validation is executed after built-in conversion and any custom parser runs, so
constraints apply to the final value passed into the tool.

### Example Registration

```python
def image_generate(prompt: str, style: str = "realistic"):
    """Generate image from text prompt"""
    pass

toolbox.add_tool(
    name="image_generate",
    fn=image_generate,
    args={
        "prompt": {"type": "string", "description": "Image description"},
        "style": {"type": "string", "description": "realistic or cartoon"}
    },
    description="Text-to-image generation tool"
)
```

#### Structured arguments example

```python
import json
from ai_agent_toolbox import Toolbox
from ai_agent_toolbox.parser_event import ParserEvent, ToolUse

def summarize_tasks(tasks, metadata, priority, limit):
    return {
        "next_task": tasks[0]["title"],
        "metadata": metadata,
        "priority": priority,
        "limit": limit,
    }


toolbox = Toolbox()
toolbox.add_tool(
    name="summarize_tasks",
    fn=summarize_tasks,
    args={
        "tasks": {"type": "list"},
        "metadata": {"type": "dict"},
        "priority": {"type": "enum", "choices": ["low", "medium", "high"]},
        "limit": {"type": "int", "min": 1, "max": 5},
    },
)

event = ParserEvent(
    type="tool",
    mode="close",
    id="tasks-1",
    tool=ToolUse(
        name="summarize_tasks",
        args={
            "tasks": json.dumps([
                {"title": "Write docs"},
                {"title": "Ship release"},
            ]),
            "metadata": json.dumps({"owner": "core-team"}),
            "priority": "high",
            "limit": "2",
        },
    ),
    is_tool_call=True,
)

result = toolbox.use(event)
print(result.result)
```

### Handling Responses

```python
events = parser.parse(llm_response)
for event in events:
    if event.is_tool_call:
        response = toolbox.use(event)
        if response:
            print(f"""
Tool used: {response.tool.name}
Arguments: {response.tool.args}
Result: {response.result}
""")
```
