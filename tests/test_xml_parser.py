import pytest
from ai_agent_toolbox.parsers import XMLParser
from ai_agent_toolbox.tools import Toolbox
from pprint import pprint

@pytest.fixture
def toolbox():
    """Fixture to provide a new toolbox instance."""
    return Toolbox()

@pytest.fixture
def parser():
    """Fixture to provide an XMLParser instance for <use_tool> blocks."""
    return XMLParser(tag="use_tool")

def test_single_tool_use(toolbox, parser):
    """
    Tests parsing and execution of a single <use_tool> block.
    """
    toolbox.add_tool(
        name="test_tool",
        args={"arg1": "str"},
        description="Test tool for parsing single arguments."
    )

    input_text = "<use_tool><name>test_tool</name><arg1>value1</arg1></use_tool>"
    events = list(parser.stream(input_text))

    # Verify events from the parser
    assert len(events) == 3
    assert events[0].is_tool_call
    assert events[0].tool_name == "test_tool"
    assert events[1].arg == "arg1"
    assert events[1].content == "value1"

    # Execute the tool and capture results
    result = toolbox.use(events[0])
    assert result == {"arg1": "value1"}

def test_multiple_tools(toolbox, parser):
    """
    Tests parsing and execution of multiple <use_tool> blocks in a single stream.
    """
    toolbox.add_tool(
        name="tool1",
        args={"input": "str"},
        description="First test tool."
    )
    toolbox.add_tool(
        name="tool2",
        args={"data": "int"},
        description="Second test tool."
    )

    input_text = (
        "<use_tool><name>tool1</name><input>hello</input></use_tool>"
        "<use_tool><name>tool2</name><data>42</data></use_tool>"
    )

    events = list(parser.stream(input_text))

    # Verify the first tool
    assert events[0].tool_name == "tool1"
    assert events[1].arg == "input"
    assert events[1].content == "hello"

    result1 = toolbox.use(events[0])
    assert result1 == {"input": "hello"}

    # Verify the second tool
    assert events[2].tool_name == "tool2"
    assert events[3].arg == "data"
    assert events[3].content == 42

    result2 = toolbox.use(events[2])
    assert result2 == {"data": 42}

def test_stream_with_text(toolbox, parser):
    """
    Tests streaming input that includes text outside <use_tool> blocks.
    """
    toolbox.add_tool(
        name="simple_tool",
        args={"value": "str"},
        description="A simple tool for testing."
    )

    input_text = "Preceding text <use_tool><name>simple_tool</name><value>test</value></use_tool> Trailing text"
    events = list(parser.stream(input_text))

    # Verify text events and tool usage
    assert events[0].is_text
    assert events[0].content == "Preceding text "

    assert events[1].is_tool_call
    assert events[1].tool_name == "simple_tool"
    assert events[2].arg == "value"
    assert events[2].content == "test"

    result = toolbox.use(events[1])
    assert result == {"value": "test"}

    assert events[3].is_text
    assert events[3].content == " Trailing text"

def test_partial_stream(toolbox, parser):
    """
    Tests handling of partial input streams.
    """
    toolbox.add_tool(
        name="increment",
        args={"number": "int"},
        description="Increments a number."
    )

    chunk1 = "<use_tool><name>increment</name><number>"
    chunk2 = "10</number></use_tool>"

    events1 = list(parser.stream(chunk1))
    assert len(events1) == 0  # No complete tool block yet

    events2 = list(parser.stream(chunk2))
    assert len(events2) == 3

    assert events2[0].is_tool_call
    assert events2[0].tool_name == "increment"
    assert events2[1].arg == "number"
    assert events2[1].content == 10

    result = toolbox.use(events2[0])
    assert result == {"number": 11}
