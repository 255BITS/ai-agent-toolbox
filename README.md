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

```
pip install ai-agent-toolbox(TODO)
```

## Examples

See our [examples](examples) folder for more!

## Usage

### Asynchronous

```python
TODO example
```

### Synchronous

```python
TODO example
```

### Native Providers

#### Anthropic tooling

Anthropic can support native tool use, or you can parse the response that comes back.

```python
TODO example
```

#### OpenAI tooling

OpenAI uses swagger definitions. You can support native OpenAI tooling as follows:

```python
TODO example
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
* Stream when necessary, for example when a user is waiting for output
* Native provider tooling can be used with local parsing
* Start simple and expand. You can test with static strings to ensure your tools are working correctly.

## Ecosystem

### Used by
* [https://github.com/255BITS/ai-agent-examples](https://github.com/255BITS/ai-agent-examples) - A repository of examples of agentic workflows
* [https://github.com/255BITS/gptdiff](https://github.com/255BITS/gptdiff) - Automatically create diffs and apply them using AI.

## License

MIT

## Credits

AI Agent Toolbox is created and maintained by <a href="255labs.xyz">255labs.xyz</a>
