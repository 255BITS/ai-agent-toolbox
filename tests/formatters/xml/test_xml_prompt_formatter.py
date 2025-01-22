import pytest
from ai_agent_toolbox import XMLPromptFormatter
from ai_agent_toolbox.toolbox import Toolbox

def test_xml_prompt_formatter_basic():
    formatter = XMLPromptFormatter(tag="use_tool")
    toolbox = Toolbox()
    toolbox.add_tool(
        name="thinking",
        fn=lambda thoughts: f"Thinking: {thoughts}",
        args={
            "thoughts": {
                "type": "string",
                "description": "Anything you want to think about"
            }
        },
        description="For thinking out loud"
    )

    prompt = formatter.usage_prompt(toolbox)
    assert "You can invoke the following tools using <use_tool>:" in prompt
    assert "Tool name: thinking" in prompt
    assert "Description: For thinking out loud" in prompt
    assert "Arguments:" in prompt
    assert "thoughts (string): Anything you want to think about" in prompt
    assert "<use_tool>" in prompt
    assert "<name>tool_name</name>" in prompt
    assert "</use_tool>" in prompt

def test_xml_prompt_formatter_custom_tag():
    formatter = XMLPromptFormatter(tag="custom_tool_tag")
    toolbox = Toolbox()
    toolbox.add_tool(
        name="tool_with_custom_tag",
        fn=lambda x: x,
        args={},
        description="Tool for custom tag test"
    )

    prompt = formatter.usage_prompt(toolbox)
    assert "You can invoke the following tools using <custom_tool_tag>:" in prompt
    assert "<custom_tool_tag>" in prompt
    assert "</custom_tool_tag>" in prompt

def test_xml_prompt_formatter_no_tools():
    formatter = XMLPromptFormatter(tag="use_tool")
    toolbox = Toolbox()
    prompt = formatter.usage_prompt(toolbox)
    assert "You can invoke the following tools using <use_tool>:" in prompt
    assert "Tool name:" not in prompt # No tools, so no tool names should be listed

def test_xml_prompt_formatter_multiple_args():
    formatter = XMLPromptFormatter(tag="use_tool")
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
    assert "arg_a (string): First argument" in prompt
    assert "arg_b (integer): Second argument" in prompt
    assert "arg_c (boolean): Third argument" in prompt
