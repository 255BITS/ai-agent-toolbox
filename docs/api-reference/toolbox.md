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
    """
```

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
        "style": {"type": "string", "enum": ["realistic", "cartoon"]}
    },
    description="Text-to-image generation tool"
)
```
