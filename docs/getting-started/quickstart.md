# Quick Start Guide

## Basic Usage

1. Create a Toolbox:
```python
from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter

toolbox = Toolbox()
parser = XMLParser()
formatter = XMLPromptFormatter()
```

2. Define and Add Tools:
```python
def thinking(thoughts=""):
    print(f"Thinking: {thoughts}")

toolbox.add_tool(
    name="thinking",
    fn=thinking,
    args={
        "thoughts": {
            "type": "string",
            "description": "Thoughts to process"
        }
    },
    description="For thinking out loud"
)
```
3. Set up your system prompt:
```python

system = "You are a thoughtful AI.\n"
system += formatter.usage_prompt(toolbox) # Add the instructions to use the tools in the toolbox
prompt = "Think about something"
```

4. Parse the response:
```python
events = parser.parse(response)

for event in events:
    toolbox.use(event)
```

5. (optional) Use async streaming for calling tools ASAP:
```python
# Stream the response
async for chunk in anthropic_stream(system, prompt):
    for event in parser.parse_chunk(chunk):
        toolbox.use_async(event)

# Make sure to reset the parser and handle any unclosed tool tags
events = parser.flush()

# Optionally you can handle unclosed tool tags, or just ignore them
for event in events:
    toolbox.use_async(event)
```
