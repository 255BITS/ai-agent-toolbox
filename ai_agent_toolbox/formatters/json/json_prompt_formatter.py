import json
from typing import Any, Dict

from ai_agent_toolbox.formatters.prompt_formatter import (
    PromptFormatter,
    iter_tool_metadata,
)


class JSONPromptFormatter(PromptFormatter):
    """Formats tool usage instructions for JSON-based tool calls."""

    def format_prompt(self, tools: Dict[str, Dict[str, Any]]) -> str:
        lines = [
            "You can invoke the following tools by returning JSON objects with type \"tool_call\":",
        ]

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

        lines.append("Example tool call payloads:")

        for tool in tool_metadata:
            example_args = {}
            for idx, arg in enumerate(tool.args, start=1):
                placeholder: Any = f"value{idx}"
                arg_type = str(arg.schema.get("type", "")).lower()
                if arg_type in {"int", "integer"}:
                    placeholder = idx
                elif arg_type in {"number", "float"}:
                    placeholder = float(idx)
                example_args[arg.name] = placeholder

            example_payload = {
                "type": "tool_call",
                "function": {
                    "name": tool.name,
                    "arguments": example_args,
                },
            }
            lines.append(json.dumps(example_payload, indent=4))
            lines.append("")

        return "\n".join(lines).strip()

