import json

from ai_agent_toolbox.parsers.json.json_parser import JSONParser


def collect(events, *, type_, mode):
    return [event for event in events if event.type == type_ and event.mode == mode]


def test_json_parser_one_shot_openai_payload():
    parser = JSONParser()
    payload = json.dumps(
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Thinking..."},
                {
                    "type": "tool_call",
                    "id": "call_123",
                    "function": {
                        "name": "get_weather",
                        "arguments": {"location": "Paris", "unit": "celsius"},
                    },
                },
            ],
        }
    )

    events = parser.parse(payload)

    text_content = "".join(event.content for event in collect(events, type_="text", mode="append"))
    assert text_content == "Thinking..."

    tool_creates = collect(events, type_="tool", mode="create")
    assert tool_creates and tool_creates[0].content == "get_weather"

    tool_closes = collect(events, type_="tool", mode="close")
    assert len(tool_closes) == 1
    close_event = tool_closes[0]
    assert close_event.is_tool_call
    assert close_event.tool.name == "get_weather"
    assert close_event.tool.args == {"location": "Paris", "unit": "celsius"}


def test_json_parser_streaming_openai_tool_call():
    parser = JSONParser()
    chunks = [
        'data: {"type":"response.delta","delta":{"content":[{"type":"output_text","text":"Working on it"}]}}\n\n',
        'data: {"type":"response.delta","delta":{"tool_calls":[{"id":"call_1","type":"function","function":{"name":"get_weather"}}]}}\n\n',
        'data: {"type":"response.delta","delta":{"tool_calls":[{"id":"call_1","type":"function","function":{"arguments":"{\\"location\\":\\"Boston\\""}}]}}\n\n',
        'data: {"type":"response.delta","delta":{"tool_calls":[{"id":"call_1","type":"function","function":{"arguments":"}"}}]}}\n\n',
        'data: {"type":"response.completed"}\n\n',
    ]

    all_events = []
    for chunk in chunks:
        all_events.extend(parser.parse_chunk(chunk))

    # flush should not emit duplicates but should be safe
    all_events.extend(parser.flush())

    text_chunks = collect(all_events, type_="text", mode="append")
    assert "".join(event.content for event in text_chunks) == "Working on it"

    tool_creates = collect(all_events, type_="tool", mode="create")
    assert tool_creates and tool_creates[0].content == "get_weather"

    tool_appends = collect(all_events, type_="tool", mode="append")
    assert [event.content for event in tool_appends] == ['{"location":"Boston"', '}']

    tool_closes = collect(all_events, type_="tool", mode="close")
    assert len(tool_closes) == 1
    close_event = tool_closes[0]
    assert close_event.tool.args == {"location": "Boston"}


def test_json_parser_streaming_anthropic_tool_use():
    parser = JSONParser()
    chunks = [
        json.dumps(
            {
                "type": "content_block_start",
                "index": 0,
                "content_block": {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "get_weather",
                    "input": {},
                },
            }
        )
        + "\n",
        json.dumps(
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {
                    "type": "input_json",
                    "partial_json": '{"location":"Rome"',
                },
            }
        )
        + "\n",
        json.dumps(
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {
                    "type": "input_json",
                    "partial_json": "}",
                },
            }
        )
        + "\n",
        json.dumps({"type": "content_block_stop", "index": 0}) + "\n",
    ]

    all_events = []
    for chunk in chunks:
        all_events.extend(parser.parse_chunk(chunk))

    all_events.extend(parser.flush())

    tool_creates = collect(all_events, type_="tool", mode="create")
    assert tool_creates and tool_creates[0].content == "get_weather"

    tool_appends = collect(all_events, type_="tool", mode="append")
    assert tool_appends[0].content == '{"location":"Rome"'
    assert tool_appends[1].content == "}"

    tool_closes = collect(all_events, type_="tool", mode="close")
    assert len(tool_closes) == 1
    close_event = tool_closes[0]
    assert close_event.tool.args == {"location": "Rome"}
