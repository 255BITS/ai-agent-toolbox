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

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("Initializing")
            await session.initialize()
            print("Listing tools")
            tools = await session.list_tools()
            for tool in tools:
                print("tool is", tool)
                #toolbox.add_mcp_tool(tool)

            #response = anthropic_llm_call(system_prompt=system, prompt=prompt)
            #events = parser.parse(response)

            #for event in events:
            #    toolbox.use(event)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
