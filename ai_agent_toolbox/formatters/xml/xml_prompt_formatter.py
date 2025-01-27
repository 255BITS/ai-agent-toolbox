from typing import Dict
from ai_agent_toolbox.formatters.prompt_formatter import PromptFormatter

class XMLPromptFormatter(PromptFormatter):
    """
    Formats tool usage prompts in XML format, compatible with XMLParser.
    Assumes the use of <tool>, <name>, <argName> XML tags.
    """
    def __init__(self, tag="tool"):
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

        lines.append("Examples:")
        for tool_name, data in tools.items():
            example_lines = [
                f"<{self.tag}>",
                f"    <name>{tool_name}</name>"
            ]
            
            for i, arg_name in enumerate(data["args"].keys(), start=1):
                example_lines.append(f"    <{arg_name}>value{i}</{arg_name}>")
            
            example_lines.append(f"</{self.tag}>")
            lines.extend(example_lines)
            # Add empty line between examples
            lines.append("")

        return "\n".join(lines)

    def usage_prompt(self, toolbox) -> str:
        """
        Generates a prompt explaining tool usage and argument schemas from a Toolbox.
        """
        base_prompt = self.format_prompt(toolbox._tools)
        return base_prompt
