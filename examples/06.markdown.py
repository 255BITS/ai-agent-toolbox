from ai_agent_toolbox import Toolbox, MarkdownParser, MarkdownPromptFormatter
from examples.util import anthropic_llm_call

# Setup the toolbox, parser, and prompt formatter for Markdown.
toolbox = Toolbox()
parser = MarkdownParser()
formatter = MarkdownPromptFormatter()

# Define a simple Python REPL tool that executes Python code.
def python_repl(content=""):
    """
    Executes the provided Python code in a simple REPL environment.
    Captures and returns stdout, or an error message if execution fails.
    """
    try:
        import io, contextlib
        output = io.StringIO()
        # Execute the code in an isolated namespace.
        with contextlib.redirect_stdout(output):
            exec(content, {})
        result = output.getvalue()
        return result if result else "No output."
    except Exception as e:
        return f"Error: {str(e)}"

# Add the Python REPL tool to the toolbox.
toolbox.add_tool(
    name="python",
    fn=python_repl,
    args={
        "content": {
            "type": "string",
            "description": "Python code to execute in a REPL environment"
        }
    },
    description="Executes Python code provided within a Markdown code fence."
)

# Construct the system prompt.
system = (
    "You are a Python REPL assistant. "
    "When given a piece of Python code wrapped in a Markdown code fence (with the language 'python'), "
    "execute it and return the result.\n"
)
# Append tool usage instructions (the formatter will show how to invoke the tool).
system += formatter.usage_prompt(toolbox)

prompt = (
    "Please provide some Python code to run. It should output something interesting and work first pass."
    "Wrap your code in a Markdown code fence starting with ```python. For example:\n\n"
    "```python\nprint('Hello, world!')\n```\n"
)

# Make the LLM call (this function is assumed to send the prompt to an LLM and return its response).
response = anthropic_llm_call(system_prompt=system, prompt=prompt)

print("--", response)
# Parse the response into events.
events = parser.parse(response)

# Process the parsed events; execute any tool calls.
for event in events:
    if event.is_tool_call:
        result = toolbox.use(event)
        print("Tool output:", result.result)
