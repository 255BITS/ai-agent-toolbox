"""Example showing how to use JSONParser with synchronous and streaming payloads."""

import json
from ai_agent_toolbox import JSONParser, JSONPromptFormatter, Toolbox

# Step 1: register a tool the model can call.
toolbox = Toolbox()


def get_weather(location: str, unit: str = "celsius") -> str:
    """Return a pretend weather report for the requested location."""
    return f"Pretend forecast for {location} (unit: {unit})."


toolbox.add_tool(
    name="get_weather",
    fn=get_weather,
    args={
        "location": {
            "type": "string",
            "description": "City to look up",
        },
        "unit": {
            "type": "string",
            "description": "Temperature unit (celsius or fahrenheit)",
        },
    },
    description="Looks up weather information for a city.",
)

# Step 2: build the system prompt that teaches the model how to call tools.
formatter = JSONPromptFormatter()
system_prompt = (
    "You are a weather assistant. "
    "Return JSON tool calls when you need live data.\n"
)
system_prompt += formatter.usage_prompt(toolbox)

print("System prompt sent to the model:\n")
print(system_prompt)
print()


def handle_events(events):
    """Utility helper that prints model text and executes tool calls."""
    for event in events:
        if event.type == "text" and event.mode == "append":
            print(f"MODEL> {event.content}")
        elif event.is_tool_call and event.mode == "close":
            print(f"TOOL CALL -> {event.tool.name}({json.dumps(event.tool.args)})")
            tool_result = toolbox.use(event)
            if tool_result is not None:
                print(f"TOOL RESULT -> {tool_result.result}")


print("=== Complete JSON payload ===")
non_streaming_payload = {
    "role": "assistant",
    "content": [
        {"type": "text", "text": "Let me look that up for you."},
        {
            "type": "tool_call",
            "id": "call_123",
            "function": {
                "name": "get_weather",
                "arguments": {"location": "Paris", "unit": "celsius"},
            },
        },
        {"type": "text", "text": "I'll report back with the results."},
    ],
}
print(json.dumps(non_streaming_payload, indent=4))
parser = JSONParser()
handle_events(parser.parse(json.dumps(non_streaming_payload)))
print()

print("=== Streaming JSON payload (SSE style chunks) ===")
streaming_parser = JSONParser()
streaming_chunks = [
    "data: "
    + json.dumps(
        {
            "type": "response.delta",
            "delta": {
                "content": [
                    {
                        "type": "output_text",
                        "text": "Checking live weather data...",
                    }
                ]
            },
        }
    )
    + "\n\n",
    "data: "
    + json.dumps(
        {
            "type": "response.delta",
            "delta": {
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "get_weather"},
                    }
                ]
            },
        }
    )
    + "\n\n",
    "data: "
    + json.dumps(
        {
            "type": "response.delta",
            "delta": {
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"arguments": '{"location":"Berlin"'},
                    }
                ]
            },
        }
    )
    + "\n\n",
    "data: "
    + json.dumps(
        {
            "type": "response.delta",
            "delta": {
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"arguments": "}"},
                    }
                ]
            },
        }
    )
    + "\n\n",
    "data: " + json.dumps({"type": "response.completed"}) + "\n\n",
]
for index, chunk in enumerate(streaming_chunks, start=1):
    print(f"-- chunk {index} --")
    print(chunk.strip())
    handle_events(streaming_parser.parse_chunk(chunk))

handle_events(streaming_parser.flush())
