import json
from typing import Any, Dict

from ai_agent_toolbox.formatters.prompt_formatter import PromptFormatter


class JSONPromptFormatter(PromptFormatter):
    """Formats tool usage instructions for JSON-based tool calls."""

    def format_prompt(self, tools: Dict[str, Dict[str, Any]]) -> str:
        lines = [
            "You can invoke the following tools by returning JSON objects with type \"tool_call\":",
        ]

        for tool_name, data in tools.items():
            lines.extend([
                f"Tool name: {tool_name}",
                f"Description: {data.get('description', '')}",
                "Arguments:",
            ])

            for arg_name, arg_schema in data.get("args", {}).items():
                arg_type = arg_schema.get("type", "string")
                arg_desc = arg_schema.get("description", "")
                lines.append(f"  {arg_name} ({arg_type}): {arg_desc}")

            lines.append("")

        lines.append("Example tool call payloads:")

        for tool_name, data in tools.items():
            example_args = {}
            for idx, (arg_name, arg_schema) in enumerate(data.get("args", {}).items(), start=1):
                placeholder = f"value{idx}"
                if arg_schema.get("type") in {"int", "integer"}:
                    placeholder = idx
                elif arg_schema.get("type") in {"number", "float"}:
                    placeholder = float(idx)
                example_args[arg_name] = placeholder

            example_payload = {
                "type": "tool_call",
                "function": {
                    "name": tool_name,
                    "arguments": example_args,
                },
            }
            lines.append(json.dumps(example_payload, indent=4))
            lines.append("")

        return "\n".join(lines).strip()

