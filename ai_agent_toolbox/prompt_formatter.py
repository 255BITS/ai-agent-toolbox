from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

__all__ = [
    "ArgumentMetadata",
    "ToolMetadata",
    "iter_tool_metadata",
    "PromptFormatter",
]


@dataclass(frozen=True)
class ArgumentMetadata:
    """Normalized metadata for a single tool argument."""

    name: str
    type: str
    description: str
    schema: Dict[str, Any]


@dataclass(frozen=True)
class ToolMetadata:
    """Normalized metadata for a registered tool."""

    name: str
    description: str
    args: Tuple[ArgumentMetadata, ...]
    content: Optional[ArgumentMetadata] = None


def _normalize_schema(schema: Any) -> Dict[str, Any]:
    """Return a dictionary representation of a schema definition."""

    if schema is None:
        return {}

    if isinstance(schema, str):
        normalized: Dict[str, Any] = {"type": schema}
    elif isinstance(schema, Mapping):
        normalized = dict(schema)
    else:
        normalized = {"type": str(schema)}

    schema_type = normalized.get("type")
    if schema_type is None:
        normalized["type"] = "string"
    elif not isinstance(schema_type, str):
        normalized["type"] = str(schema_type)

    if "description" in normalized and not isinstance(normalized["description"], str):
        normalized["description"] = str(normalized["description"])

    return normalized


def iter_tool_metadata(tools: Mapping[str, Mapping[str, Any]]) -> Iterable[ToolMetadata]:
    """Yield normalized metadata structures for tools from a toolbox dictionary."""

    for tool_name, raw_data in tools.items():
        data_candidate = raw_data or {}
        if not isinstance(data_candidate, Mapping):
            data_candidate = {}
        data: Mapping[str, Any] = data_candidate
        raw_description = data.get("description", "")
        description = "" if raw_description is None else str(raw_description)

        arg_entries = []
        for arg_name, arg_schema in (data.get("args") or {}).items():
            normalized = _normalize_schema(arg_schema)
            arg_entries.append(
                ArgumentMetadata(
                    name=arg_name,
                    type=normalized.get("type", "string"),
                    description=normalized.get("description", ""),
                    schema=normalized,
                )
            )
        args: Tuple[ArgumentMetadata, ...] = tuple(arg_entries)

        content_meta: Optional[ArgumentMetadata] = None
        if "content" in data and data.get("content") is not None:
            normalized = _normalize_schema(data.get("content"))
            content_meta = ArgumentMetadata(
                name="content",
                type=normalized.get("type", "string"),
                description=normalized.get("description", ""),
                schema=normalized,
            )

        yield ToolMetadata(
            name=tool_name,
            description=description,
            args=args,
            content=content_meta,
        )


class PromptFormatter:
    """Abstract base class for prompt formatters."""

    def format_prompt(self, tools: Mapping[str, Mapping[str, Any]]) -> str:
        """Formats the prompt to describe available tools."""

        raise NotImplementedError

    def usage_prompt(self, toolbox) -> str:
        """Generate a usage prompt from a Toolbox instance."""

        return self.format_prompt(toolbox._tools)
