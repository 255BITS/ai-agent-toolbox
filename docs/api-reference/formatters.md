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

By instantiating `XMLPromptFormatter()` without arguments, the formatter will
emit prompts that use the `<use_tool>` tag, matching the default for
`XMLParser()`.

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

## MarkdownPromptFormatter
```python
class MarkdownPromptFormatter(PromptFormatter):
    """
    Formats tool usage prompts in Markdown format.

    This formatter converts tool descriptions into a Markdown-formatted string that uses
    code fences to clearly delineate tool usage examples. Each tool is displayed with its
    name, description, and arguments, along with an example invocation wrapped in a code fence.

    Parameters:
        fence (str): The delimiter used for Markdown code fences (default: "```").

    Methods:
        format_prompt(tools: Dict[str, Dict[str, str]]) -> str
            Creates a Markdown string that lists all available tools along with their details.
        
        usage_prompt(toolbox: Toolbox) -> str
            Generates a complete usage prompt from a Toolbox instance by formatting its
            registered tools.
    """
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
