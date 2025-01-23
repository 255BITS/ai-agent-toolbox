import asyncio
from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter
from examples.util import anthropic_stream

# Your workbench setup
toolbox = Toolbox()
parser = XMLParser(tag="use_tool")
formatter = XMLPromptFormatter(tag="use_tool")

async def thinking(thoughts=""):
    print(f"Thinking: {thoughts}")

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

async def main():
    system = "You are a thinking AI. You have interesting thoughts."
    prompt = "Think about something interesting."
    system += formatter.usage_prompt(toolbox)

    async for chunk in anthropic_stream(system, prompt):
        for event in parser.parse_chunk(chunk):
            await toolbox.use_async(event)

    # Process any remaining events after stream ends
    for event in parser.flush():
        toolbox.use(event)

if __name__ == "__main__":
    asyncio.run(main())
