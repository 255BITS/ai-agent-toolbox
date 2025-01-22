from typing import Dict
from ai_agent_toolbox.formatters.prompt_formatter import PromptFormatter

class XMLPromptFormatter(PromptFormatter):
    """
    Formats tool usage prompts in XML format, compatible with XMLParser.
    Assumes the use of <use_tool>, <name>, <argName> XML tags.
    """
    def __init__(self, tag="use_tool"):
        self.tag = tag

    def format_prompt(self, tools: Dict[str, Dict[str, str]]) -> str:
        lines = [f"You can invoke the following tools using <{self.tag}>:"]

        for tool_name, data in tools.items():
            lines.extend([
                f"Tool name: {tool_name}",
                f"Description: {data['description']}",
                "Arguments:"
            ])

            for arg_name, arg_schema in data["args"].items():
                arg_type = arg_schema.get("type", "string")
                arg_desc = arg_schema.get("description", "")
                lines.append(f"  {arg_name} ({arg_type}): {arg_desc}")

            lines.append("")

        lines.extend([
            "Example:",
            f"<{self.tag}>",
            "    <name>tool_name</name>",
            "    <arg1>value1</arg1>",
            "    <arg2>value2</arg2>",
            f"</{self.tag}>"
        ])

        return "\n".join(lines)

    def usage_prompt(self, toolbox) -> str:
        """
        Generates a prompt explaining tool usage and argument schemas from a Toolbox.
        """
        return self.format_prompt(toolbox._tools)
