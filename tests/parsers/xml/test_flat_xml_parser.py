import pytest
from ai_agent_toolbox.parsers.xml.flat_xml_parser import FlatXMLParser
from ai_agent_toolbox.parser_event import ParserEvent

@pytest.fixture
def parser():
    return FlatXMLParser("think", "action")


#
# Assertion Helpers
#
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


#
# Regular (non-streaming) Tests
#
def test_no_tags(parser):
    text = "This text has no tags at all."
    events = list(parser.parse(text))
    # Expect: text create, text append, text close
    assert len(events) == 3

    e1, e2, e3 = events
    assert_text_create(e1)
    text_id = e1.id
    assert_text_append(e2, text_id, "This text has no tags at all.")
    assert_text_close(e3, text_id)

def test_single_tag(parser):
    text = "hello <think>I should say be enthusiastic</think> goodbye"
    events = list(parser.parse(text))
    # Expect:
    #  1) text create
    #  2) text append("hello ")
    #  3) text close
    #  4) tool create
    #  5) tool append("I should say be enthusiastic")
    #  6) tool close
    #  7) text create
    #  8) text append(" goodbye")
    #  9) text close
    assert len(events) == 9

    # First text block
    assert_text_create(events[0])
    text_id_1 = events[0].id
    assert_text_append(events[1], text_id_1, "hello ")
    assert_text_close(events[2], text_id_1)

    # Recognized tag <think>
    assert_tool_create(events[3])
    tool_id = events[3].id
    assert_tool_append(events[4], tool_id, "I should say be enthusiastic")
    assert_tool_close(events[5], tool_id, "think", "I should say be enthusiastic")

    # Final text block
    assert_text_create(events[6])
    text_id_2 = events[6].id
    assert_text_append(events[7], text_id_2, " goodbye")
    assert_text_close(events[8], text_id_2)

def test_multiple_tags(parser):
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

def test_interleaved_text(parser):
    text = "Intro <think>One</think> Middle <action>Two</action> End"
    events = list(parser.parse(text))
    # We'll have:
    #  1) text create
    #  2) text append("Intro ")
    #  3) text close
    #  4) tool create(think)
    #  5) tool append("One")
    #  6) tool close
    #  7) text create
    #  8) text append(" Middle ")
    #  9) text close
    #  10) tool create(action)
    #  11) tool append("Two")
    #  12) tool close
    #  13) text create
    #  14) text append(" End")
    #  15) text close
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

    # End text
    e13, e14, e15 = events[12], events[13], events[14]
    assert_text_create(e13)
    text_id_3 = e13.id
    assert_text_append(e14, text_id_3, " End")
    assert_text_close(e15, text_id_3)

def test_unclosed_tag(parser):
    text = "<think>Partially closed"
    events = list(parser.parse(text))
    # We get 3 events for the recognized tag: create, append, close
    assert len(events) == 3

    e1, e2, e3 = events
    assert_tool_create(e1)
    tool_id = e1.id
    assert_tool_append(e2, tool_id, "Partially closed")
    assert_tool_close(e3, tool_id, "think", "Partially closed")

def test_unknown_tag(parser):
    text = "<unknown>Not captured</unknown> <think>Captured</think>"
    events = list(parser.parse(text))
    # The <unknown>... is considered plain text because "unknown" isn't recognized
    # So we expect:
    #   text create/append/close => entire string "<unknown>Not captured</unknown> "
    #   then 3 events for the recognized <think>
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

def test_nested_unknown_tags(parser):
    """Test that nested unknown tags are treated as plain text without parsing."""
    text = "<diff>outer<diff>inner</diff></diff>"
    events = list(parser.parse(text))
    # Should create a single text block containing the entire XML as text
    assert len(events) == 3

    e1, e2, e3 = events
    assert_text_create(e1)
    text_id = e1.id
    # The entire content including <diff> tag is captured as text
    assert_text_append(e2, text_id, "<diff>outer<diff>inner</diff></diff>")
    assert_text_close(e3, text_id)


