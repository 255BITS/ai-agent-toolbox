from ai_agent_toolbox import FlatXMLParser, FlatXMLPromptFormatter
from examples.util import r1_llm_call
from pprint import pprint

# Setup
toolbox = Toolbox()
parser = FlatXMLParser(tag="think")
formatter = FlatXMLPromptFormatter(tag="think")

system = "You are a thinking AI. You have interesting thoughts."
prompt = "Think about something interesting."
response = r1_llm_call(system_prompt=system, prompt=prompt)

print("Found response", response)
events = parser.parse(response)

def thinking(thoughts=""):
    print("I'm thinking:", thoughts)

for event in events:
    result = toolbox.use(event)
