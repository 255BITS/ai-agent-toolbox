import pytest
from ai_agent_toolbox.parsers.markdown.markdown_parser import MarkdownParser
from ai_agent_toolbox.parser_event import ParserEvent, ToolUse

# --- Assertion Helpers ---

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
    assert event.content == expected_content

# --- Non-streaming Tests ---

def test_no_code_fence():
    parser = MarkdownParser()
    text = "This is plain text with no code fences."
    events = list(parser.parse(text))
    # Expect a single text block.
    assert len(events) == 3
    create, append, close = events
    assert_text_create(create)
    text_id = create.id
    assert_text_append(append, text_id, "This is plain text with no code fences.")
    assert_text_close(close, text_id)

def test_single_code_fence():
    parser = MarkdownParser()
    # Code block with language identifier "python"
    text = "Hello world. \n```python\nprint('hi')\n``` Goodbye."
    events = list(parser.parse(text))
    # Expected:
    # - A text block for "Hello world. \n"
    # - A tool block for the code fence (tool name "python") containing "print('hi')\n"
    # - A text block for " Goodbye."
    # In total, 9 events.
    assert len(events) == 9

    # First text block.
    assert_text_create(events[0])
    text_id1 = events[0].id
    assert_text_append(events[1], text_id1, "Hello world. \n")
    assert_text_close(events[2], text_id1)

    # Tool block.
    assert_tool_create(events[3])
    tool_id = events[3].id
    # The tool content may be appended in one or more pieces.
    assert_tool_append(events[4], tool_id, "print('hi')\n")
    assert_tool_close(events[5], tool_id, "python", "print('hi')\n")

    # Final text block.
    assert_text_create(events[6])
    text_id2 = events[6].id
    assert_text_append(events[7], text_id2, " Goodbye.")
    assert_text_close(events[8], text_id2)

def test_multiple_code_fences():
    parser = MarkdownParser()
    text = "```diff\n- line1\n+ line2\n``````python\nprint('code')\n```"
    events = list(parser.parse(text))
    # There are two tool blocks back-to-back.
    # First tool: language "diff", content "- line1\n+ line2\n"
    # Second tool: language "python", content "print('code')\n"
    # Total events: 3 events for each tool = 6.
    assert len(events) == 6

    # First tool block.
    assert_tool_create(events[0])
    tool_id1 = events[0].id
    assert_tool_append(events[1], tool_id1, "- line1\n+ line2\n")
    assert_tool_close(events[2], tool_id1, "diff", "- line1\n+ line2\n")

    # Second tool block.
    assert_tool_create(events[3])
    tool_id2 = events[3].id
    assert_tool_append(events[4], tool_id2, "print('code')\n")
    assert_tool_close(events[5], tool_id2, "python", "print('code')\n")


def test_nested_backticks():
    text = """```diff
--- a/README.md
+++ b/README.md
@@
-# GPTDiff
-```
-bash
-gptdiff
-```
```"""
    parser = MarkdownParser()
    events = list(parser.parse(text))
    tool_id = events[1].id
    assert_tool_append(events[1], tool_id, text.replace("```diff", "")[:-3])
    assert len(events) == 3

def test_interleaved_text_and_code():
    parser = MarkdownParser()
    text = "Start text\n```bash\necho 'run'\n```\nEnd text"
    events = list(parser.parse(text))
    # Expected:
    # - Text block ("Start text\n")
    # - Tool block with language "bash" and content "echo 'run'\n"
    # - Text block ("End text")
    assert len(events) == 9

    # First text block.
    assert_text_create(events[0])
    text_id1 = events[0].id
    assert_text_append(events[1], text_id1, "Start text\n")
    assert_text_close(events[2], text_id1)

    # Tool block.
    assert_tool_create(events[3])
    tool_id = events[3].id
    assert_tool_append(events[4], tool_id, "echo 'run'\n")
    assert_tool_close(events[5], tool_id, "bash", "echo 'run'\n")

    # Second text block.
    assert_text_create(events[6])
    text_id2 = events[6].id
    assert_text_append(events[7], text_id2, "End text")
    assert_text_close(events[8], text_id2)

def test_unclosed_code_fence():
    parser = MarkdownParser()
    text = "Before code\n```python\nincomplete code"
    events = list(parser.parse(text))
    events.extend(parser.flush())
    # Expect:
    # - Text block: "Before code\n"
    # - Tool block for "python", force-closed with content "incomplete code"
    # Our MarkdownParser produces 6 events in this case.
    assert len(events) >= 6

    # First text block.
    assert_text_create(events[0])
    text_id = events[0].id
    assert_text_append(events[1], text_id, "Before code\n")
    assert_text_close(events[2], text_id)

    # Tool block.
    assert_tool_create(events[3])
    tool_id = events[3].id
    # There should be an append event for the incomplete code.
    assert_tool_append(events[4], tool_id, "incomplete code")
    # The flush() should have closed the tool.
    assert_tool_close(events[5], tool_id, "python", "incomplete code")

# --- Streaming Tests ---

def test_streaming_partial_open_fence():
    parser = MarkdownParser()
    # Split the opening fence across chunks.
    chunks = [
        "Text before\n``",
        "`python\nprint('partial')\n``` After"
    ]
    all_events = []
    for chunk in chunks:
        all_events.extend(parser.parse_chunk(chunk))
    all_events.extend(parser.flush())

    # Expect a text block for "Text before\n", a tool block for python, and a text block for " After"
    # Verify text before.
    text_events = [e for e in all_events if e.type == "text" and e.mode == "append"]
    assert any("Text before" in e.content for e in text_events)
    # Verify tool block.
    tool_closes = [e for e in all_events if e.mode == "close" and e.type == "tool" and e.is_tool_call]
    assert len(tool_closes) == 1
    assert tool_closes[0].tool.name == "python"
    assert tool_closes[0].content == "print('partial')\n"
    # Verify text after.
    assert any(" After" in e.content for e in text_events)

def test_streaming_split_across_chunks():
    parser = MarkdownParser()
    chunks = [
        "Start\n```bash\necho 'hello",
        " world'\n```End"
    ]
    all_events = []
    for chunk in chunks:
        all_events.extend(parser.parse_chunk(chunk))
    all_events.extend(parser.flush())

    # Expect:
    # - Text block: "Start\n"
    # - Tool block: language "bash" with content "echo 'hello world'\n"
    # - Text block: "End"
    # Check tool block.
    tool_closes = [e for e in all_events if e.mode == "close" and e.type == "tool" and e.is_tool_call]
    assert len(tool_closes) == 1
    assert tool_closes[0].tool.name == "bash"
    assert tool_closes[0].content == "echo 'hello world'\n"
