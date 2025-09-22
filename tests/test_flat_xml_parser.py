import pytest

from ai_agent_toolbox.parsers.xml.flat_xml_parser import FlatXMLParser


@pytest.fixture
def flat_xml_event_goldens():
    return {
        "partial_tags_and_multiple_blocks": [
            {"type": "text", "mode": "create", "id": "id0", "is_tool_call": False},
            {"type": "text", "mode": "append", "id": "id0", "is_tool_call": False, "content": "Before "},
            {"type": "text", "mode": "close", "id": "id0", "is_tool_call": False},
            {"type": "tool", "mode": "create", "id": "id1", "is_tool_call": False},
            {"type": "tool", "mode": "append", "id": "id1", "is_tool_call": False, "content": "One"},
            {
                "type": "tool",
                "mode": "close",
                "id": "id1",
                "is_tool_call": True,
                "content": "One",
                "tool": {"name": "think", "args": {"content": "One"}},
            },
            {"type": "text", "mode": "create", "id": "id2", "is_tool_call": False},
            {"type": "text", "mode": "append", "id": "id2", "is_tool_call": False, "content": " mid "},
            {"type": "text", "mode": "close", "id": "id2", "is_tool_call": False},
            {"type": "tool", "mode": "create", "id": "id3", "is_tool_call": False},
            {"type": "tool", "mode": "append", "id": "id3", "is_tool_call": False, "content": "Go"},
            {
                "type": "tool",
                "mode": "close",
                "id": "id3",
                "is_tool_call": True,
                "content": "Go",
                "tool": {"name": "action", "args": {"content": "Go"}},
            },
            {"type": "text", "mode": "create", "id": "id4", "is_tool_call": False},
            {"type": "text", "mode": "append", "id": "id4", "is_tool_call": False, "content": " after"},
            {"type": "text", "mode": "close", "id": "id4", "is_tool_call": False},
        ],
        "forced_close_on_flush": [
            {"type": "tool", "mode": "create", "id": "id0", "is_tool_call": False},
            {"type": "tool", "mode": "append", "id": "id0", "is_tool_call": False, "content": "value"},
            {"type": "tool", "mode": "append", "id": "id0", "is_tool_call": False, "content": " continues"},
            {
                "type": "tool",
                "mode": "close",
                "id": "id0",
                "is_tool_call": True,
                "content": "value continues",
                "tool": {"name": "think", "args": {"content": "value continues"}},
            },
        ],
    }


def test_flat_xml_parser_handles_partial_tags(flat_xml_event_goldens, stream_events):
    parser = FlatXMLParser("think", "action")
    chunks = ["Before <thin", "k>One</think> mid <", "action>Go</action> after"]
    actual = stream_events(parser, chunks)
    assert actual == flat_xml_event_goldens["partial_tags_and_multiple_blocks"]


def test_flat_xml_parser_flushes_unclosed_tag(flat_xml_event_goldens, stream_events):
    parser = FlatXMLParser("think")
    chunks = ["<think>value", " continues"]
    actual = stream_events(parser, chunks)
    assert actual == flat_xml_event_goldens["forced_close_on_flush"]
