# AI Agent Toolbox

TODO LOGO

AI Agent Toolbox is a set of tools that allow for easy AI Tool usage across models and frameworks. While the focus is on AI agents, AI Agent Toolbox works for any use case that requires Tool use.

## Features

* Native support protocols such as Anthropic MCP(link)
* Robust parsing
* Support for write-only tools and also tools that use responses
* Framework compatible
* Model provider-agnostic - supports Anthropic, OpenAI, Groq, Ollama, Hyperbolic, NanoGPT, and more

## Comparison

| Feature | AI Agent Toolbox | Raw Provider Tools | Other Solutions |
|---------|-----------------|-------------------|-----------------|
| Cross-platform | ✅ | ❌ | Varies |
| Native Support | ✅ | ✅ | ❌ |
| Read-Write Tools | ✅ | Varies | ❌ |
| Streaming | ✅ | Varies | ❌ |

## Installation

```
pip install ai-agent-toolbox(TODO)
```

## Usage

Add a thinking Tool.

### Asynchronous

```python
from ai_agent_toolbox import Toolbox
from ai_agent_toolbox.tools import Tool
from ai_agent_toolbox.parsers import XMLParser

# Your workbench setup
toolbox = Toolbox()
parser = XMLParser(tag="use_tool")

# Adding tools to your toolbox
toolbox.add_tool(
    name="thinking",
    args={"thoughts": "str"},
    description="For thinking out loud"
)

#TODO anthropic code and setting prompt
async for event in parser.stream(ai_response):
    if event.is_tool_call:
        await toolbox.use(event)
```

### Synchronous

```python
#TODO
```

### Native Providers

#### Anthropic tooling

Anthropic can support native tool use, or you can parse the response that comes back.

```python
```


#### OpenAI tooling

OpenAI uses swagger definitions. You can support native OpenAI tooling as follows:

```python
#TODO
```

#### Native tooling

This supports other providers and open source models. Here you parse the results yourself.

### Retrieval and read-write Tools

Some tools, such as search, may want to give the AI information for further action. This involves crafting a new prompt to the LLM includes any Tool responses. We make this easy.

```python
# TODO Example
```

## Agent loops

Workflows and agent loops involve multiple calls to a LLM provider.

## Tips

* Keep the system prompt the same across invocations when using multiple LLM calls
* Stream when necessary
* If using native provider tooling, you can also parse your own tools. Using both gets the best of both worlds.

## About

AI Agent Toolbox is meant to be stable, reliable, and easy to master.

## Credits

AI Agent Toolbox is created and maintained by <a href="255labs.xyz">255labs.xyz</a>
