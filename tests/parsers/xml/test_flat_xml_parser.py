import pytest
from ai_agent_toolbox.parsers.xml.flat_xml_parser import FlatXMLParser
from ai_agent_toolbox.parser_event import ParserEvent

def assert_text_create(event: ParserEvent):
    assert event.type == "text"
    assert event.mode == "create"
    assert event.id is not None

def assert_text_append(event: ParserEvent, text_id: str, content: str):
    assert event.type == "text"
    assert event.mode == "append"
    assert event.id == text_id
    assert event.content == content

def assert_text_close(event: ParserEvent, text_id: str):
    assert event.type == "text"
    assert event.mode == "close"
    assert event.id == text_id

def assert_tool_create(event: ParserEvent):
    assert event.type == "tool"
    assert event.mode == "create"
    assert event.id is not None

def assert_tool_append(event: ParserEvent, tool_id: str, content: str):
    assert event.type == "tool"
    assert event.mode == "append"
    assert event.id == tool_id
    assert event.content == content

def assert_tool_close(event: ParserEvent, tool_id: str, expected_name: str, expected_content: str):
    assert event.type == "tool"
    assert event.mode == "close"
    assert event.id == tool_id
    assert event.is_tool_call
    assert event.tool is not None
    assert event.tool.name == expected_name
    # The parser doesn't store sub-args, but sets content to the entire text inside the tag
    assert event.content == expected_content

def test_no_tags():
    parser = FlatXMLParser("think", "action")
    text = "This text has no tags at all."
    events = list(parser.parse(text))
    # Expect: text create, text append, text close
    assert len(events) == 3
    
    e1, e2, e3 = events
    assert_text_create(e1)
    text_id = e1.id
    assert_text_append(e2, text_id, "This text has no tags at all.")
    assert_text_close(e3, text_id)

def test_single_tag():
    parser = FlatXMLParser("think", "action")
    text = "hello <think>I should say be enthusiastic</think> goodbye"
    events = list(parser.parse(text))
    # Expect:
    # 1) text create
    # 2) text append("hello ")
    # 3) text close
    # 4) tool create
    # 5) tool append("I should say be enthusiastic")
    # 6) tool close
    # 7) text create
    # 8) text append(" goodbye")
    # 9) text close
    assert len(events) == 9
    
    # Check the first text block
    assert_text_create(events[0])
    text_id_1 = events[0].id
    assert_text_append(events[1], text_id_1, "hello ")
    assert_text_close(events[2], text_id_1)
    
    # Check the recognized tag
    assert_tool_create(events[3])
    tool_id = events[3].id
    assert_tool_append(events[4], tool_id, "I should say be enthusiastic")
    assert_tool_close(events[5], tool_id, "think", "I should say be enthusiastic")
    
    # Final text block
    assert_text_create(events[6])
    text_id_2 = events[6].id
    assert_text_append(events[7], text_id_2, " goodbye")
    assert_text_close(events[8], text_id_2)

def test_multiple_tags():
    parser = FlatXMLParser("think", "action")
    text = "<think>Be bold</think><action>wave vigorously</action>"
    events = list(parser.parse(text))
    # Expect: 3 events for <think>, then 3 for <action> => total 6
    assert len(events) == 6
    
    # <think> events
    assert_tool_create(events[0])
    tool_id_1 = events[0].id
    assert_tool_append(events[1], tool_id_1, "Be bold")
    assert_tool_close(events[2], tool_id_1, "think", "Be bold")
    
    # <action> events
    assert_tool_create(events[3])
    tool_id_2 = events[3].id
    assert_tool_append(events[4], tool_id_2, "wave vigorously")
    assert_tool_close(events[5], tool_id_2, "action", "wave vigorously")

def test_interleaved_text():
    parser = FlatXMLParser("think", "action")
    text = "Intro <think>One</think> Middle <action>Two</action> End"
    events = list(parser.parse(text))
    # We'll have:
    # 1) text create
    # 2) text append("Intro ")
    # 3) text close
    # 4) tool create (think)
    # 5) tool append("One")
    # 6) tool close
    # 7) text create
    # 8) text append(" Middle ")
    # 9) text close
    # 10) tool create (action)
    # 11) tool append("Two")
    # 12) tool close
    # 13) text create
    # 14) text append(" End")
    # 15) text close
    assert len(events) == 15
    
    # Intro text
    e1, e2, e3 = events[0], events[1], events[2]
    assert_text_create(e1)
    text_id_1 = e1.id
    assert_text_append(e2, text_id_1, "Intro ")
    assert_text_close(e3, text_id_1)

    # <think>One</think>
    e4, e5, e6 = events[3], events[4], events[5]
    assert_tool_create(e4)
    tool_id_1 = e4.id
    assert_tool_append(e5, tool_id_1, "One")
    assert_tool_close(e6, tool_id_1, "think", "One")
    
    # Middle text
    e7, e8, e9 = events[6], events[7], events[8]
    assert_text_create(e7)
    text_id_2 = e7.id
    assert_text_append(e8, text_id_2, " Middle ")
    assert_text_close(e9, text_id_2)
    
    # <action>Two</action>
    e10, e11, e12 = events[9], events[10], events[11]
    assert_tool_create(e10)
    tool_id_2 = e10.id
    assert_tool_append(e11, tool_id_2, "Two")
    assert_tool_close(e12, tool_id_2, "action", "Two")

    # Ending text
    e13, e14, e15 = events[12], events[13], events[14]
    assert_text_create(e13)
    text_id_3 = e13.id
    assert_text_append(e14, text_id_3, " End")
    assert_text_close(e15, text_id_3)

def test_unclosed_tag():
    parser = FlatXMLParser("think", "action")
    text = "<think>Partially closed"
    events = list(parser.parse(text))
    # We get 3 events for this recognized tag: create, append, close
    assert len(events) == 3
    
    # <think> events
    e1, e2, e3 = events
    assert_tool_create(e1)
    tool_id = e1.id
    assert_tool_append(e2, tool_id, "Partially closed")
    # content is "Partially closed"
    assert_tool_close(e3, tool_id, "think", "Partially closed")

def test_unknown_tag():
    parser = FlatXMLParser("think", "action")
    text = "<unknown>Not captured</unknown> <think>Captured</think>"
    events = list(parser.parse(text))
    # The <unknown>... is considered plain text because "unknown" isn't recognized
    # So we expect:
    #   text create/append/close => entire string "<unknown>Not captured</unknown> "
    #   then 3 events for <think>
    assert len(events) == 6

    # text block (for the unknown tag chunk)
    e1, e2, e3 = events[0], events[1], events[2]
    assert_text_create(e1)
    text_id_1 = e1.id
    assert_text_append(e2, text_id_1, "<unknown>Not captured</unknown> ")
    assert_text_close(e3, text_id_1)

    # recognized <think> tag
    e4, e5, e6 = events[3], events[4], events[5]
    assert_tool_create(e4)
    tool_id = e4.id
    assert_tool_append(e5, tool_id, "Captured")
    assert_tool_close(e6, tool_id, "think", "Captured")
