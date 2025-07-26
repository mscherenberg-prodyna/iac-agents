"""GitHub agent node for LangGraph workflow."""

import asyncio
import json
import os
from typing import List

from ...logging_system import (
    log_agent_response,
    log_agent_start,
    log_info,
    log_warning,
)
from ...templates import template_manager
from ..git_utils import get_git_tools, git_tool_executor
from ..mcp_utils import MCPClient
from ..react_agent import agent_react_step
from ..state import InfrastructureStateDict
from ..utils import add_error_to_state, get_github_token, load_agent_response_schema

AGENT_NAME = "github_agent"


def run_github_react_workflow(
    mcp_client: MCPClient,
    conversation_history: List[str],
    schema: dict,
) -> str:
    """Sync wrapper for GitHub ReAct workflow."""

    async def _async_workflow():
        # Get tools description within session context
        async with mcp_client.session() as session:
            tools_list = await mcp_client.list_tools(session)

        # Format tools for consistency with devops agent
        tools_description = "\n".join(
            [f"- {tool['name']}: {tool['description']}" for tool in tools_list]
        )

        system_prompt = template_manager.get_prompt(
            AGENT_NAME,
            tools_description=tools_description,
            response_schema=json.dumps(schema, indent=2),
        )

        return await agent_react_step(
            mcp_client, system_prompt, conversation_history, AGENT_NAME, schema
        )

    return asyncio.run(_async_workflow())


def github_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Handle GitHub operations using ReAct workflow with MCP tools."""
    log_agent_start(AGENT_NAME, "Running GitHub interactions")

    # get GitHub token from config
    github_token = get_github_token()
    if not github_token:
        error_msg = "GITHUB_TOKEN environment variable not set"
        log_warning(AGENT_NAME, error_msg)

    mcp_client = MCPClient(
        [
            "run",
            "-i",
            "--rm",
            "-v",
            f"{os.getcwd()}:/workspace",
            "-w",
            "/workspace",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server",
        ],
        {"GITHUB_PERSONAL_ACCESS_TOKEN": github_token},
    )
    mcp_client.extend_tools(get_git_tools())
    mcp_client.set_custom_tool_executor(git_tool_executor)

    conversation_history = state["conversation_history"]

    log_info(AGENT_NAME, "Starting ReAct workflow with GitHub tools")

    try:
        # Load response schema once
        schema = load_agent_response_schema()
        
        # Run the ReAct workflow
        response = run_github_react_workflow(
            mcp_client=mcp_client,
            conversation_history=conversation_history,
            schema=schema,
        )
        conversation_history.append(
            f"GitHub: {response}"
        )  # Append response to conversation history

        # Log the response
        log_agent_response(AGENT_NAME, response)

        result_state = {
            **state,
            "current_agent": AGENT_NAME,
            "conversation_history": conversation_history,
        }

        return result_state

    except Exception as e:
        log_warning(AGENT_NAME, f"ReAct workflow failed: {str(e)}")
        return add_error_to_state(state, f"GitHub agent error: {str(e)}")
