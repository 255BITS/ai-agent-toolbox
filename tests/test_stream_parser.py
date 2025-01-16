import pytest
import re
from app.llm.stream_parser import StreamParser
from app.tools import Tool, tool_action
from pprint import pprint

@pytest.fixture
def parser():
    """
    A pytest fixture that returns a fresh StreamParser each time.
    Assumes the new StreamParser emits events with type='text'/'tool'
    and modes: 'create', 'append', 'close'.
    """
    return StreamParser()

def assert_text_create(event, expected_id_pattern=None):
    """Helper to assert an event is a text create."""
    assert event["type"] == "text"
    assert event["mode"] == "create"
    assert "id" in event
    if expected_id_pattern:
        assert re.match(expected_id_pattern, event["id"])

def assert_text_append(event, text_id, content):
    """Helper to assert an event is a text append."""
    assert event["type"] == "text"
    assert event["mode"] == "append"
    assert event["id"] == text_id
    assert event["content"] == content

def assert_text_close(event, text_id):
    """Helper to assert an event is a text close."""
    assert event["type"] == "text"
    assert event["mode"] == "close"
    assert event["id"] == text_id

def assert_tool_create(event, expected_tool_name=None):
    """Helper to assert an event is tool create."""
    assert event["type"] == "tool"
    assert event["mode"] == "create"
    assert "id" in event
    if expected_tool_name:
        assert event["tool_name"] == expected_tool_name

def assert_tool_append(event, tool_id, arg, content):
    """Helper to assert an event is tool append."""
    assert event["type"] == "tool"
    assert event["mode"] == "append"
    assert event["id"] == tool_id
    assert event["arg"] == arg
    assert event["content"] == content

def assert_tool_close(event, tool_id):
    """Helper to assert an event is tool close."""
    assert event["type"] == "tool"
    assert event["mode"] == "close"
    assert event["id"] == tool_id


def test_single_tool_use(parser):
    """
    A single <use_tool> block in a single parse call, plus text before and after.
    """
    input_text = "Some text <use_tool><name>test_tool</name><arg1>value1</arg1></use_tool> More text"
    events = parser.parse(input_text)
    events += parser.flush()

    # We expect:
    # 1) text create
    # 2) text append "Some text "
    # 3) text close
    # 4) tool create (test_tool)
    # 5) tool append (arg1, "value1")
    # 6) tool close
    # 7) text create
    # 8) text append " More text"
    # 9) text close

    # Text block #1
    assert_text_create(events[0])
    text_id_1 = events[0]["id"]
    assert_text_append(events[1], text_id_1, "Some text ")
    assert_text_close(events[2], text_id_1)

    # Tool usage
    assert_tool_create(events[3], expected_tool_name="test_tool")
    tool_id = events[3]["id"]
    assert_tool_append(events[4], tool_id, "arg1", "value1")
    assert_tool_close(events[5], tool_id)

    # Text block #2
    assert_text_create(events[6])
    text_id_2 = events[6]["id"]
    assert_text_append(events[7], text_id_2, " More text")
    assert_text_close(events[8], text_id_2)
    assert len(events) == 9


def test_multiple_tool_uses(parser):
    """
    Two separate tool uses with intermediate text in a single parse call.
    """
    input_text = (
        "<use_tool><name>test_tool</name><arg1>value1</arg1></use_tool>"
        "Intermediate text"
        "<use_tool><name>test_tool</name><arg2>value2</arg2></use_tool>"
    )
    events = parser.parse(input_text)
    events += parser.flush()

    # Expected sequence:
    # 1) tool create
    # 2) tool append (arg1, "value1")
    # 3) tool close
    # 4) text create
    # 5) text append "Intermediate text"
    # 6) text close
    # 7) tool create
    # 8) tool append (arg2, "value2")
    # 9) tool close

    pprint(events)
    assert len(events) == 9

    # First tool block
    assert_tool_create(events[0], "test_tool")
    tool_id_1 = events[0]["id"]
    assert_tool_append(events[1], tool_id_1, "arg1", "value1")
    assert_tool_close(events[2], tool_id_1)

    # Intermediate text
    assert_text_create(events[3])
    text_id_1 = events[3]["id"]
    assert_text_append(events[4], text_id_1, "Intermediate text")
    assert_text_close(events[5], text_id_1)

    # Second tool block
    assert_tool_create(events[6], "test_tool")
    tool_id_2 = events[6]["id"]
    assert_tool_append(events[7], tool_id_2, "arg2", "value2")
    assert_tool_close(events[8], tool_id_2)