#
# Streaming Tests
#
def test_streaming_partial_tag(parser):
    """Test parsing a tag split across multiple chunks."""
    chunk1 = "Hello <think>This is par"
    chunk2 = "tial content</think> bye"
    
    events1 = list(parser.parse_chunk(chunk1))
    events2 = list(parser.parse_chunk(chunk2))
    # After all chunks, flush to finalize
    events_flush = list(parser.flush())

    all_events = events1 + events2 + events_flush
    # Expect text create, append, close for "Hello "
    # Then tool create, append, append, close for <think>
    # Then text create, append, close for " bye"
    # => total 10 events

    assert len(all_events) == 10

    # Validate the first text block
    assert_text_create(all_events[0])
    text_id_1 = all_events[0].id
    assert_text_append(all_events[1], text_id_1, "Hello ")
    assert_text_close(all_events[2], text_id_1)

    # Tool block
    assert_tool_create(all_events[3])
    tool_id = all_events[3].id
    assert_tool_append(all_events[4], tool_id, "This is par")
    assert_tool_append(all_events[5], tool_id, "tial content")
    assert_tool_close(all_events[6], tool_id, "think", "This is partial content")

    # Final text block
    assert_text_create(all_events[7])
    text_id_2 = all_events[7].id
    assert_text_append(all_events[8], text_id_2, " bye")
    assert_text_close(all_events[9], text_id_2)

def test_streaming_split_across_chunks(parser):
    """Test recognized tags split across multiple chunks."""
    chunks = [
        "<think>Begin con",
        "tent</think><action>A",
        "ction content</action>"
    ]
    all_events = []
    for chunk in chunks:
        all_events.extend(parser.parse_chunk(chunk))
    all_events.extend(parser.flush())

    # We should end up with 3 events for <think> plus 3 events for <action> => 6
    # But also verify that the content is appended properly in pieces
    # Let's gather final tool close events to check content.
    think_close = [e for e in all_events if e.mode == "close" and e.type == "tool" and e.tool and e.tool.name == "think"]
    action_close = [e for e in all_events if e.mode == "close" and e.type == "tool" and e.tool and e.tool.name == "action"]

    assert len(think_close) == 1
    assert think_close[0].content == "Begin content"

    assert len(action_close) == 1
    assert action_close[0].content == "Action content"

def test_streaming_multiple_small_chunks(parser):
    """Test with many tiny character chunks for a single recognized tag."""
    text = "<think>Small chunk test</think>"
    chunks = list(text)  # Split into individual characters

    all_events = []
    for ch in chunks:
        all_events.extend(parser.parse_chunk(ch))
    all_events.extend(parser.flush())

    # We should see 3 events for <think>
    # Let's verify final content
    tool_closes = [e for e in all_events if e.mode == "close" and e.type == "tool"]
    assert len(tool_closes) == 1
    close_event = tool_closes[0]
    assert close_event.tool.name == "think"
    assert close_event.content == "Small chunk test"

def test_streaming_partial_start_tag(parser):
    """Test partial start tag completion across chunks."""
    chunks = [
        "Intro <thi",
        "nk>hello</think> outro"
    ]

    all_events = []
    for chunk in chunks:
        all_events.extend(parser.parse_chunk(chunk))
    all_events.extend(parser.flush())

    # We expect text block for "Intro " then a tool block for <think>, then another text block " outro"
    # So at minimum 9 events in total. Check the final tool's content.
    tool_closes = [e for e in all_events if e.mode == "close" and e.type == "tool"]
    assert len(tool_closes) == 1
    close_event = tool_closes[0]
    assert close_event.tool.name == "think"
    assert close_event.content == "hello"

def test_streaming_back_to_back_tags(parser):
    """Test consecutive recognized tags across chunks."""
    chunks = [
        "<think>One</think>",
        "<action>Two</action>"
    ]

    all_events = []
    for chunk in chunks:
        all_events.extend(parser.parse_chunk(chunk))
    all_events.extend(parser.flush())

    think_closes = [e for e in all_events if e.mode == "close" and e.type == "tool" and e.tool.name == "think"]
    action_closes = [e for e in all_events if e.mode == "close" and e.type == "tool" and e.tool.name == "action"]
    assert len(think_closes) == 1
    assert len(action_closes) == 1
    assert think_closes[0].content == "One"
    assert action_closes[0].content == "Two"

def test_streaming_unclosed_tag(parser):
    """Test flush() completes partial recognized tag parse."""
    chunks = [
        "Start <think>some partial con",
        "tent"
    ]

    all_events = []
    for chunk in chunks:
        all_events.extend(parser.parse_chunk(chunk))
    all_events.extend(parser.flush())  # Force completion

    # We should have ended with a forced close of the <think> tag
    tool_closes = [e for e in all_events if e.type == "tool" and e.mode == "close"]
    assert len(tool_closes) == 1
    assert tool_closes[0].tool.name == "think"
    assert tool_closes[0].content == "some partial content"