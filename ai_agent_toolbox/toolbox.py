from typing import Any, Callable, Dict, Optional
from .parser_event import ParserEvent, ToolUse
from .tool_response import ToolResponse
import inspect

class ToolConflictError(Exception):
    """Raised when trying to register a tool name that already exists"""
    pass

class Toolbox:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def add_tool(self, name: str, fn: Callable, args: Dict, description: str = ""):
        if name in self._tools:
            raise ToolConflictError(f"Tool {name} already registered")

        # Store whether the function is async
        self._tools[name] = {
            "fn": fn,
            "is_async": inspect.iscoroutinefunction(fn),
            "args": args,
            "description": description,
        }

    def use(self, event: ParserEvent) -> Optional[ToolResponse]:
        """For sync tool execution only"""
        tool_data = self._get_tool_data(event)
        if not tool_data:
            return None

        if tool_data["is_async"]:
            raise RuntimeError(f"Async tool {event.tool.name} called with sync use(). Call use_async() instead.")

        tool_result = tool_data["fn"](**tool_data["processed_args"])
        return ToolResponse(
            tool=event.tool,
            result=tool_result
        )

    async def use_async(self, event: ParserEvent) -> Optional[ToolResponse]:
        """For both sync and async tools"""
        tool_data = self._get_tool_data(event)
        if not tool_data:
            return None
        if tool_data["is_async"]:
            tool_result = await tool_data["fn"](**tool_data["processed_args"])
        else:
            tool_result = tool_data["fn"](**tool_data["processed_args"])
        return ToolResponse(
            tool=event.tool,
            result=tool_result
        )

    def _get_tool_data(self, event: ParserEvent) -> Optional[Dict]:
        """Shared validation and argument processing"""
        if not event.is_tool_call or not event.tool:
            return None

        tool_name = event.tool.name
        if tool_name not in self._tools:
            return None

        tool_data = {**self._tools[tool_name]}  # Shallow copy
        processed_args = {}
        
        for arg_name, arg_schema in tool_data["args"].items():
            if arg_name not in event.tool.args:
                print("Could not find argument", arg_name)
                continue
                
            raw_value = event.tool.args[arg_name]
            arg_type = arg_schema.get("type", "string")
            processed_args[arg_name] = self._convert_arg(raw_value, arg_type)
        
        tool_data["processed_args"] = processed_args
        return tool_data

    @staticmethod
    def _convert_arg(value: str, arg_type: str) -> Any:
        """Converts string arguments to specified types"""
        if arg_type == "int":
            return int(value)
        if arg_type == "float":
            return float(value)
        if arg_type == "bool":
            return value.lower() in ("true", "1", "yes")
        return value  # Default to string
