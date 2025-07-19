"""MCP utilities for agent operations using Python MCP package."""

import re
from typing import List

from ..templates import template_manager
from .mcp_utils import MCPClient


async def agent_react_step(
    mcp_client: MCPClient,
    llm_call_func,
    conversation_history: List[str],
    agent_name: str,
) -> str:
    """Execute a ReAct loop with GitHub tools."""

    async with mcp_client.session() as session:
        tools_description = await mcp_client.list_tools(session)

        system_prompt = template_manager.get_prompt(
            agent_name,
            tools_description=tools_description,
        )

        # Start ReAct loop
        while True:
            # Get LLM response
            user_message = "\n\n###\n\n".join(conversation_history)

            response = llm_call_func(system_prompt, user_message)
            print(f"LLM Response: {response}")

            # Check if agent wants to use a tool
            if "TOOL_CALL:" in response:
                tool_lines = [
                    line for line in response.split("\n") if "TOOL_CALL:" in line
                ]
                if tool_lines:
                    tool_call = tool_lines[0].split("TOOL_CALL:")[1].strip()
                    match = re.match(r"(\w+)\((.*)\)", tool_call)
                    if match:
                        tool_name = match.group(1)

                        # Parse arguments - simple implementation for key="value" format
                        args_str = match.group(2)
                        arguments = {}
                        if args_str:
                            for param in args_str.split(","):
                                if "=" in param:
                                    key, value = param.split("=", 1)
                                    key = key.strip()
                                    value = value.strip().strip("\"'")
                                    # Convert boolean strings
                                    if value.lower() == "true":
                                        value = True
                                    elif value.lower() == "false":
                                        value = False
                                    arguments[key] = value

                        # Execute tool correctly
                        tool_result = await mcp_client.call_tool(
                            session, tool_name, arguments
                        )

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
