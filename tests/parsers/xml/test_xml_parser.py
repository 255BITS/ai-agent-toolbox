import pytest
from ai_agent_toolbox import XMLParser
from pprint import pprint

@pytest.fixture
def parser():
    return XMLParser(tag="use_tool")

def assert_text_create(event, expected_id_pattern=None):
    assert event.type == "text"
    assert event.mode == "create"
    assert event.id is not None
    if expected_id_pattern:
        assert re.match(expected_id_pattern, event.id)

def assert_text_append(event, text_id, content):
    assert event.type == "text"
    assert event.mode == "append"
    assert event.id == text_id
    assert event.content == content

def assert_text_close(event, text_id):
    assert event.type == "text"
    assert event.mode == "close"
    assert event.id == text_id

def assert_tool_create(event):
    assert event.type == "tool"
    assert event.mode == "create"
    assert event.id is not None

def assert_tool_append(event, tool_id, arg, content):
    assert event.type == "tool"
    assert event.mode == "append"
    assert event.id == tool_id
    assert event.content == content

def assert_tool_close(event, tool_id, expected_tool_name=None):
    assert event.type == "tool"
    assert event.mode == "close"
    assert event.id == tool_id
    if expected_tool_name:
        assert event.tool is not None
        assert event.tool.name == expected_tool_name

def test_basic_tool_parsing(parser):
    """Test parsing a single complete tool use."""
    input_text = """Some text
    <use_tool>
        <name>thinking</name>
        <thoughts>test thoughts</thoughts>
    </use_tool>
    More text"""
    
    events = list(parser.parse(input_text))
    
    # Expect sequence:
    # 1. text create
    # 2. text append "Some text\n    "
    # 3. text close
    # 4. tool create (thinking)
    # 5. tool append (thoughts="test thoughts")
    # 6. tool close
    # 7. text create
    # 8. text append "\n    More text"
    # 9. text close
    
    assert len(events) == 9
    
    # First text block
    assert_text_create(events[0])
    text_id_1 = events[0].id
    assert_text_append(events[1], text_id_1, "Some text\n    ")
    assert_text_close(events[2], text_id_1)
    
    # Tool block
    assert_tool_create(events[3])
    tool_id = events[3].id
    assert_tool_append(events[4], tool_id, "thoughts", "test thoughts")
    assert_tool_close(events[5], tool_id)
    
    # Final text block
    assert_text_create(events[6])
    text_id_2 = events[6].id
    assert_text_append(events[7], text_id_2, "\n    More text")
    assert_text_close(events[8], text_id_2)
    
    # Verify tool call accessibility
    assert events[5].is_tool_call
    assert events[5].tool.args == {"thoughts": "test thoughts"}

def test_streaming_partial_tool(parser):
    """Test parsing a tool split across multiple chunks."""
    chunk1 = """Some text <use_tool><name>thinking</name><thou"""
    chunk2 = """ghts>test thoughts</thoughts></use_tool> More text"""
    
    events1 = list(parser.parse_chunk(chunk1))
    events2 = list(parser.parse_chunk(chunk2))
    
    # First chunk should produce:
    # 1. text create
    # 2. text append "Some text "
    # 3. text close
    # 4. tool create
    assert len(events1) == 4
    assert_text_create(events1[0])
    text_id_1 = events1[0].id
    assert_text_append(events1[1], text_id_1, "Some text ")
    assert_text_close(events1[2], text_id_1)
    assert_tool_create(events1[3])
    tool_id = events1[3].id
    
    # Second chunk should complete the tool and start new text:
    # 1. tool append (thoughts="test thoughts")
    # 2. tool close
    # 3. text create
    # 4. text append " More text"
    assert len(events2) >= 4
    assert_tool_append(events2[0], tool_id, "thoughts", "test thoughts")
    assert_tool_close(events2[1], tool_id)
    
    # Verify the complete tool is accessible
    assert events2[1].is_tool_call
    assert events2[1].tool.args == {"thoughts": "test thoughts"}

def test_multiple_tools(parser):
    """Test parsing multiple tools in sequence."""
    input_text = """
    <use_tool>
        <name>tool1</name>
        <arg1>value1</arg1>
    </use_tool>
    Middle text
    <use_tool>
        <name>tool2</name>
        <arg2>value2</arg2>
    </use_tool>
    """
    
    events = list(parser.parse(input_text))
    
    # Verify both tools are parsed correctly
    tool_events = [e for e in events if e.is_tool_call]
    assert len(tool_events) == 2
    assert tool_events[0].tool.args == {"arg1": "value1"}
    assert tool_events[1].tool.args == {"arg2": "value2"}
