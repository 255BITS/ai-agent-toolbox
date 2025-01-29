# AI Agent Toolbox

<figure>
  <img src="https://raw.githubusercontent.com/255BITS/ai-agent-toolbox/main/docs/ai-agent-toolbox-logo.jpg" alt="AI Agent Toolbox Logo" width="300">
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

## Documentation

See the full documentation at [toolbox.255labs.xyz](https://toolbox.255labs.xyz/)

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

### Synchronous (Complete Response)

To parse a fully formed response:

```python
from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter
from examples.util import anthropic_llm_call

# Setup
toolbox = Toolbox()
parser = XMLParser(tag="use_tool")
formatter = XMLPromptFormatter(tag="use_tool")

# Add tools to your toolbox
def thinking(thoughts=""):
    print("I'm thinking:", thoughts)

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

system = "You are a thinking AI. You have interesting thoughts.\n"
prompt = "Think about something interesting."

# Add instructions on using the available tools to the AI system prompt
system += formatter.usage_prompt(toolbox)

response = anthropic_llm_call(system_prompt=system, prompt=prompt)
events = parser.parse(response)

for event in events:
    toolbox.use(event)
```

### Asynchronous (Streaming)

If you want to parse LLM responses as they come in:

```python
import asyncio
from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter
from examples.util import anthropic_stream

async def main():
    # Initialize components
    toolbox = Toolbox()
    parser = XMLParser(tag="tool")
    formatter = XMLPromptFormatter(tag="tool")
    
    # Register tools (add your actual tools here)
    toolbox.add_tool(
        name="search",
        fn=lambda query: f"Results for {query}",
        args={"query": {"type": "string"}},
        description="Web search tool"
    )
    # Set up the system and user prompt
    system = "You are a search agent.\n"

    # Add tool usage instructions
    system += formatter.usage_prompt(toolbox)
    prompt = "Search for ..."

    # Simulated streaming response from LLM
    async for chunk in anthropic_stream(system=system, prompt=prompt, ...):
        # Parse each chunk as it arrives
        for event in parser.parse_chunk(chunk):
            if event.is_tool_call:
                print(f"Executing tool: {event.tool.name}")
                await toolbox.use_async(event)  # Handle async tools

    # Call this at the end of output to handle any unclosed or invalid LLM outputs
    for event in parser.flush():
        if event.is_tool_call:
            print(f"Executing tool: {event.tool.name}")
            await toolbox.use_async(event)  # Handle async tools

if __name__ == "__main__":
    asyncio.run(main())
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

## Benefits

| Feature/Capability          | AI Agent Toolbox ✅ | Naive Regex ❌ | Standard XML Parsers ❌ |
|-----------------------------|---------------------|----------------|-------------------------|
| **Streaming Support**        | ✅ Chunk-by-chunk processing | ❌ Full text required | ❌ DOM-based requires full document |
| **Nested HTML/React**        | ✅ Handles JSX-like fragments | ❌ Fails on nesting | ❌ Requires strict hierarchy |
| **Flexible Tool Format**     | ✅ Supports multiple tool use formats | ❌ Brittle pattern matching | ❌ Requires schema validation |
| **Automatic Type Conversion**| ✅ String→int/float/bool | ❌ Manual casting needed | ❌ Returns only strings |
| **Error Recovery**           | ✅ Heals partial/malformed tags | ❌ Fails on first mismatch | ❌ Aborts on validation errors |
| **Battle Tested**            | ✅ Heavily tested | ❌ Ad-hoc testing | ❌ Generic XML cases only |
| **Tool Schema Enforcement**  | ✅ Args + types validation | ❌ No validation | ❌ Only structural validation |
| **Mixed Content Handling**   | ✅ Text + tools interleaved | ❌ Captures block text | ❌ Text nodes require special handling |
| **Async Ready**              | ✅ Native async/sync support | ❌ Callback hell | ❌ Sync-only typically |
| **Memory Safety**            | ✅ Guardrails against OOM | ❌ Unbounded buffers | ❌ DOM explosion risk |
| **LLM Output Optimized**     | ✅ Tolerates unclosed tags | ❌ Fails on partials | ❌ Strict tag matching |
| **Tool Feedback Loops**      | ✅ ToolResponse chaining | ❌ Manual stitching | ❌ No built-in concept |

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
* [https://github.com/255BITS/gptdiff](https://github.com/255BITS/gptdiff) - CLI and API to automatically create diffs and apply them
* [https://github.com/255BITS/filecannon](https://github.com/255BITS/filecannon) - CLI to generate files with AI
* [https://github.com/255BITS/appcannon](https://github.com/255BITS/appcannon) - A universal app generator for generating entire projects using AI

## License

MIT

## Credits

AI Agent Toolbox is created and maintained by <a href="255labs.xyz">255labs.xyz</a>
