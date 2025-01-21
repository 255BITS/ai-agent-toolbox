import pytest
from ai_agent_toolbox import FlatXMLParser

def test_no_tags():
    parser = FlatXMLParser("think", "action")
    text = "This text has no tags at all."
    events = parser.parse(text)
    assert len(events) == 1
    assert events[0]["type"] == "text"
    assert events[0]["content"] == text

def test_single_tag():
    parser = FlatXMLParser("think", "action")
    text = "hello <think>I should say be enthusiastic</think> goodbye"
    events = parser.parse(text)
    assert len(events) == 3
    assert events[0] == {"type": "text", "content": "hello "}
    assert events[1] == {"type": "think", "content": "I should say be enthusiastic"}
    assert events[2] == {"type": "text", "content": " goodbye"}

def test_multiple_tags():
    parser = FlatXMLParser("think", "action")
    text = "<think>Be bold</think><action>wave vigorously</action>"
    events = parser.parse(text)
    assert len(events) == 2
    assert events[0] == {"type": "think", "content": "Be bold"}
    assert events[1] == {"type": "action", "content": "wave vigorously"}

def test_interleaved_text():
    parser = FlatXMLParser("think", "action")
    text = "Intro <think>One</think> Middle <action>Two</action> End"
    events = parser.parse(text)
    # events: [text("Intro "), think("One"), text(" Middle "), action("Two"), text(" End")]
    assert len(events) == 5
    assert events[0] == {"type": "text", "content": "Intro "}
    assert events[1] == {"type": "think", "content": "One"}
    assert events[2] == {"type": "text", "content": " Middle "}
    assert events[3] == {"type": "action", "content": "Two"}
    assert events[4] == {"type": "text", "content": " End"}

def test_unclosed_tag():
    parser = FlatXMLParser("think", "action")
    text = "<think>Partially closed"
    events = parser.parse(text)
    # We expect one "think" event with content "Partially closed"
    assert len(events) == 1
    assert events[0] == {"type": "think", "content": "Partially closed"}

def test_unknown_tag():
    parser = FlatXMLParser("think", "action")
    text = "<unknown>Not captured</unknown> <think>Captured</think>"
    events = parser.parse(text)
    # The <unknown> tag will be ignored as a tag, so it's seen as normal text
    assert len(events) == 2
    assert events[0]["type"] == "text"
    # Confirm that the text includes the entire <unknown>...</unknown> portion
    assert events[0]["content"] == "<unknown>Not captured</unknown> "
    assert events[1] == {"type": "think", "content": "Captured"}
