import glob
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


def _split_nodeid(arg: str) -> tuple[str, str | None]:
    if "::" in arg:
        base, node = arg.split("::", 1)
        return base, node
    return arg, None


def _node_matches_file(node: str | None, path: pathlib.Path) -> bool:
    """Heuristically determine if a node id could live in ``path``."""

    if node is None:
        return True

    segments = [segment.split("[", 1)[0] for segment in node.split("::") if segment]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False

    for segment in segments:
        if segment.startswith("test"):
            signature = f"def {segment}"
            async_signature = f"async def {segment}"
            if signature in text or async_signature in text:
                continue
        if segment[0].isupper():
            class_signature = f"class {segment}"
            if class_signature in text:
                continue
        if segment in text:
            continue
        return False
    return True


def _expand_glob_pattern(arg: str) -> List[str]:
    base, node = _split_nodeid(arg)
    if not any(character in base for character in "*?["):
        return [arg]

    matches = sorted(glob.glob(base, recursive=True))
    if not matches:
        return [arg]

    cwd = pathlib.Path.cwd()
    expanded: List[str] = []
    for match in matches:
        match_path = pathlib.Path(match)
        if not _node_matches_file(node, match_path):
            continue
        try:
            match_path = match_path.relative_to(cwd)
        except ValueError:
            pass
        path_text = match_path.as_posix()
        if node is not None:
            path_text = f"{path_text}::{node}"
        expanded.append(path_text)

    if expanded:
        return expanded
    return [arg]


def pytest_configure(config):
    """Expand glob patterns in CLI arguments so ``pytest`` sees real files."""

    original_args = list(config.args)
    if not original_args:
        return

    expanded_parts = [_expand_glob_pattern(arg) for arg in original_args]
    if all(part == [original] for part, original in zip(expanded_parts, original_args)):
        return

    expanded_args = [item for part in expanded_parts for item in part]
    config.args[:] = expanded_args
    if hasattr(config.option, "file_or_dir"):
        config.option.file_or_dir[:] = expanded_args

    invocation_args = list(config.invocation_params.args)
    replacements = iter(zip(original_args, expanded_parts))
    current = next(replacements, None)
    rewritten: List[str] = []
    for arg in invocation_args:
        if current is not None and arg == current[0]:
            rewritten.extend(current[1])
            current = next(replacements, None)
        else:
            rewritten.append(arg)

    invocation_cls = type(config.invocation_params)
    config._invocation_params = invocation_cls(
        args=rewritten,
        plugins=config.invocation_params.plugins,
        dir=config.invocation_params.dir,
    )
