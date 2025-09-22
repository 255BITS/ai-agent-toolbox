from typing import Dict

from ai_agent_toolbox.formatters.prompt_formatter import (
    PromptFormatter,
    iter_tool_metadata,
)

class MarkdownPromptFormatter(PromptFormatter):
    """
    Formats tool usage prompts in Markdown format.
    Tools are described using Markdown code fences.
    """
    def __init__(self, fence="```"):
        self.fence = fence

    def format_prompt(self, tools: Dict[str, Dict[str, str]]) -> str:
        lines = ["You can invoke the following tools using Markdown code fences:"]

        for tool in iter_tool_metadata(tools):
            lines.append("")
            lines.append(f"**Tool name:** {tool.name}")
            lines.append(f"**Description:** {tool.description}")
            lines.append("**Arguments:**")
            for arg in tool.args:
                lines.append(f"- {arg.name} ({arg.type}): {arg.description}")
            lines.append("")
            lines.append("**Example:**")
            lines.append(f"{self.fence}{tool.name}")
            # For each argument, provide a placeholder value.
            for i, arg in enumerate(tool.args, start=1):
                lines.append(f"    {arg.name}: value{i}")
            lines.append(f"{self.fence}")
        return "\n".join(lines)

