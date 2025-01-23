from ai_agent_toolbox import FlatXMLParser, FlatXMLPromptFormatter, Toolbox
from examples.util import r1_llm_call
from pprint import pprint

# Setup
toolbox = Toolbox()
parser = FlatXMLParser("think")
formatter = FlatXMLPromptFormatter(tag="think")

# Add tools to your toolbox
# Note: argument name is always 'default' with FlatXMLParser
# TODO This is a bit of a smell, should do *args instead of **kwargs
def think(default=""):
    print("I'm thinking:", default)

toolbox.add_tool(
    name="think",
    fn=think,
    args={
        # FlatXMLParser only takes a single string as an argument
        "default": {
            "type": "string",
            "description": "Anything you want to think about"
        }
    },
    description="For thinking out loud"
)

system = "You are a thinking AI. You have interesting thoughts.\n"
prompt = "Think about something interesting."

# Add our usage prompt
system += formatter.usage_prompt(toolbox)

response = r1_llm_call(system_prompt=system, prompt=prompt)
events = parser.parse(response)

for event in events:
    result = toolbox.use(event)
