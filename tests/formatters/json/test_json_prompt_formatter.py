from ai_agent_toolbox.formatters.json.json_prompt_formatter import JSONPromptFormatter
from ai_agent_toolbox.toolbox import Toolbox


def test_json_prompt_formatter_outputs_example_payload():
    formatter = JSONPromptFormatter()
    prompt = formatter.format_prompt(
        {
            "search": {
                "description": "Web search tool",
                "args": {
                    "query": {"type": "string", "description": "Search keywords"},
                    "limit": {"type": "int", "description": "Max results"},
                },
            }
        }
    )

    assert '"type": "tool_call"' in prompt
    assert '"name": "search"' in prompt
    assert '"query"' in prompt
    assert '"limit"' in prompt


def test_json_prompt_formatter_usage_prompt_from_toolbox():
    toolbox = Toolbox()

    def fetch(location: str) -> str:
        return f"Weather for {location}"

    toolbox.add_tool(
        name="get_weather",
        fn=fetch,
        args={"location": {"type": "string", "description": "City to inspect"}},
        description="Fetches the weather",
    )

    formatter = JSONPromptFormatter()
    usage = formatter.usage_prompt(toolbox)

    assert '"name": "get_weather"' in usage
    assert '"location"' in usage
