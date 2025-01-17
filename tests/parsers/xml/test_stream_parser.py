import pytest
from ai_agent_toolbox.parsers.xml import XMLParser

@pytest.fixture
def parser():
    return XMLParser(tag="use_tool")

def test_basic_tool_parsing(parser):
    response = """
    Some text before
    <use_tool>
        <name>thinking</name>
        <thoughts>test thoughts</thoughts>
    </use_tool>
    Some text after
    """
    events = list(parser.parse(response))
    assert len(events) == 1
    assert events[0].is_tool_call == True
    assert events[0].name == "thinking"
    assert events[0].args == {"thoughts": "test thoughts"}

def test_multiple_tools(parser):
    response = """
    <use_tool>
        <name>tool1</name>
        <arg1>value1</arg1>
    </use_tool>
    Some text between
    <use_tool>
        <name>tool2</name>
        <arg2>value2</arg2>
    </use_tool>
    """
    events = list(parser.parse(response))
    assert len(events) == 2
    assert events[0].name == "tool1"
    assert events[0].args == {"arg1": "value1"}
    assert events[1].name == "tool2"
    assert events[1].args == {"arg2": "value2"}

def test_malformed_xml(parser):
    response = """
    <use_tool>
        <name>thinking
        <thoughts>incomplete tag</thoughts>
    </use_tool>
    """
    with pytest.raises(Exception):  # Replace with specific exception once implemented
        list(parser.parse(response))

def test_missing_required_name(parser):
    response = """
    <use_tool>
        <thoughts>no name provided</thoughts>
    </use_tool>
    """
    with pytest.raises(ValueError):
        list(parser.parse(response))

def test_nested_tools(parser):
    response = """
    <use_tool>
        <name>outer</name>
        <arg>
            <use_tool>
                <name>inner</name>
                <value>nested</value>
            </use_tool>
        </arg>
    </use_tool>
    """
    events = list(parser.parse(response))
    assert len(events) == 1  # Should only parse outer tool
    assert events[0].name == "outer"
    assert events[0].args == {"arg": "\n            <use_tool>\n                <name>inner</name>\n                <value>nested</value>\n            </use_tool>\n        "}

def test_whitespace_handling(parser):
    response = """<use_tool><name>compact</name><value>test</value></use_tool>"""
    events = list(parser.parse(response))
    assert len(events) == 1
    assert events[0].name == "compact"
    assert events[0].args == {"value": "test"}

def test_empty_tool(parser):
    response = """
    <use_tool>
    </use_tool>
    """
    with pytest.raises(ValueError):
        list(parser.parse(response))

def test_custom_tag(parser):
    custom_parser = XMLParser(tag="custom_tool")
    response = """
    <custom_tool>
        <name>test</name>
        <value>data</value>
    </custom_tool>
    """
    events = list(custom_parser.parse(response))
    assert len(events) == 1
    assert events[0].name == "test"
    assert events[0].args == {"value": "data"}
