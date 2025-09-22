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
