"""MCP utilities for agent operations using Python MCP package."""

from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Union

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


class MCPClient:
    """Generic MCP client."""

    def __init__(self, mcp_args: List[str], mcp_env: Dict[str, str]):
        self.mcp_args = mcp_args
        self.mcp_env = mcp_env
        self.tools_cache = None
        self.custom_tools = []
        self.custom_tool_executor = None

    @asynccontextmanager
    async def session(self):
        """Context manager for MCP session."""
        server_params = StdioServerParameters(
            command="docker",
            args=self.mcp_args,
            env=self.mcp_env,
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    async def list_tools(self, session: ClientSession) -> List[Dict[str, Any]]:
        """Get available tools."""
        if self.tools_cache:
            return self.tools_cache

        tools_result = await session.list_tools()
        mcp_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }
            for tool in tools_result.tools
        ]

        self.tools_cache = mcp_tools + self.custom_tools
        return self.tools_cache

    def extend_tools(
        self,
        custom_tools: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Extend tools with custom tools."""
        self.custom_tools.extend(custom_tools)
        if self.tools_cache:
            self.tools_cache.extend(custom_tools)
        return self.tools_cache or custom_tools

    def set_custom_tool_executor(
        self, executor: Callable[[str, Dict[str, Any]], Union[str, Any]]
    ):
        """Set the executor function for custom tools."""
        self.custom_tool_executor = executor

    def _is_custom_tool(self, tool_name: str) -> bool:
        """Check if a tool is a custom tool."""
        return any(tool["name"] == tool_name for tool in self.custom_tools)

    async def call_tool(
        self, session: ClientSession, name: str, arguments: Dict[str, Any]
    ) -> str:
        """Call a tool and return result."""
        try:
            if self._is_custom_tool(name):
                if not self.custom_tool_executor:
                    return f"Error: No executor function set for custom tool {name}"

                try:
                    result = self.custom_tool_executor(name, arguments)
                    if hasattr(result, "__await__"):
                        result = await result
                    return (
                        str(result)
                        if result is not None
                        else f"Custom tool {name} executed successfully"
                    )
                except Exception as e:
                    return f"Error executing custom tool {name}: {e}"

            result = await session.call_tool(name, arguments)

            if result.content:
                return "\n".join(
                    [
                        c.text if isinstance(c, TextContent) else str(c)
                        for c in result.content
                    ]
                )
            return f"Tool {name} executed successfully"

        except Exception as e:
            return f"Error calling tool {name}: {e}"
