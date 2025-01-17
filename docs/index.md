# AI Agent Toolbox

AI Agent Toolbox (AAT) makes AI tool usage across models and frameworks easy. It works for parsing single use responses, or in agent and workflow loops.

## Key Features

* Native support for protocols such as Anthropic MCP
* Robust parsing with streaming support
* Support for read-write and write-only tools
* Framework compatible
* Model provider-agnostic

## Quick Example

```python
from ai_agent_toolbox import Toolbox
from ai_agent_toolbox.parsers import XMLParser

toolbox = Toolbox()

# Add a simple thinking tool
toolbox.add_tool(
    name="thinking",
    fn=thinking,
    args={"thoughts": {"type": str}},
    description="For thinking out loud"
)

# Parse and execute tools
for event in parser.parse(ai_response):
    if event.is_tool_call:
        tool_result = toolbox.use(event.name, event.args)
```

## Getting Started

Check out our [Quick Start Guide](getting-started/quickstart.md) to begin using AI Agent Toolbox.
