"""GitHub agent node for LangGraph workflow."""

import asyncio
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
from ..utils import add_error_to_state, get_github_token

AGENT_NAME = "github_agent"


def run_github_react_workflow(
    mcp_client: MCPClient,
    system_prompt: str,
    conversation_history: List[str],
) -> str:
    """Sync wrapper for GitHub ReAct workflow."""

    async def _async_workflow():
        return await agent_react_step(
            mcp_client, system_prompt, conversation_history, AGENT_NAME
        )

    return asyncio.run(_async_workflow())


async def github_agent(state: InfrastructureStateDict):
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
    tools_description = await mcp_client.list_tools(mcp_client.session())
    system_prompt = template_manager.get_prompt(
        AGENT_NAME,
        tools_description=tools_description,
    )
    conversation_history = state["conversation_history"]

    log_info(AGENT_NAME, "Starting ReAct workflow with GitHub tools")

    try:
        # Run the ReAct workflow
        response = run_github_react_workflow(
            mcp_client=mcp_client,
            system_prompt=system_prompt,
            conversation_history=conversation_history,
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
