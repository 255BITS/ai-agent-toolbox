from __future__ import annotations

import inspect
import json
from typing import Any, Callable, Dict, Optional, Union

from .parser_event import ParserEvent
from .tool_response import ToolResponse

# Type alias for argument schema: can be a string like "int" or a dict with type/description/etc
ArgSchema = Union[str, Dict[str, Any]]

# Bool coercion constants
_TRUTHY = frozenset(("true", "1", "yes", "y", "on"))
_FALSY = frozenset(("false", "0", "no", "n", "off"))


def _coerce_bool(value: Any) -> bool:
    """Coerce value to bool with string parsing."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUTHY:
            return True
        if lowered in _FALSY:
            return False
    raise ValueError(f"Cannot convert value {value!r} to bool")

class ToolConflictError(Exception):
    """Raised when trying to register a tool name that already exists."""

    pass


class ToolArgumentError(ValueError):
    """Raised when a tool argument fails type conversion or validation.

    Inherits from ValueError for backwards compatibility with code that
    catches ValueError for validation errors.

    Attributes:
        tool_name: The name of the tool being invoked.
        arg_name: The name of the argument that failed.
        message: Description of what went wrong.
    """

    def __init__(self, tool_name: str, arg_name: str, message: str) -> None:
        self.tool_name = tool_name
        self.arg_name = arg_name
        super().__init__(f"Tool '{tool_name}' argument '{arg_name}': {message}")

class Toolbox:
    def __init__(self) -> None:
        self._tools: Dict[str, Dict[str, Any]] = {}

    def add_tool(
        self,
        name: str,
        fn: Callable[..., Any],
        args: Dict[str, ArgSchema],
        description: str = "",
    ) -> None:
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

    def _get_tool_data(self, event: ParserEvent) -> Optional[Dict[str, Any]]:
        """Shared validation and argument processing."""
        if not event.is_tool_call or not event.tool:
            return None

        tool_name = event.tool.name
        if tool_name not in self._tools:
            return None

        tool_data = {**self._tools[tool_name]}  # Shallow copy
        processed_args: Dict[str, Any] = {}

        for arg_name, arg_schema in tool_data["args"].items():
            if arg_name not in event.tool.args:
                # Argument not provided - skip it (allows optional arguments)
                continue

            raw_value = event.tool.args[arg_name]
            schema_dict = self._normalize_arg_schema(arg_schema)
            try:
                processed_args[arg_name] = self._convert_arg(raw_value, schema_dict)
            except (ValueError, TypeError) as exc:
                raise ToolArgumentError(tool_name, arg_name, str(exc)) from exc

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

    # Type coercion dispatch table - O(1) lookup vs if-chain
    _COERCERS: Dict[str, Callable[[Any], Any]] = {
        "int": int,
        "float": float,
        "bool": _coerce_bool,
        "string": lambda v: v if isinstance(v, str) else str(v),
    }

    @classmethod
    def _coerce_type(cls, value: Any, arg_type: str) -> Any:
        if arg_type == "list":
            return cls._load_json_container(value, list)
        if arg_type == "dict":
            return cls._load_json_container(value, dict)
        if arg_type == "enum":
            return cls._maybe_parse_json(value)
        coercer = cls._COERCERS.get(arg_type)
        return coercer(value) if coercer else value

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
        choices = arg_schema.get("choices")
        if choices is not None and value not in choices:
            raise ValueError(f"Value {value!r} not in allowed choices: {choices!r}")
        min_value = arg_schema.get("min")
        if min_value is not None:
            try:
                if value < min_value:
                    raise ValueError(f"Value {value!r} is less than minimum {min_value!r}")
            except TypeError as exc:
                raise TypeError(f"Cannot compare value {value!r} with minimum {min_value!r}") from exc
        max_value = arg_schema.get("max")
        if max_value is not None:
            try:
                if value > max_value:
                    raise ValueError(f"Value {value!r} exceeds maximum {max_value!r}")
            except TypeError as exc:
                raise TypeError(f"Cannot compare value {value!r} with maximum {max_value!r}") from exc
