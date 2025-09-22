import json
from unittest.mock import Mock

import pytest

from ai_agent_toolbox.toolbox import Toolbox, ToolConflictError
from ai_agent_toolbox.parser_event import ParserEvent
from ai_agent_toolbox.tool_use import ToolUse

def test_use_tool_happy_path():
    """
    Test that a tool is properly called when a tool event is passed
    and the function returns the correct result.
    """
    mock_fn = Mock(return_value="Called successfully")
    toolbox = Toolbox()
    toolbox.add_tool(
        name="thinking",
        fn=mock_fn,
        args={"thoughts": {"type": "string", "description": "some desc"}},
        description="dummy desc"
    )
    event = ParserEvent(
        type="tool",
        mode="close",
        id="test-id",
        tool=ToolUse(name="thinking", args={"thoughts": "test thoughts"}),
        is_tool_call=True
    )

    result = toolbox.use(event)
    mock_fn.assert_called_once_with(thoughts="test thoughts")
    assert result.result == "Called successfully"


def test_use_tool_missing_tool():
    """
    Test behavior when a tool call references a tool name that's not in the toolbox.
    Expecting None as the result.
    """
    toolbox = Toolbox()

    event = ParserEvent(
        type="tool",
        mode="close",
        id="test-id",
        tool=ToolUse(name="missing_tool", args={"arg": "val"}),
        is_tool_call=True
    )
    result = toolbox.use(event)
    assert result is None


def test_use_event_not_a_tool_call():
    """
    Test that if an event is not a tool call, Toolbox.use returns None
    and does not attempt to invoke anything.
    """
    toolbox = Toolbox()
    event = ParserEvent(
        type="text",
        mode="close",
        id="text-id",
        is_tool_call=False
    )

    result = toolbox.use(event)
    assert result is None


def test_use_tool_raising_exception():
    """
    Test that if the tool function itself raises an exception, the
    Toolbox.use method does not catch it and allows it to propagate.
    """
    def error_fn(**kwargs):
        raise ValueError("Simulated tool error")

    toolbox = Toolbox()
    toolbox.add_tool(
        name="error_tool",
        fn=error_fn,
        args={"arg1": {"type": "string", "description": "Some arg"}},
        description="A tool that errors when called"
    )

    event = ParserEvent(
        type="tool",
        mode="close",
        id="test-id",
        tool=ToolUse(name="error_tool", args={"arg1": "some_value"}),
        is_tool_call=True
    )

    with pytest.raises(ValueError, match="Simulated tool error"):
        toolbox.use(event)

def test_tool_conflict_error():
    toolbox = Toolbox()
    toolbox.add_tool(name="test", fn=lambda x: x, args={}, description="")
    with pytest.raises(ToolConflictError):
        toolbox.add_tool(name="test", fn=lambda x: x, args={}, description="")

def test_type_conversion():
    toolbox = Toolbox()
    toolbox.add_tool(
        name="converter",
        fn=lambda **x: x,
        args={
            "int_arg": {"type": "int"},
            "float_arg": {"type": "float"},
            "bool_arg": {"type": "bool"}
        }
    )
    
    event = ParserEvent(
        type="tool",
        mode="close",
        id="test-id",
        tool=ToolUse(
            name="converter",
            args={
                "int_arg": "42",
                "float_arg": "3.14",
                "bool_arg": "true"
            }
        ),
        is_tool_call=True
    )
    
    response = toolbox.use(event)
    assert response.result == {
        "int_arg": 42,
        "float_arg": 3.14,
        "bool_arg": True
    }


def test_composite_type_conversion():
    toolbox = Toolbox()
    toolbox.add_tool(
        name="composite",
        fn=lambda **kwargs: kwargs,
        args={
            "items": {"type": "list"},
            "config": {"type": "dict"},
            "mode": {"type": "enum", "choices": ["fast", "slow"]},
        },
    )

    event = ParserEvent(
        type="tool",
        mode="close",
        id="test-id",
        tool=ToolUse(
            name="composite",
            args={
                "items": "[1, 2, 3]",
                "config": '{"threshold": 0.7}',
                "mode": "fast",
            },
        ),
        is_tool_call=True,
    )

    response = toolbox.use(event)
    assert response.result == {
        "items": [1, 2, 3],
        "config": {"threshold": 0.7},
        "mode": "fast",
    }


def test_invalid_json_for_list_raises_error():
    toolbox = Toolbox()
    toolbox.add_tool(
        name="broken",
        fn=lambda **kwargs: kwargs,
        args={"items": {"type": "list"}},
    )

    event = ParserEvent(
        type="tool",
        mode="close",
        id="test-id",
        tool=ToolUse(name="broken", args={"items": "not-json"}),
        is_tool_call=True,
    )

    with pytest.raises(ValueError):
        toolbox.use(event)


def test_schema_validation_enforced():
    toolbox = Toolbox()
    toolbox.add_tool(
        name="validator",
        fn=lambda **kwargs: kwargs,
        args={
            "count": {"type": "int", "min": 1, "max": 3},
            "mode": {"type": "enum", "choices": ["fast", "slow"]},
        },
    )

    invalid_min = ParserEvent(
        type="tool",
        mode="close",
        id="test-id",
        tool=ToolUse(name="validator", args={"count": "0", "mode": "fast"}),
        is_tool_call=True,
    )

    with pytest.raises(ValueError, match="less than minimum"):
        toolbox.use(invalid_min)

    invalid_max = ParserEvent(
        type="tool",
        mode="close",
        id="test-id",
        tool=ToolUse(name="validator", args={"count": "5", "mode": "fast"}),
        is_tool_call=True,
    )

    with pytest.raises(ValueError, match="exceeds maximum"):
        toolbox.use(invalid_max)

    invalid_choice = ParserEvent(
        type="tool",
        mode="close",
        id="test-id",
        tool=ToolUse(name="validator", args={"count": "2", "mode": "medium"}),
        is_tool_call=True,
    )

    with pytest.raises(ValueError, match="allowed choices"):
        toolbox.use(invalid_choice)


def test_custom_parser_invoked():
    parser = Mock(side_effect=lambda payload: {item["key"]: item["value"] for item in payload})

    toolbox = Toolbox()
    toolbox.add_tool(
        name="custom",
        fn=lambda **kwargs: kwargs,
        args={
            "payload": {
                "type": "list",
                "parser": parser,
                "choices": [
                    {"a": 1, "b": 2}
                ],
            }
        },
    )

    event = ParserEvent(
        type="tool",
        mode="close",
        id="test-id",
        tool=ToolUse(
            name="custom",
            args={
                "payload": json.dumps([
                    {"key": "a", "value": 1},
                    {"key": "b", "value": 2},
                ])
            },
        ),
        is_tool_call=True,
    )

    response = toolbox.use(event)
    parser.assert_called_once()
    assert parser.call_args[0][0] == [
        {"key": "a", "value": 1},
        {"key": "b", "value": 2},
    ]
    assert response.result == {"payload": {"a": 1, "b": 2}}
