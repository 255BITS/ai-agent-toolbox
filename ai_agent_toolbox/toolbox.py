from typing import Any, Callable, Dict, Optional, Tuple
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
        tool_data, error = self._get_tool_data(event)
        if tool_data is None and error is None:
            return None

        if error:
            return ToolResponse(
                tool=event.tool,
                error=error
            )

        if tool_data["is_async"]:
            raise RuntimeError(f"Async tool {event.tool.name} called with sync use(). Call use_async() instead.")

        tool_result = tool_data["fn"](**tool_data["processed_args"])
        return ToolResponse(
            tool=event.tool,
            result=tool_result
        )

    async def use_async(self, event: ParserEvent) -> Optional[ToolResponse]:
        """For both sync and async tools"""
        tool_data, error = self._get_tool_data(event)
        if tool_data is None and error is None:
            return None

        if error:
            return ToolResponse(
                tool=event.tool,
                error=error
            )

        if tool_data["is_async"]:
            tool_result = await tool_data["fn"](**tool_data["processed_args"])
        else:
            tool_result = tool_data["fn"](**tool_data["processed_args"])
        return ToolResponse(
            tool=event.tool,
            result=tool_result
        )

    def _get_tool_data(self, event: ParserEvent) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Shared validation and argument processing"""
        if not event.is_tool_call or not event.tool:
            return None, None

        tool_name = event.tool.name
        if tool_name not in self._tools:
            return None, {
                "type": "unknown_tool",
                "message": f"Tool '{tool_name}' is not registered."
            }

        tool_def = self._tools[tool_name]
        tool_data = {**tool_def}  # Shallow copy
        processed_args: Dict[str, Any] = {}
        validation_errors = []
        errored_fields = set()
        provided_args = event.tool.args or {}

        for arg_name, arg_schema in tool_def.get("args", {}).items():
            schema = arg_schema or {}
            required = schema.get("required", True)
            arg_type = schema.get("type", "string")
            has_value = arg_name in provided_args and provided_args[arg_name] is not None

            if not has_value:
                if "default" in schema:
                    default_value = schema["default"]
                    try:
                        processed_args[arg_name] = self._convert_arg(default_value, arg_type)
                    except (ValueError, TypeError) as exc:
                        validation_errors.append({
                            "field": arg_name,
                            "type": "invalid_default",
                            "message": f"Default value for '{arg_name}' is not valid for type '{arg_type}'.",
                            "value": default_value,
                            "details": str(exc)
                        })
                        errored_fields.add(arg_name)
                elif required:
                    validation_errors.append({
                        "field": arg_name,
                        "type": "missing",
                        "message": f"Missing required argument '{arg_name}'."
                    })
                    errored_fields.add(arg_name)
                continue

            raw_value = provided_args[arg_name]
            try:
                processed_args[arg_name] = self._convert_arg(raw_value, arg_type)
            except (ValueError, TypeError) as exc:
                validation_errors.append({
                    "field": arg_name,
                    "type": "invalid",
                    "message": f"Invalid value for '{arg_name}' with type '{arg_type}'.",
                    "value": raw_value,
                    "details": str(exc)
                })
                errored_fields.add(arg_name)

        for arg_name, raw_value in provided_args.items():
            if arg_name in errored_fields:
                continue
            if arg_name not in processed_args:
                processed_args[arg_name] = raw_value

        tool_data["processed_args"] = processed_args

        if validation_errors:
            return tool_data, {
                "type": "validation_error",
                "message": "Argument validation failed.",
                "errors": validation_errors
            }

        return tool_data, None

    @staticmethod
    def _convert_arg(value: Any, arg_type: str) -> Any:
        """Converts arguments to specified types"""
        if arg_type == "int":
            if isinstance(value, int):
                return value
            return int(value)
        if arg_type == "float":
            if isinstance(value, float):
                return value
            if isinstance(value, int):
                return float(value)
            return float(value)
        if arg_type == "bool":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in ("true", "1", "yes", "y", "on"):
                    return True
                if normalized in ("false", "0", "no", "n", "off"):
                    return False
                raise ValueError(f"Cannot convert '{value}' to bool")
            if isinstance(value, (int, float)):
                return bool(value)
            raise TypeError(f"Cannot convert type {type(value).__name__} to bool")
        return value  # Default to string
