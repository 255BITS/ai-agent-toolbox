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

## FlatXMLPromptFormatter

```python
class FlatXMLPromptFormatter(PromptFormatter):
    """
    Formats tool usage prompts in Flat XML format, compatible with FlatXMLParser.

    This formatter converts a set of tool descriptions into a simple, flat XML format.
    It outputs a list of tools with their names, descriptions, and a placeholder for arguments.
    The generated XML is ideal for use with lightweight XML parsers that do not require nested tags.

    Parameters:
        tag (str): The XML tag to wrap the tool usage instructions (default: "use_tool").

    Methods:
        format_prompt(tools: Dict[str, Dict[str, str]]) -> str
            Returns a formatted XML string containing tool details.
        
        usage_prompt(toolbox: Toolbox) -> str
            Generates the XML usage prompt based on the tools registered in a Toolbox.
    """
```

