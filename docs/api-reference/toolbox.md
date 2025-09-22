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

### Argument schema

Each entry in the `args` dictionary describes one argument the tool accepts. The schema supports:

* `type` – coercion target (`"int"`, `"float"`, `"bool"`, `"string"`). Defaults to `"string"`.
* `description` – human readable docs for prompt templates.
* `required` – whether the model must supply the argument. Defaults to `True`.
* `default` – value used when the argument is omitted and `required` is `False`. Defaults are type-converted with the same rules as user input.

Missing required values and invalid conversions are surfaced as structured validation errors instead of printing to stdout.

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
        "style": {
            "type": "string",
            "description": "realistic or cartoon",
            "required": False,
            "default": "realistic",
        }
    },
    description="Text-to-image generation tool"
)
```

### Handling Responses

```python
events = parser.parse(llm_response)
for event in events:
    if event.is_tool_call:
        response = toolbox.use(event)
        if response and response.error:
            print("Validation failed:", response.error)
            continue
        if response:
            print(f"""
Tool used: {response.tool.name}
Arguments: {response.tool.args}
Result: {response.result}
""")

# Example validation error payload when a required arg is missing
# {
#     "type": "validation_error",
#     "message": "Argument validation failed.",
#     "errors": [{"field": "prompt", "type": "missing", ...}]
# }
```
