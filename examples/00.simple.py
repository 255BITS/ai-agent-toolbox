from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter
from examples.util import anthropic_llm_call

# Setup
toolbox = Toolbox()
parser = XMLParser(tag="use_tool")
formatter = XMLPromptFormatter(tag="use_tool")

# Add tools to your toolbox
def thinking(thoughts: str, tone: str = "curious"):
    message = f"I'm thinking ({tone}): {thoughts}"
    print(message)
    return message

toolbox.add_tool(
    name="thinking",
    fn=thinking,
    args={
        "thoughts": {
            "type": "string",
            "description": "Anything you want to think about",
            "required": True,
        },
        "tone": {
            "type": "string",
            "description": "Optional vibe for the thoughts",
            "required": False,
            "default": "curious",
        },
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
    response = toolbox.use(event)
    if response and response.error:
        print("Tool validation error:", response.error)
    elif response:
        print(f"{response.tool.name} result:", response.result)
