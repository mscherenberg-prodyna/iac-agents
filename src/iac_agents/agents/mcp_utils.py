"""MCP utilities for agent operations using Python MCP package."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional, Union

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

from ..logging_system import log_info, log_warning


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


class MultiMCPClient:
    """Multi-server MCP client that directly connects to locally running servers."""

    def __init__(self):
        self.servers: Dict[str, StdioServerParameters] = {}
        self.custom_tools: Dict[str, Dict] = {}
        self.custom_executors: Dict[str, Callable] = {}
        self._tools_cache: Optional[List[Dict]] = None

    @asynccontextmanager
    async def session(self):
        """Context manager for MCP session."""
        yield self

    def add_server(
        self, name: str, mcp_args: List[str], mcp_env: Dict[str, str] = None
    ):
        """Add an MCP server."""
        self.servers[name] = StdioServerParameters(
            command="docker", args=mcp_args, env=mcp_env or {}
        )
        self._tools_cache = None  # Invalidate cache
        log_info("MultiMCP", f"Added server: {name}")

    def add_custom_tools(self, prefix: str, tools: List[Dict], executor: Callable):
        """Add custom tools."""
        self.custom_executors[prefix] = executor

        for tool in tools:
            tool_name = f"{prefix}_{tool['name']}"
            self.custom_tools[tool_name] = {
                "name": tool_name,
                "description": tool["description"],
                "inputSchema": tool.get("inputSchema", {}),
                "prefix": prefix,
                "original_name": tool["name"],
                "source": "custom",
            }

        self._tools_cache = None  # Invalidate cache
        log_info("MultiMCP", f"Added {len(tools)} custom tools with prefix: {prefix}")

    async def _get_server_tools(
        self, server_name: str, server_params: StdioServerParameters
    ) -> List[Dict]:
        """Get tools from a single MCP server."""
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()

                    return [
                        {
                            "name": f"{server_name}_{tool.name}",
                            "description": tool.description,
                            "inputSchema": tool.inputSchema or {},
                            "server": server_name,
                            "original_name": tool.name,
                            "source": "mcp_server",
                        }
                        for tool in tools_result.tools
                    ]
        except Exception as e:
            log_warning("MultiMCP", f"Failed to get tools from {server_name}: {e}")
            return []

    async def list_tools(self, _session=None) -> List[Dict[str, Any]]:
        """Get all tools from all servers and custom tools."""
        if self._tools_cache is not None:
            return self._tools_cache

        all_tools = []

        # Get tools from all MCP servers
        server_tasks = [
            self._get_server_tools(name, params)
            for name, params in self.servers.items()
        ]

        if server_tasks:
            server_results = await asyncio.gather(*server_tasks, return_exceptions=True)
            for result in server_results:
                if isinstance(result, list):
                    all_tools.extend(result)

        # Add custom tools
        for tool_info in self.custom_tools.values():
            all_tools.append(
                {
                    "name": tool_info["name"],
                    "description": tool_info["description"],
                    "inputSchema": tool_info["inputSchema"],
                }
            )

        self._tools_cache = all_tools
        return all_tools

    async def call_tool(self, _session, name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool by routing to the correct server or executor."""

        # Check custom tools first
        if name in self.custom_tools:
            tool_info = self.custom_tools[name]
            try:
                executor = self.custom_executors[tool_info["prefix"]]
                result = executor(tool_info["original_name"], arguments)
                if hasattr(result, "__await__"):
                    result = await result
                return str(result) if result is not None else "Success"
            except Exception as e:
                return f"Error executing custom tool {name}: {e}"

        # Check MCP servers
        for server_name, server_params in self.servers.items():
            if name.startswith(f"{server_name}_"):
                original_name = name[len(f"{server_name}_") :]
                try:
                    async with stdio_client(server_params) as (read, write):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            result = await session.call_tool(original_name, arguments)

                            if result.content:
                                return "\n".join(
                                    [
                                        c.text if isinstance(c, TextContent) else str(c)
                                        for c in result.content
                                    ]
                                )
                            return "Success"
                except Exception as e:
                    return f"Error calling {name} on {server_name}: {e}"

        return f"Tool {name} not found"
