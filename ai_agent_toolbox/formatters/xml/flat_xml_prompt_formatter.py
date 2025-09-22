from typing import Dict

from ai_agent_toolbox.formatters.prompt_formatter import (
    PromptFormatter,
    iter_tool_metadata,
)

class FlatXMLPromptFormatter(PromptFormatter):
    """
    Formats tool usage prompts in Flat XML format, compatible with FlatXMLParser.
    """
    def __init__(self, tag="use_tool"):
        self.tag = tag

    def format_prompt(self, tools: Dict[str, Dict[str, str]]) -> str:
        lines = [f"You can invoke the following tools using <{self.tag}>:"]

        for tool in iter_tool_metadata(tools):
            lines.extend(
                [
                    f"Tool name: {tool.name}",
                    f"Description: {tool.description}",
                    "Argument: string",
                ]
            )

            if tool.content and tool.content.description:
                lines.append(f"Argument description: {tool.content.description}")

            lines.append("")

        lines.extend(
            [
                "Example:",
                f"<{self.tag}>",
                "arguments",
                f"</{self.tag}>",
            ]
        )

        return "\n".join(lines)

