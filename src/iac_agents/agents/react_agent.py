"""MCP utilities for agent operations using Python MCP package."""

import re
from typing import Any, Callable, Dict, List

from ..logging_system import (
    log_agent_response,
)
from .mcp_utils import MCPClient
from .utils import make_llm_call

TOOL_TRIGGER = "TOOL_CALL:"


async def agent_react_step(
    mcp_client: MCPClient,
    system_prompt: str,
    conversation_history: List[str],
    agent_name: str,
) -> str:
    """Execute a ReAct loop with an MCP client and additional tools."""

    async with mcp_client.session() as session:

        # start ReAct loop
        while True:

            # get LLM response
            user_message = "\n\n###\n\n".join(conversation_history)

            response = make_llm_call(system_prompt, user_message)

            # check if agent wants to use a tool
            if TOOL_TRIGGER in response:
                tool_lines = [
                    line for line in response.split("\n") if TOOL_TRIGGER in line
                ]
                if tool_lines:
                    tool_call = tool_lines[0].split(TOOL_TRIGGER)[1].strip()
                    match = re.match(r"(\w+)\((.*)\)", tool_call)
                    if match:
                        tool_name = match.group(1)

                        args_str = match.group(2)
                        arguments = {}
                        if args_str:
                            for param in args_str.split(","):
                                if "=" in param:
                                    key, value = param.split("=", 1)
                                    key = key.strip()
                                    value = value.strip().strip("\"'")
                                    if value.lower() == "true":
                                        value = True
                                    elif value.lower() == "false":
                                        value = False
                                    arguments[key] = value

                        log_agent_response(
                            agent_name,
                            f"Calling tool: {tool_name} with args: {arguments}",
                        )
                        tool_result = await mcp_client.call_tool(
                            session, tool_name, arguments
                        )
                        log_agent_response(agent_name, f"Tool Result: {tool_result}")

                    else:
                        tool_result = f"Error: Invalid tool call format: {tool_call}"

                    # Add to conversation
                    conversation_history.append(f"Agent: {response}")
                    conversation_history.append(f"Tool Result: {tool_result}")
                else:
                    # No valid tool call found, continue
                    conversation_history.append(f"Agent: {response}")
            else:
                # No tool call, agent is done
                return response


class ToolClient:
    """Simple tool client for non-MCP tools that mimics MCP client interface."""

    def __init__(self, tools: List[Dict[str, Any]], tool_executor: Callable):
        """Initialize with tools and executor function."""
        self.tools = tools
        self.tool_executor = tool_executor

    def session(self):
        """Mock session context manager."""
        return self

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

    async def call_tool(
        self, session, tool_name: str, arguments: Dict[str, Any]
    ) -> str:
        """Execute tool using the provided executor."""
        return self.tool_executor(tool_name, arguments)


async def agent_react_step_with_tools(
    tools: List[Dict[str, Any]],
    tool_executor: Callable,
    system_prompt: str,
    conversation_history: List[str],
    agent_name: str,
) -> str:
    """Execute ReAct loop with custom tools (non-MCP)."""

    # Create tool client
    tool_client = ToolClient(tools, tool_executor)

    # Use existing react agent with our tool client
    return await agent_react_step(
        tool_client, system_prompt, conversation_history, agent_name
    )
