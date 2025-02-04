import pytest
from ai_agent_toolbox.formatters.markdown.markdown_prompt_formatter import MarkdownPromptFormatter
from ai_agent_toolbox.toolbox import Toolbox

def test_basic_markdown_prompt_formatter():
    formatter = MarkdownPromptFormatter()
    toolbox = Toolbox()
    toolbox.add_tool(
        name="thinking",
        fn=lambda thoughts: f"Thinking: {thoughts}",
        args={
            "thoughts": {
                "type": "string",
                "description": "What you want to think about"
            }
        },
        description="For thinking out loud"
    )

    prompt = formatter.usage_prompt(toolbox)
    assert "You can invoke the following tools using Markdown code fences:" in prompt
    assert "**Tool name:** thinking" in prompt
    assert "**Description:** For thinking out loud" in prompt
    assert "- thoughts (string): What you want to think about" in prompt
    assert "```thinking" in prompt  # The example shows the fence with the tool name
    assert "    thoughts: value1" in prompt
    assert "```" in prompt

def test_markdown_prompt_formatter_multiple_args():
    formatter = MarkdownPromptFormatter(fence="```")
    toolbox = Toolbox()
    toolbox.add_tool(
        name="complex_tool",
        fn=lambda a, b, c: a + b + c,
        args={
            "arg_a": {"type": "string", "description": "First argument"},
            "arg_b": {"type": "integer", "description": "Second argument"},
            "arg_c": {"type": "boolean", "description": "Third argument"}
        },
        description="Tool with multiple arguments"
    )

    prompt = formatter.usage_prompt(toolbox)
    assert "**Tool name:** complex_tool" in prompt
    assert "- arg_a (string): First argument" in prompt
    assert "- arg_b (integer): Second argument" in prompt
    assert "- arg_c (boolean): Third argument" in prompt
    # Check that the example code fence starts with the tool name.
    assert "```complex_tool" in prompt
