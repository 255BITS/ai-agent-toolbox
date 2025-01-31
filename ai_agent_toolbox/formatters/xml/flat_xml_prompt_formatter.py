from typing import Dict
from ai_agent_toolbox.formatters.prompt_formatter import PromptFormatter

class FlatXMLPromptFormatter(PromptFormatter):
    """
    Formats tool usage prompts in Flat XML format, compatible with FlatXMLParser.
    """
    def __init__(self, tag="use_tool"):
        self.tag = tag

    def format_prompt(self, tools: Dict[str, Dict[str, str]]) -> str:
        lines = [f"You can invoke the following tools using <{self.tag}>:"]

        for tool_name, data in tools.items():
            lines.extend([
                f"Tool name: {tool_name}",
                f"Description: {data['description']}",
                "Argument: string",
            ])
            if data.get('content', {}).get('description', None):
                lines.extend([f"Argument description: {data['content']['description']}"])

            lines.append("")

        lines.extend([
            "Example:",
            f"<{self.tag}>",
            "arguments",
            f"</{self.tag}>"
        ])

        return "\n".join(lines)

    def usage_prompt(self, toolbox) -> str:
        """
        Generates a prompt explaining tool usage and argument schemas from a Toolbox.
        """
        return self.format_prompt(toolbox._tools)
