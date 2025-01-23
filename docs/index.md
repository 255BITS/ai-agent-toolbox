# AI Agent Toolbox

AI Agent Toolbox makes AI tool usage across models and frameworks easy. It works for parsing single use responses, or in agent and workflow loops.

## Key Features

* Native support for protocols such as Anthropic MCP
* Robust parsing with streaming support
* Support for read-write and write-only tools
* Framework compatible
* Model provider-agnostic

## Quick Example

```python
from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter

# Setup
toolbox = Toolbox()
parser = XMLParser(tag="use_tool")
formatter = XMLPromptFormatter(tag="use_tool")

def thinking(thoughts=""):
    print("I'm thinking:", thoughts)

# Add tools to your toolbox
toolbox.add_tool(
    name="thinking",
    fn=thinking,
    args={
        "thoughts": {
            "type": "string",
            "description": "Anything you want to think about"
        }
    },
    description="For thinking out loud"
)

system = "You are a thinking AI. You have interesting thoughts."
prompt = "Think about something interesting."

# Add our usage prompt
system += formatter.usage_prompt(toolbox)

response = llm_call(system_prompt=system, prompt=prompt)
events = parser.parse(response)

for event in events:
    toolbox.use(event)
```

There are many more examples in the `examples` folder, viewable on github - [link][https://github.com/255BITS/ai-agent-toolbox/examples].

## Getting Started

Check out our [Quick Start Guide](getting-started/quickstart.md) to begin using AI Agent Toolbox.
