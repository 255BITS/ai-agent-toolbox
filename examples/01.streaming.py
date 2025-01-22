from ai_agent_toolbox import Toolbox
from ai_agent_toolbox.tools import Tool
from ai_agent_toolbox.parsers import XMLParser

# Your workbench setup
toolbox = Toolbox()
parser = XMLParser(tag="use_tool")

def thinking(thoughts=""):
    pass

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

system = "You are a thinking AI. You have interesting thoughts."
prompt = "Think about something interesting."

for async text in anthropic_stream(system, prompt):
    for event in parser.parse_chunk(text):
        toolbox.use(event)

for event in parser.flush():
    toolbox.use(event)
#TODO

print("Thinking called with:", result["thoughts"])
