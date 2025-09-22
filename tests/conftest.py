import pathlib
import sys
from typing import Iterable, List

import pytest

# Ensure the repository root is importable when running tests without installing the package.
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_agent_toolbox.parser_event import ParserEvent


@pytest.fixture
def normalize_events():
    """Normalize ParserEvent objects for deterministic comparison."""

    def _normalize(events: Iterable[ParserEvent]):
        id_map = {}
        normalized: List[dict] = []
        for event in events:
            if event.id not in id_map:
                id_map[event.id] = f"id{len(id_map)}"
            entry = {
                "type": event.type,
                "mode": event.mode,
                "id": id_map[event.id],
                "is_tool_call": event.is_tool_call,
            }
            if event.content is not None:
                entry["content"] = event.content
            if event.tool is not None:
                entry["tool"] = {
                    "name": event.tool.name,
                    "args": event.tool.args,
                }
            normalized.append(entry)
        return normalized

    return _normalize


@pytest.fixture
def stream_events(normalize_events):
    """Stream parser chunks and return normalized events (including flush)."""

    def _stream(parser, chunks: Iterable[str], *, flush: bool = True):
        events: List[ParserEvent] = []
        for chunk in chunks:
            events.extend(parser.parse_chunk(chunk))
        if flush:
            events.extend(parser.flush())
        return normalize_events(events)

    return _stream
