import inspect
import json
from typing import Any, Callable, Dict, Optional

from .parser_event import ParserEvent
from .tool_use import ToolUse
from .tool_response import ToolResponse

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
            schema_dict = self._normalize_arg_schema(arg_schema)
            processed_args[arg_name] = self._convert_arg(raw_value, schema_dict)

        tool_data["processed_args"] = processed_args
        return tool_data

    @staticmethod
    def _normalize_arg_schema(arg_schema: Any) -> Dict[str, Any]:
        if isinstance(arg_schema, dict):
            return arg_schema
        if isinstance(arg_schema, str):
            return {"type": arg_schema}
        raise TypeError(f"Argument schema must be a dict or string, got {type(arg_schema)!r}")

    @staticmethod
    def _convert_arg(value: Any, arg_schema: Dict[str, Any]) -> Any:
        """Converts arguments to specified types with validation and custom parsing"""
        arg_type = arg_schema.get("type", "string")
        if isinstance(arg_type, str):
            arg_type = arg_type.lower()

        converted = Toolbox._coerce_type(value, arg_type)

        parser = arg_schema.get("parser")
        if parser is not None:
            if not callable(parser):
                raise TypeError("Parser specified in arg schema must be callable")
            converted = parser(converted)

        Toolbox._validate_value(converted, arg_schema)

        return converted

    @staticmethod
    def _coerce_type(value: Any, arg_type: str) -> Any:
        if arg_type == "int":
            if isinstance(value, bool):
                return int(value)
            return int(value)
        if arg_type == "float":
            if isinstance(value, bool):
                return float(int(value))
            return float(value)
        if arg_type == "bool":
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in ("true", "1", "yes", "y", "on"):
                    return True
                if lowered in ("false", "0", "no", "n", "off"):
                    return False
            raise ValueError(f"Cannot convert value {value!r} to bool")
        if arg_type == "list":
            return Toolbox._load_json_container(value, list)
        if arg_type == "dict":
            return Toolbox._load_json_container(value, dict)
        if arg_type == "enum":
            return Toolbox._maybe_parse_json(value)
        if arg_type == "string":
            if isinstance(value, str):
                return value
            return str(value)
        return value

    @staticmethod
    def _maybe_parse_json(value: Any) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return ""
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return value
        return value

    @staticmethod
    def _load_json_container(value: Any, expected_type: type) -> Any:
        if isinstance(value, expected_type):
            return value
        if not isinstance(value, str):
            raise TypeError(f"Expected {expected_type.__name__} or JSON string, got {type(value).__name__}")
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON for {expected_type.__name__}: {value!r}") from exc
        if not isinstance(parsed, expected_type):
            raise TypeError(
                f"JSON value did not produce a {expected_type.__name__}: {parsed!r}"
            )
        return parsed

    @staticmethod
    def _validate_value(value: Any, arg_schema: Dict[str, Any]) -> None:
        if "choices" in arg_schema:
            choices = arg_schema["choices"]
            if value not in choices:
                raise ValueError(f"Value {value!r} not in allowed choices: {choices!r}")
        if "min" in arg_schema:
            min_value = arg_schema["min"]
            try:
                if value < min_value:
                    raise ValueError(f"Value {value!r} is less than minimum {min_value!r}")
            except TypeError as exc:
                raise TypeError(
                    f"Cannot compare value {value!r} with minimum {min_value!r}"
                ) from exc
        if "max" in arg_schema:
            max_value = arg_schema["max"]
            try:
                if value > max_value:
                    raise ValueError(f"Value {value!r} exceeds maximum {max_value!r}")
            except TypeError as exc:
                raise TypeError(
                    f"Cannot compare value {value!r} with maximum {max_value!r}"
                ) from exc
