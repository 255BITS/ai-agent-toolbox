import pytest
from ai_agent_toolbox.formatters.xml.flat_xml_prompt_formatter import FlatXMLPromptFormatter

def test_single_tool_description():
    """Test that a single tool's description is included in the formatted prompt."""
    tools = {
        "test_tool": {
            "description": "A test description."
        }
    }
    formatter = FlatXMLPromptFormatter()
    prompt = formatter.format_prompt(tools)
    
    assert "Tool name: test_tool" in prompt
    assert "Description: A test description." in prompt
    assert "Argument: string" in prompt

def test_multiple_tools_descriptions():
    """Test formatting with multiple tools ensures all descriptions are present."""
    tools = {
        "tool1": {"description": "First tool"},
        "tool2": {"description": "Second tool"}
    }
    formatter = FlatXMLPromptFormatter()
    prompt = formatter.format_prompt(tools)
    
    assert "Tool name: tool1" in prompt
    assert "Description: First tool" in prompt
    assert "Tool name: tool2" in prompt
    assert "Description: Second tool" in prompt

def test_xml_tag_in_initial_line_and_example():
    """Test that the specified XML tag appears in the initial line and example."""
    formatter = FlatXMLPromptFormatter(tag="custom_tag")
    prompt = formatter.format_prompt({})
    
    assert "You can invoke the following tools using <custom_tag>:" in prompt
    assert "<custom_tag>" in prompt
    assert "</custom_tag>" in prompt

def test_example_structure():
    """Verify the example XML structure in the prompt."""
    formatter = FlatXMLPromptFormatter()
    prompt = formatter.format_prompt({})
    
    example_section = [
        "Example:",
        "<use_tool>",
        "arguments",
        "</use_tool>"
    ]
    for line in example_section:
        assert line in prompt

def test_usage_prompt_integration_with_toolbox():
    """Test that usage_prompt correctly uses the Toolbox's tools."""
    class MockToolbox:
        _tools = {
            "mock_tool": {"description": "Mock description"},
            "another_tool": {"description": "Another description"}
        }
    
    formatter = FlatXMLPromptFormatter()
    prompt = formatter.usage_prompt(MockToolbox())
    
    assert "Tool name: mock_tool" in prompt
    assert "Description: Mock description" in prompt
    assert "Tool name: another_tool" in prompt
    assert "Description: Another description" in prompt

def test_no_tools_prompt_structure():
    """Test prompt structure when no tools are provided."""
    formatter = FlatXMLPromptFormatter()
    prompt = formatter.format_prompt({})
    
    # Check essential components
    assert "You can invoke the following tools using <use_tool>:" in prompt
    assert "Example:" in prompt
    # Ensure no tool-specific lines are present
    assert "Tool name:" not in prompt
    assert "Description:" not in prompt
    assert "Argument: string" not in prompt

def test_argument_line_static_text():
    """Ensure 'Argument: string' is present for each tool regardless of actual args."""
    tools = {
        "tool_with_args": {
            "description": "Tool with arguments",
            "content": {"type": "string", "description": "test description"}
        }
    }
    formatter = FlatXMLPromptFormatter()
    prompt = formatter.format_prompt(tools)
    
    assert "Argument: string" in prompt
    assert "test description" in prompt
