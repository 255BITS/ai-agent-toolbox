from ai_agent_toolbox import Toolbox
from ai_agent_toolbox.tools import Tool
from ai_agent_toolbox.parsers import XMLParser
from .util import anthropic_llm_call

# Setup
toolbox = Toolbox()
parser = XMLParser(tag="use_tool")

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

#TODO build toolbox
system += toolbox.usage_prompt()
response = anthropic_llm_call(system_prompt=system, prompt=prompt)
events = parser.parse(response)

for event in events:
    #if event.is_tool_call: TODO move to toolbox.use
    toolbox.use(event)
