#TODO this example is not yet working
from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pathlib import Path
from examples.util import anthropic_llm_call

# Setup
toolbox = Toolbox()
parser = XMLParser(tag="use_tool")
formatter = XMLPromptFormatter(tag="use_tool")

server_params = StdioServerParameters(
    command="python",
    args=[str(Path(__file__).parent.resolve() / "05.mcp_server.py")],
)

def convert_input_schema(inputSchema):
    args = {}
    properties = inputSchema["properties"]
    for key in properties.keys():
        args[key]={"type": properties[key]["type"], "description": properties[key]['title']}
    return args

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            def call_tool(tool):
                async def _call_tool(**kwargs):
                    return await session.call_tool(tool.name, kwargs)
                return _call_tool

            print("Initializing")
            await session.initialize()
            print("Listing tools")
            tools = await session.list_tools()
            for tool_tuple in tools:
                if tool_tuple[0] == "tools":
                    for tool in tool_tuple[1]:
                        print(f'adding tool "{tool.name}" with arguments {convert_input_schema(tool.inputSchema)}')
                        toolbox.add_tool(fn=call_tool(tool), name=tool.name, description=tool.description, args=convert_input_schema(tool.inputSchema))

            system = "You are testing a tool.\n"+formatter.usage_prompt(toolbox)
            prompt = "Use the tool to add 5 + 7"
            response = anthropic_llm_call(system_prompt=system, prompt=prompt)
            events = parser.parse(response)

            for event in events:
                if event.is_tool_call:
                    print("Calling tool", event.tool)
                    result = await toolbox.use_async(event)
                    print("Result", result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
