from typing import Any, Callable, Dict, Optional
from .parser_event import ParserEvent, ToolUse

class Toolbox:
    """
    A straightforward toolbox that holds references to callable tools
    and can generate a usage prompt for them.
    """

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def add_tool(
        self,
        name: str,
        fn: Callable[..., Any],
        args: Dict[str, Any],
        description: str = "",
    ) -> None:
        """
        Register a tool with the given name, function, argument schema, and description.
        """
        self._tools[name] = {
            "fn": fn,
            "args": args,
            "description": description,
        }

    def usage_prompt(self) -> str:
        """
        Generate a string describing how to invoke each tool and the schema for its arguments.
        This can be appended to system prompts to guide an LLM on how to call these tools.
        """
        lines = []
        lines.append("You can invoke the following tools using <use_tool>:")
        for tool_name, data in self._tools.items():
            lines.append(f"Tool name: {tool_name}")
            lines.append(f"Description: {data['description']}")
            lines.append("Arguments:")
            for arg_name, arg_schema in data["args"].items():
                arg_type = arg_schema.get("type", "string")
                arg_desc = arg_schema.get("description", "")
                lines.append(f"  {arg_name} ({arg_type}): {arg_desc}")
            lines.append("")

        lines.append("For example:")
        lines.append("<use_tool>")
        lines.append("    <name>tool_name</name>")
        lines.append("    <arg1>value1</arg1>")
        lines.append("    <arg2>value2</arg2>")
        lines.append("</use_tool>")

        return "\n".join(lines)

    def use(self, event: ParserEvent) -> Optional[Any]:
        """
        If the event is a tool call, attempts to call the corresponding tool function
        with the event's arguments. Returns the function result or None if not applicable.
        """
        if event.is_tool_call and event.tool is not None:
            tool_name = event.tool.name
            if tool_name in self._tools:
                fn = self._tools[tool_name]["fn"]
                try:
                    return fn(**event.tool.args)
                except Exception:
                    # You can log or handle errors as desired. We just return None here.
                    return None
            else:
                # No such tool in the toolbox
                return None
        return None
