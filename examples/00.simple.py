from ai_agent_toolbox import Toolbox
from ai_agent_toolbox.tools import Tool
from ai_agent_toolbox.parsers import XMLParser
from anthropic import Anthropic

# Your workbench setup
toolbox = Toolbox()
parser = XMLParser(tag="use_tool")

async def thinking(thoughts=""):
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
response = anthropic_llm_call(system_prompt=system, prompt=prompt)
tool_results = toolbox.parse(response)
tool_result = tool_results[0]

print("Thinking called with:", tool_result["thoughts"])
