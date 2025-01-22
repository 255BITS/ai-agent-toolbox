from typing import Any, Callable, Dict, Optional
from .parser_event import ParserEvent, ToolUse

class ToolConflictError(Exception):
    """Raised when trying to register a tool name that already exists"""
    pass

class Toolbox:
    """
    A toolbox that holds callable tools with schema validation,
    type conversion, and usage prompt generation.
    """

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def add_tool(
        self,
        name: str,
        fn: Callable[..., Any],
        args: Dict[str, Dict[str, str]],
        description: str = "",
    ) -> None:
        """
        Register a tool with validation against name conflicts.
        """
        if name in self._tools:
            raise ToolConflictError(f"Tool {name} already registered")
        self._tools[name] = {
            "fn": fn,
            "args": args,
            "description": description,
        }

    def use(self, event: ParserEvent) -> Optional[Any]:
        """
        Executes tools with schema validation and type conversion.
        Returns None for invalid calls or execution errors.
        """
        if not event.is_tool_call or not event.tool:
            return None

        tool_name = event.tool.name
        if tool_name not in self._tools:
            return None

        tool_data = self._tools[tool_name]
        processed_args = {}

        for arg_name, arg_schema in tool_data["args"].items():
            # Validate required arguments
            print("items", arg_name)
            if arg_name not in event.tool.args:
                return None

            # Convert argument types
            raw_value = event.tool.args[arg_name]
            arg_type = arg_schema.get("type", "string")
            processed_args[arg_name] = self._convert_arg(raw_value, arg_type)
        return tool_data["fn"](**processed_args)

    @staticmethod
    def _convert_arg(value: str, arg_type: str) -> Any:
        """Converts string arguments to specified types"""
        if arg_type == "integer":
            return int(value)
        if arg_type == "number":
            return float(value)
        if arg_type == "boolean":
            return value.lower() in ("true", "1", "yes")
        return value  # Default to string
