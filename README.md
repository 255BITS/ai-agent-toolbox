# AI Agent Toolbox

<figure>
  <img src="docs/ai-agent-toolbox-logo.jpg" alt="AI Agent Toolbox Logo" width="300">
</figure>

AI Agent Toolbox makes AI tool usage across models and frameworks easy. For use with parsing single responses or in agent loops and workflow.

AI Agent Toolbox is meant to be stable, reliable, and easy to master.

## Features

* Model provider-agnostic - supports Anthropic, OpenAI, Groq, NEAR AI, Ollama, Hyperbolic, NanoGPT, and more
* Framework compatible - usable in anthropic-sdk-python, openai-python, ell, LangChain, etc
* Supports protocols such as Anthropic Model Context Protocol(MCP)
* Robust parsing
* Streaming support
* Support for read-write tools (feedback) as well as write-only tools

## Installation

```bash
pip install ai-agent-toolbox
```

## Examples

See our [examples folder](https://github.com/255BITS/ai-agent-toolbox/tree/main/examples) for:
- Simple tool usage
- Streaming integration
- Read-write tools with feedback loops
- Agent workflow examples

## Usage

### Asynchronous

```python
from ai_agent_toolbox import Toolbox, XMLParser
from examples.util import anthropic_stream

async def main():
    toolbox = Toolbox()
    parser = XMLParser(tag="tool")
    # Add tools and handle streaming responses
    async for chunk in anthropic_stream(...):
        for event in parser.parse_chunk(chunk):
            await toolbox.use_async(event)
```

### Synchronous

```python
from ai_agent_toolbox import Toolbox, XMLParser

# Initialize components
toolbox = Toolbox()
parser = XMLParser(tag="tool")
# Parse and execute tools
events = parser.parse(llm_response)
for event in events:
    toolbox.use(event)
```

### Local Tooling

This supports other providers and open source models. Here you parse the results yourself.

### Retrieval and read-write tools

Some tools, such as search, may want to give the AI information for further action. This involves crafting a new prompt to the LLM includes any tool responses. We make this easy.

```python 
from ai_agent_toolbox import ToolResponse

def search_tool(query: str):
    return f"Results for {query}"

# In your agent loop:
responses = [r.result for r in tool_responses if r.result]
new_prompt = f"Previous tool outputs:\n{'\n'.join(responses)}\n{original_prompt}"

# Execute next LLM call with enriched prompt
next_response = llm_call(
    system_prompt=system,
    prompt=new_prompt
)
# Continue processing...

```

## Agent loops

Workflows and agent loops involve multiple calls to a LLM provider.

## Tips

* Keep the system prompt the same across invocations when using multiple LLM calls
* Stream when necessary, for example when a user is waiting for output
* Native provider tooling can be used with local parsing
* Start simple and expand. You can test with static strings to ensure your tools are working correctly.

## Ecosystem
### Used by
* [https://github.com/255BITS/ai-agent-examples](https://github.com/255BITS/ai-agent-examples) - A repository of examples of agentic workflows
* [https://github.com/255BITS/gptdiff](https://github.com/255BITS/gptdiff) - AI automatically create diffs and applies them

## License

MIT

## Credits

AI Agent Toolbox is created and maintained by <a href="255labs.xyz">255labs.xyz</a>