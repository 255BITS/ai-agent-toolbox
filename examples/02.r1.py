from ai_agent_toolbox import FlatXMLParser, FlatXMLPromptFormatter
from examples.util import r1_llm_call
from pprint import pprint

parser = FlatXMLParser("think")
formatter = FlatXMLPromptFormatter(tag="use_tool")

system = "You are a thinking AI. You have interesting thoughts."
prompt = "Think about something interesting."
response = r1_llm_call(system_prompt=system, prompt=prompt)

print("Found response", response)
events = parser.parse(response)

result = None
pprint(events)
for event in events:
    if event.is_tool_call:
        result = event.content

print("Think:", result)
