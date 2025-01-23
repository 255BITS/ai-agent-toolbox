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

system = "You are a thinking AI. You have interesting thoughts."
prompt = "Think about something interesting."

# Add our usage prompt
system += formatter.usage_prompt(toolbox)

response = anthropic_llm_call(system_prompt=system, prompt=prompt)
events = parser.parse(response)

for event in events:
    toolbox.use(event)
