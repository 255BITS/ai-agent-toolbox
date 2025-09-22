import pytest

from ai_agent_toolbox import XMLParser


@pytest.fixture
def xml_event_goldens():
    return {
        "partial_prefix_finalize": [
            {"type": "text", "mode": "create", "id": "id0", "is_tool_call": False},
            {"type": "text", "mode": "append", "id": "id0", "is_tool_call": False, "content": "Hello "},
            {"type": "text", "mode": "close", "id": "id0", "is_tool_call": False},
            {"type": "tool", "mode": "create", "id": "id1", "is_tool_call": False, "content": "calc"},
            {"type": "tool", "mode": "append", "id": "id1", "is_tool_call": False, "content": "1,2"},
            {"type": "tool", "mode": "append", "id": "id1", "is_tool_call": False, "content": "3"},
            {
                "type": "tool",
                "mode": "close",
                "id": "id1",
                "is_tool_call": True,
                "tool": {"name": "calc", "args": {"numbers": "1,23"}},
            },
        ],
        "nested_tool_recovery": [
            {"type": "tool", "mode": "create", "id": "id0", "is_tool_call": False, "content": "outer"},
            {"type": "tool", "mode": "append", "id": "id0", "is_tool_call": False, "content": "prefix "},
            {
                "type": "tool",
                "mode": "append",
                "id": "id0",
                "is_tool_call": False,
                "content": "<name>inner</name>",
            },
            {"type": "tool", "mode": "append", "id": "id0", "is_tool_call": False, "content": "value"},
            {
                "type": "tool",
                "mode": "close",
                "id": "id0",
                "is_tool_call": True,
                "tool": {
                    "name": "outer",
                    "args": {"arg": "prefix value", "use_tool": "<name>inner</name>"},
                },
            },
            {"type": "text", "mode": "create", "id": "id1", "is_tool_call": False},
            {
                "type": "text",
                "mode": "append",
                "id": "id1",
                "is_tool_call": False,
                "content": " suffix</arg></use_tool>",
            },
            {"type": "text", "mode": "close", "id": "id1", "is_tool_call": False},
        ],
        "invalid_tool_fallback": [
            {"type": "text", "mode": "create", "id": "id0", "is_tool_call": False},
            {"type": "text", "mode": "append", "id": "id0", "is_tool_call": False, "content": "pre "},
            {"type": "text", "mode": "close", "id": "id0", "is_tool_call": False},
            {"type": "text", "mode": "create", "id": "id1", "is_tool_call": False},
            {
                "type": "text",
                "mode": "append",
                "id": "id1",
                "is_tool_call": False,
                "content": " trailing text",
            },
            {"type": "text", "mode": "close", "id": "id1", "is_tool_call": False},
        ],
    }


def test_xml_parser_partial_prefix_finalize(xml_event_goldens, stream_events):
    """Chunks ending mid-tag trigger partial prefix buffering and flush finalizes the tool."""
    parser = XMLParser(tag="use_tool")
    chunks = ["Hello <use_to", "ol><name>calc</name><numbers>1,2", "3"]
    actual = stream_events(parser, chunks)
    assert actual == xml_event_goldens["partial_prefix_finalize"]


def test_xml_parser_nested_tool_recovery(xml_event_goldens, stream_events):
    """Nested tool markers inside arguments stay literal and stream resumes as text."""
    parser = XMLParser(tag="use_tool")
    chunks = [
        "<use_tool><name>outer</name><arg>prefix ",
        "<use_tool><name>inner</name>",
        "<arg>value</arg></use_tool> suffix</arg></use_tool>",
    ]
    actual = stream_events(parser, chunks)
    assert actual == xml_event_goldens["nested_tool_recovery"]


def test_xml_parser_invalid_tool_promotes_text(xml_event_goldens, normalize_events):
    """Malformed tool blocks without a <name> recover into plain text after flush."""
    parser = XMLParser(tag="use_tool")
    events = []
    events.extend(parser.parse_chunk("pre <use_tool><invalid>"))
    events.extend(parser.parse_chunk("value"))
    events.extend(parser.flush())
    events.extend(parser.parse_chunk(" trailing text"))
    events.extend(parser.flush())
    actual = normalize_events(events)
    assert actual == xml_event_goldens["invalid_tool_fallback"]
