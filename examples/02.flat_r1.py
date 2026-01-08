from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter
from examples.util import r1_llm_call
from pprint import pprint

# Setup
toolbox = Toolbox()
parser = XMLParser(tag="tool")
formatter = XMLPromptFormatter(tag="tool")

# Add tools to your toolbox
# Single required argument passed positionally
def think(content=""):
    print("I'm thinking:", content)

toolbox.add_tool(
    name="think",
    fn=think,
    args={
        # XMLParser reads named arguments from XML tags.
        "content": {
            "type": "string",
            "description": "Anything you want to think about"
        }
    },
    description="For thinking out loud"
)

system = "You are a thinking AI. You have interesting thoughts.\n"
prompt = "Think about something interesting."

#This isn't needed because of our r1_llm_call method
#system += formatter.usage_prompt(toolbox)

response = r1_llm_call(system_prompt=system, prompt=prompt)
events = parser.parse(response)

for event in events:
    toolbox.use(event)
