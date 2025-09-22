import asyncio
import pytest
from unittest.mock import Mock

from ai_agent_toolbox.toolbox import Toolbox, ToolConflictError
from ai_agent_toolbox.parser_event import ParserEvent, ToolUse

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
    assert result.error is None


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
    assert result is not None
    assert result.result is None
    assert result.error == {
        "type": "unknown_tool",
        "message": "Tool 'missing_tool' is not registered."
    }


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
    assert response.error is None


def test_sync_tool_validation_success():
    toolbox = Toolbox()

    def sample_tool(topic: str, max_results: int, tone: str):
        return {
            "topic": topic,
            "max_results": max_results,
            "tone": tone,
        }

    toolbox.add_tool(
        name="research",
        fn=sample_tool,
        args={
            "topic": {"type": "string"},
            "max_results": {"type": "int", "required": False},
            "tone": {"type": "string", "required": False, "default": "neutral"},
        }
    )

    event = ParserEvent(
        type="tool",
        mode="close",
        id="event-id",
        tool=ToolUse(
            name="research",
            args={"topic": "LLMs", "max_results": "5", "tone": "curious"}
        ),
        is_tool_call=True,
    )

    response = toolbox.use(event)
    assert response.error is None
    assert response.result == {
        "topic": "LLMs",
        "max_results": 5,
        "tone": "curious",
    }


def test_sync_tool_missing_required_argument():
    toolbox = Toolbox()
    called = {"called": False}

    def sample_tool(topic: str):
        called["called"] = True
        return topic

    toolbox.add_tool(
        name="research",
        fn=sample_tool,
        args={"topic": {"type": "string"}},
    )

    event = ParserEvent(
        type="tool",
        mode="close",
        id="event-id",
        tool=ToolUse(name="research", args={}),
        is_tool_call=True,
    )

    response = toolbox.use(event)
    assert not called["called"]
    assert response.result is None
    assert response.error is not None
    assert response.error["type"] == "validation_error"
    assert response.error["message"] == "Argument validation failed."
    assert response.error["errors"][0]["field"] == "topic"
    assert response.error["errors"][0]["type"] == "missing"


def test_sync_tool_optional_argument_default():
    toolbox = Toolbox()
    recorded = {}

    def sample_tool(topic: str, max_results: int = 3):
        recorded["args"] = {"topic": topic, "max_results": max_results}
        return max_results

    toolbox.add_tool(
        name="research",
        fn=sample_tool,
        args={
            "topic": {"type": "string"},
            "max_results": {"type": "int", "required": False, "default": "7"},
        }
    )

    event = ParserEvent(
        type="tool",
        mode="close",
        id="event-id",
        tool=ToolUse(name="research", args={"topic": "LLMs"}),
        is_tool_call=True,
    )

    response = toolbox.use(event)
    assert response.error is None
    assert response.result == 7
    assert recorded["args"] == {"topic": "LLMs", "max_results": 7}


def test_async_tool_validation_success():
    toolbox = Toolbox()

    async def sample_tool(topic: str, max_results: int):
        return {
            "topic": topic,
            "max_results": max_results,
        }

    toolbox.add_tool(
        name="research_async",
        fn=sample_tool,
        args={
            "topic": {"type": "string"},
            "max_results": {"type": "int"},
        }
    )

    async def run():
        event = ParserEvent(
            type="tool",
            mode="close",
            id="event-id",
            tool=ToolUse(name="research_async", args={"topic": "LLMs", "max_results": "2"}),
            is_tool_call=True,
        )
        return await toolbox.use_async(event)

    response = asyncio.run(run())
    assert response.error is None
    assert response.result == {"topic": "LLMs", "max_results": 2}


def test_async_tool_missing_required_argument():
    toolbox = Toolbox()
    called = {"called": False}

    async def sample_tool(topic: str):
        called["called"] = True
        return topic

    toolbox.add_tool(
        name="research_async",
        fn=sample_tool,
        args={"topic": {"type": "string"}},
    )

    async def run():
        event = ParserEvent(
            type="tool",
            mode="close",
            id="event-id",
            tool=ToolUse(name="research_async", args={}),
            is_tool_call=True,
        )
        return await toolbox.use_async(event)

    response = asyncio.run(run())
    assert not called["called"]
    assert response.result is None
    assert response.error is not None
    assert response.error["type"] == "validation_error"
    assert response.error["errors"][0]["field"] == "topic"
    assert response.error["errors"][0]["type"] == "missing"


def test_async_tool_optional_argument_default():
    toolbox = Toolbox()
    recorded = {}

    async def sample_tool(topic: str, max_results: int = 3):
        recorded["args"] = {"topic": topic, "max_results": max_results}
        return max_results

    toolbox.add_tool(
        name="research_async",
        fn=sample_tool,
        args={
            "topic": {"type": "string"},
            "max_results": {"type": "int", "required": False, "default": "4"},
        }
    )

    async def run():
        event = ParserEvent(
            type="tool",
            mode="close",
            id="event-id",
            tool=ToolUse(name="research_async", args={"topic": "LLMs"}),
            is_tool_call=True,
        )
        return await toolbox.use_async(event)

    response = asyncio.run(run())
    assert response.error is None
    assert response.result == 4
    assert recorded["args"] == {"topic": "LLMs", "max_results": 4}
