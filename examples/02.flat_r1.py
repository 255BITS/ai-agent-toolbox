from ai_agent_toolbox import FlatXMLParser, FlatXMLPromptFormatter, Toolbox
from examples.util import r1_llm_call
from pprint import pprint

# Setup
toolbox = Toolbox()
parser = FlatXMLParser("think")
formatter = FlatXMLPromptFormatter(tag="think")

# Add tools to your toolbox
# Single required argument passed positionally
def think(content=""):
    print("I'm thinking:", content)

toolbox.add_tool(
    name="think",
    fn=think,
    args={
        # FlatXMLParser only takes a single string as an argument
        "content": {
            "type": "string",
            "description": "Anything you want to think about"
        }
    },
    description="For thinking out loud"
)

system = "You are a thinking AI. You have interesting thoughts.\n"
prompt = "Think about something interesting."

response = r1_llm_call(system_prompt=system, prompt=prompt)
events = parser.parse(response)

for event in events:
    toolbox.use(event)
