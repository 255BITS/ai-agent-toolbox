import pytest

from ai_agent_toolbox.parsers.markdown.markdown_parser import MarkdownParser


@pytest.fixture
def markdown_event_goldens():
    return {
        "json_code_block": [
            {"type": "text", "mode": "create", "id": "id0", "is_tool_call": False},
            {"type": "text", "mode": "append", "id": "id0", "is_tool_call": False, "content": "Before "},
            {"type": "text", "mode": "close", "id": "id0", "is_tool_call": False},
            {"type": "tool", "mode": "create", "id": "id1", "is_tool_call": False},
            {"type": "tool", "mode": "append", "id": "id1", "is_tool_call": False, "content": '{"key": 1'},
            {"type": "tool", "mode": "append", "id": "id1", "is_tool_call": False, "content": "}\n"},
            {
                "type": "tool",
                "mode": "close",
                "id": "id1",
                "is_tool_call": True,
                "content": '{"key": 1}\n',
                "tool": {"name": "json", "args": {"content": '{"key": 1}\n'}},
            },
            {"type": "text", "mode": "create", "id": "id2", "is_tool_call": False},
            {"type": "text", "mode": "append", "id": "id2", "is_tool_call": False, "content": " After"},
            {"type": "text", "mode": "close", "id": "id2", "is_tool_call": False},
        ],
        "partial_fence_then_close": [
            {"type": "text", "mode": "create", "id": "id0", "is_tool_call": False},
            {"type": "text", "mode": "append", "id": "id0", "is_tool_call": False, "content": "Intro "},
            {"type": "text", "mode": "close", "id": "id0", "is_tool_call": False},
            {"type": "tool", "mode": "create", "id": "id1", "is_tool_call": False},
            {"type": "tool", "mode": "append", "id": "id1", "is_tool_call": False, "content": "code"},
            {"type": "tool", "mode": "append", "id": "id1", "is_tool_call": False, "content": "\n"},
            {
                "type": "tool",
                "mode": "close",
                "id": "id1",
                "is_tool_call": True,
                "content": "code\n",
                "tool": {"name": "python", "args": {"content": "code\n"}},
            },
            {"type": "text", "mode": "create", "id": "id2", "is_tool_call": False},
            {"type": "text", "mode": "append", "id": "id2", "is_tool_call": False, "content": " trailing"},
            {"type": "text", "mode": "close", "id": "id2", "is_tool_call": False},
        ],
        "forced_flush_completion": [
            {"type": "tool", "mode": "create", "id": "id0", "is_tool_call": False},
            {"type": "tool", "mode": "append", "id": "id0", "is_tool_call": False, "content": "line"},
            {"type": "tool", "mode": "append", "id": "id0", "is_tool_call": False, "content": " one"},
            {
                "type": "tool",
                "mode": "close",
                "id": "id0",
                "is_tool_call": True,
                "content": "line one",
                "tool": {"name": "python", "args": {"content": "line one"}},
            },
        ],
    }


def test_markdown_parser_streams_json_block(markdown_event_goldens, stream_events):
    parser = MarkdownParser()
    chunks = ["Before ```json\n{\"key\": 1", "}\n", "``` After"]
    actual = stream_events(parser, chunks)
    assert actual == markdown_event_goldens["json_code_block"]


def test_markdown_parser_handles_partial_fence(markdown_event_goldens, stream_events):
    parser = MarkdownParser()
    chunks = ["Intro ``", "`python\ncode", "\n``` trailing"]
    actual = stream_events(parser, chunks)
    assert actual == markdown_event_goldens["partial_fence_then_close"]


def test_markdown_parser_flushes_unclosed_block(markdown_event_goldens, stream_events):
    parser = MarkdownParser()
    chunks = ["```python\nline", " one"]
    actual = stream_events(parser, chunks)
    assert actual == markdown_event_goldens["forced_flush_completion"]
