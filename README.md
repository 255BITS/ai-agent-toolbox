# AI Agent Toolbox

TODO LOGO

AI Agent Toolbox(AAT) makes AI tool usage across models and frameworks easy. AAT works for parsing single use responses, or in agent and workflow loops.

## About

AI Agent Toolbox is meant to be stable, reliable, and easy to master.


## Features

* Native support protocols such as Anthropic MCP(link)
* Robust parsing
* Streaming support
* Support for read-write and write-only tools
* Framework compatible
* Model provider-agnostic - supports Anthropic, OpenAI, Groq, Ollama, Hyperbolic, NanoGPT, and more

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

async def thinking(thoughts=""):
    print("I am thinking: "+thoughts)

# Adding tools to your toolbox
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

#TODO anthropic code and setting prompt
async for event in parser.stream(ai_response):
    if event.is_tool_call:
        tool_result = await toolbox.use(event.name, event.args)
print("thinking called with", tool_result["thoughts"])
```

### Synchronous

```python
from ai_agent_toolbox import Toolbox
from ai_agent_toolbox.tools import Tool
from ai_agent_toolbox.parsers import XMLParser

# Your workbench setup
toolbox = Toolbox()
parser = XMLParser(tag="use_tool")

def thinking(thoughts=""):
    print("I am thinking: "+thoughts)

# Adding tools to your toolbox
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

#TODO anthropic code and setting prompt
for event in parser.parse(ai_response):
    if event.is_tool_call:
        tool_result = toolbox.use(event.name, event.args)
print("thinking called with", tool_result["thoughts"])
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

#### Local tooling

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

## Ecosystem

### Usage

Used by [https://github.com/255BITS/ai-agent-examples](https://github.com/255BITS/ai-agent-examples)

## License

MIT

## Credits

AI Agent Toolbox is created and maintained by <a href="255labs.xyz">255labs.xyz</a>
