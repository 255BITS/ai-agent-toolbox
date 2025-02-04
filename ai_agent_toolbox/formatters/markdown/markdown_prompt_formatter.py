from typing import Dict
from ai_agent_toolbox.formatters.prompt_formatter import PromptFormatter

class MarkdownPromptFormatter(PromptFormatter):
    """
    Formats tool usage prompts in Markdown format.
    Tools are described using Markdown code fences.
    """
    def __init__(self, fence="```"):
        self.fence = fence

    def format_prompt(self, tools: Dict[str, Dict[str, str]]) -> str:
        lines = ["You can invoke the following tools using Markdown code fences:"]
        for tool_name, data in tools.items():
            lines.append("")
            lines.append(f"**Tool name:** {tool_name}")
            lines.append(f"**Description:** {data.get('description', '')}")
            lines.append("**Arguments:**")
            for arg_name, arg_schema in data.get("args", {}).items():
                arg_type = arg_schema.get("type", "string")
                arg_desc = arg_schema.get("description", "")
                lines.append(f"- {arg_name} ({arg_type}): {arg_desc}")
            lines.append("")
            lines.append("**Example:**")
            lines.append(f"{self.fence}{tool_name}")
            # For each argument, provide a placeholder value.
            for i, arg_name in enumerate(data.get("args", {}).keys(), start=1):
                lines.append(f"    {arg_name}: value{i}")
            lines.append(f"{self.fence}")
        return "\n".join(lines)

    def usage_prompt(self, toolbox) -> str:
        """
        Generates a usage prompt from a Toolbox instance.
        """
        return self.format_prompt(toolbox._tools)