def test_partial_tool_use(parser):
    """
    Here we split the tool block across two parse calls.
    First parse call doesn't complete the tool usage.
    Second parse call finishes it.
    """
    chunk1 = "Some text <use_tool><name>test_tool</name><arg1>value1"
    events1 = parser.parse(chunk1)

    # The parser sees "Some text " outside, so it should form a text block,
    # but doesn't see a full </use_tool> yet, so no tool close.
    # Also, the <arg1> block is incomplete (missing </arg1>).
    # Expected events:
    #   1) text create
    #   2) text append "Some text "
    #   3) text close
    #   4) tool create
    #   5) tool append
    # The partial <use_tool> remains in buffer with partial <arg1>.
    assert len(events1) == 5
    assert_text_create(events1[0])
    txt_id = events1[0]["id"]
    assert_text_append(events1[1], txt_id, "Some text ")
    assert_text_close(events1[2], txt_id)

    # Second chunk completes the arg block and closes the tool.
    chunk2 = "</arg1></use_tool> More text"
    events2 = parser.parse(chunk2)
    events2 += parser.flush()

    # We expect:
    # 1) tool close
    # 2) text create
    # 3) text append " More text"
    # 4) text close

    # Assert the remaining tool events from the second chunk
    assert len(events2) == 4

    # Tool usage
    tool_id = events1[3]["id"]  # The tool created in the first chunk
    assert_tool_close(events2[0], tool_id)  # Closing the tool

    # Text block after tool usage
    assert_text_create(events2[1])  # New text block starts
    text_id_2 = events2[2]["id"]
    assert_text_append(events2[2], text_id_2, " More text")
    assert_text_close(events2[3], text_id_2)


def test_partial_tag(parser):
    """
    Test a scenario where <use_tool> is split across chunk boundaries,
    e.g. "Some text <us" in chunk1 and "e_tool>" in chunk2.
    """
    chunk1 = "Some text <us"
    events1 = parser.parse(chunk1)

    # Assert that we processed the initial text block "Some text "
    # and the parser is holding onto "<us" for potential completion.
    assert len(events1) == 2
    assert_text_create(events1[0])  # Text block starts
    text_id_1 = events1[0]["id"]
    assert_text_append(events1[1], text_id_1, "Some text ")

    # Next chunk completes "<use_tool>"
    chunk2 = "e_tool><name>test_tool</name><arg1>val</arg1></use_tool> End"
    events2 = parser.parse(chunk2)
    events2 += parser.flush()

    # Expected:
    #  1) text close
    #  2) tool create (test_tool)
    #  3) tool append (arg1, "val")
    #  4) tool close
    #  5) text create
    #  6) text append " End"
    #  7) text close

    pprint(events2)
    assert len(events2) == 7

    # Tool usage block
    assert_tool_create(events2[1], "test_tool")
    tool_id = events2[1]["id"]
    assert_tool_append(events2[2], tool_id, "arg1", "val")
    assert_tool_close(events2[3], tool_id)

    # Final text block
    assert_text_create(events2[4])
    text_id_2 = events2[4]["id"]
    assert_text_append(events2[5], text_id_2, " End")
    assert_text_close(events2[6], text_id_2)

def test_multiple_args(parser):
    """
    Test a single tool block with multiple arguments.
    We want to see separate 'append' events for each arg,
    plus partial text if the parser is designed that way.
    """
    input_text = (
        "<use_tool>"
        "<name>test_tool</name>"
        "<arg1>Hello</arg1>"
        "<arg2>World</arg2>"
        "<arg1>Again</arg1>"
        "</use_tool>"
    )
    events = parser.parse(input_text)

    # Expected event flow:
    #   1) tool create (test_tool)
    #   2) tool append {arg=arg1, content="Hello"}
    #   3) tool append {arg=arg2, content="World"}
    #   4) tool append {arg=arg1, content="Again"}
    #   5) tool close
    assert len(events) == 5

    # tool create
    assert_tool_create(events[0], "test_tool")
    tool_id = events[0]["id"]

    # arg1=Hello
    assert_tool_append(events[1], tool_id, "arg1", "Hello")
    # arg2=World
    assert_tool_append(events[2], tool_id, "arg2", "World")
    # arg1=Again
    assert_tool_append(events[3], tool_id, "arg1", "Again")

    # close
    assert_tool_close(events[4], tool_id)

def test_partial_end_tag(parser):
    chunk1 = "Some text <use_tool>"
    events1 = parser.parse(chunk1)
    chunk2 = "<name>test_tool</name><arg1>val</arg1></us"
    events2 = parser.parse(chunk2)
    chunk3 = "e_tool> End"
    events3 = parser.parse(chunk3)
    events3 += parser.flush()

    # Expected:
    #  1) tool close
    #  2) text create
    #  3) text append " End"
    #  4) text close

    tool_id = events2[0]["id"]
    assert len(events3) == 4

    assert_tool_close(events3[0], tool_id)

    assert_text_create(events3[1])
    text_id_2 = events3[2]["id"]
    assert_text_append(events3[2], text_id_2, " End")
    assert_text_close(events3[3], text_id_2)


