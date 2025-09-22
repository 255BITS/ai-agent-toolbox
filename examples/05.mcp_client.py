"""Client example that exercises the companion MCP server.

The script connects to :mod:`examples.05.mcp_server`, registers the exposed
MCP tools with :class:`ai_agent_toolbox.Toolbox`, and then uses Anthropic's
Claude model to trigger a tool invocation.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Dict

from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter
from examples.util import anthropic_llm_call
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT = Path(__file__).with_name("05.mcp_server.py")
SERVER_PARAMS = StdioServerParameters(
    command="python",
    args=[str(SERVER_SCRIPT.resolve())],
)

_JSON_TYPE_MAPPING = {
    "integer": "int",
    "number": "float",
    "boolean": "bool",
}


def convert_input_schema(input_schema: Mapping[str, Any]) -> Dict[str, Dict[str, str]]:
    """Convert an MCP JSON schema into Toolbox argument metadata."""

    properties = input_schema.get("properties", {})
    args: Dict[str, Dict[str, str]] = {}

    for name, schema in properties.items():
        json_type = schema.get("type", "string")
        normalized_type = _JSON_TYPE_MAPPING.get(json_type, json_type)
        description = schema.get("description") or schema.get("title") or ""
        args[name] = {
            "type": normalized_type,
            "description": description,
        }

    return args


def build_remote_tool(session: ClientSession, tool_name: str):
    """Return a coroutine function that forwards calls to the MCP session."""

    async def _call_tool(**kwargs: Any) -> Any:
        return await session.call_tool(tool_name, kwargs)

    return _call_tool


async def register_remote_tools(session: ClientSession, toolbox: Toolbox) -> None:
    """Populate ``toolbox`` with the tools advertised by ``session``."""

    print("Initializing MCP session")
    await session.initialize()

    print("Listing tools")
    tool_groups = await session.list_tools()
    for kind, tools in tool_groups:
        if kind != "tools":
            continue

        for tool in tools:
            args = convert_input_schema(tool.inputSchema)
            print(f'adding tool "{tool.name}" with arguments {args}')
            toolbox.add_tool(
                name=tool.name,
                fn=build_remote_tool(session, tool.name),
                description=tool.description or "",
                args=args,
            )


async def run() -> None:
    toolbox = Toolbox()
    parser = XMLParser(tag="use_tool")
    formatter = XMLPromptFormatter(tag="use_tool")

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await register_remote_tools(session, toolbox)

            system_prompt = "You are testing a tool.\n" + formatter.usage_prompt(toolbox)
            prompt = "Use the tool to add 5 + 7"
            response = anthropic_llm_call(prompt=prompt, system_prompt=system_prompt)

            for event in parser.parse(response):
                if not event.is_tool_call:
                    continue

                print("Calling tool", event.tool)
                tool_response = await toolbox.use_async(event)

                if tool_response is None:
                    print("No matching tool found.")
                    continue

                print("Result", tool_response)


if __name__ == "__main__":
    asyncio.run(run())
