from typing import Dict

from ai_agent_toolbox.formatters.prompt_formatter import (
    PromptFormatter,
    iter_tool_metadata,
)

class XMLPromptFormatter(PromptFormatter):
    """
    Formats tool usage prompts in XML format, compatible with XMLParser.
    Assumes the use of <tool>, <name>, <argName> XML tags.
    """
    def __init__(self, tag="tool"):
        self.tag = tag

    def format_prompt(self, tools: Dict[str, Dict[str, str]]) -> str:
        lines = [f"You can invoke the following tools using <{self.tag}>:"]

        tool_metadata = list(iter_tool_metadata(tools))

        for tool in tool_metadata:
            lines.extend(
                [
                    f"Tool name: {tool.name}",
                    f"Description: {tool.description}",
                    "Arguments:",
                ]
            )

            for arg in tool.args:
                lines.append(f"  {arg.name} ({arg.type}): {arg.description}")

            lines.append("")

        lines.append("Examples:")
        for tool in tool_metadata:
            example_lines = [
                f"<{self.tag}>",
                f"    <name>{tool.name}</name>",
            ]

            for i, arg in enumerate(tool.args, start=1):
                example_lines.append(f"    <{arg.name}>value{i}</{arg.name}>")

            example_lines.append(f"</{self.tag}>")
            lines.extend(example_lines)
            # Add empty line between examples
            lines.append("")

        return "\n".join(lines)

