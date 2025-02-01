#TODO this example is not yet working
from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pathlib import Path

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

async def call_tool(tool):
    async def _call_tool(*args, **kwargs):
        pass
    return _call_tool

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("Initializing")
            await session.initialize()
            print("Listing tools")
            tools = await session.list_tools()
            for tool_tuple in tools:
                if tool_tuple[0] == "tools":
                    for tool in tool_tuple[1]:
                        print("tool is", tool)
                        toolbox.add_tool(name=tool.name, description=tool.description, **convert_input_schema(tool.inputSchema))
                        print("--", toolbox._tools)
                #toolbox.add_mcp_tool(tool)

            #response = anthropic_llm_call(system_prompt=system, prompt=prompt)
            #events = parser.parse(response)

            #for event in events:
            #    toolbox.use(event)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
