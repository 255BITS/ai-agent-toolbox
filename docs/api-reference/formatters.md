# Formatters

## XMLPromptFormatter

```python
class XMLPromptFormatter:
    """
    Generates XML-structured prompts for tool documentation
    
    Parameters:
        tag (str): Root XML tag (default: 'use_tool')
    
    Methods:
        format_prompt(tools: Dict) -> str
            Create full prompt with XML tool descriptions
            
        usage_prompt(toolbox: Toolbox) -> str
            Generate prompt section from registered tools
    """
```

### Example Output

```xml
You can invoke the following tools using <use_tool>:
Tool name: search
Description: Web search tool
Arguments:
  query (string): Search keywords
  limit (int): Maximum results to return

Example:
<use_tool>
    <name>search</name>
    <query>AI advancements</query>
</use_tool>
```
