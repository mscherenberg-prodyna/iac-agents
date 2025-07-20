"""GitHub agent for handling Git and GitHub-related tasks."""

import asyncio
import os
from typing import List

from src.iac_agents.agents.git_utils import get_git_tools, git_tool_executor
from src.iac_agents.agents.mcp_utils import MCPClient
from src.iac_agents.agents.react_agent import agent_react_step
from src.iac_agents.agents.utils import make_llm_call
from src.iac_agents.config.settings import config
from src.iac_agents.logging_system import (
    log_agent_complete,
    log_agent_response,
    log_agent_start,
    log_info,
    log_warning,
)

AGENT_NAME = "github_agent"


def run_github_react_workflow(
    github_token: str,
    llm_call_func,
    conversation_history: List[str],
) -> str:
    """Sync wrapper for GitHub ReAct workflow."""

    async def _async_workflow():
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
        return await agent_react_step(
            mcp_client, llm_call_func, conversation_history, AGENT_NAME
        )

    return asyncio.run(_async_workflow())


def github_agent():
    """Handle GitHub operations using ReAct workflow with MCP tools."""
    log_agent_start(AGENT_NAME, "Processing GitHub operations request")

    # Get GitHub token from config
    github_token = config.github.github_token
    if not github_token:
        error_msg = "GITHUB_TOKEN environment variable not set"
        log_warning(AGENT_NAME, error_msg)

    # Create LLM call function with agent context
    def llm_call_func(sys_prompt: str, user_msg: str) -> str:
        return make_llm_call(sys_prompt, user_msg)

    # Execute ReAct workflow with GitHub tools
    log_info(AGENT_NAME, "Starting ReAct workflow with GitHub tools")
    response = run_github_react_workflow(
        github_token=github_token,
        llm_call_func=llm_call_func,
        conversation_history=[
            "USER: Push the current main branch to GitHub. Do not commit any changes."
        ],
    )

    # Check if operation was successful
    operation_success = (
        "error" not in response.lower() and "failed" not in response.lower()
    )

    # Log the response
    log_agent_response(AGENT_NAME, response)

    log_agent_complete(
        AGENT_NAME,
        f"GitHub operations {'completed successfully' if operation_success else 'completed with issues'}",
    )


if __name__ == "__main__":
    github_agent()
