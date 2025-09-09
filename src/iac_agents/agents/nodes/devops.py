"""DevOps Engineer Agent node for LangGraph workflow."""

import asyncio
import json
import os
from pathlib import Path
from typing import List, Tuple

from ...logging_system import (
    get_thread_id,
    log_agent_response,
    log_agent_start,
    log_info,
    log_warning,
)
from ...templates import template_manager
from ..git_utils import get_git_tools, git_tool_executor
from ..mcp_utils import MultiMCPClient
from ..react_agent import agent_react_step
from ..state import InfrastructureStateDict
from ..terraform_utils import get_terraform_tools, terraform_tool_executor
from ..utils import (
    add_error_to_state,
    get_github_token,
    load_agent_response_schema,
    verify_azure_auth,
)

AGENT_NAME = "devops"


def run_devops_react_workflow(
    mcp_client: MultiMCPClient,
    conversation_history: List[str],
    schema: dict,
) -> Tuple[str, str | None]:
    """Sync wrapper for DevOps ReAct workflow."""

    async def _async_workflow():
        # Get tools description within session context
        async with mcp_client.session() as session:
            tools_list = await mcp_client.list_tools(session)

        # Format tools for consistency
        tools_description = "\n".join(
            [f"- {tool['name']}: {tool['description']}" for tool in tools_list]
        )

        system_prompt = template_manager.get_prompt(
            AGENT_NAME,
            tools_description=tools_description,
            working_dir=str(
                Path.cwd() / "terraform_deployments" / f"deployment_{get_thread_id()}"
            ),
            response_schema=json.dumps(schema, indent=2),
        )

        return await agent_react_step(
            mcp_client,
            system_prompt,
            conversation_history,
            AGENT_NAME,
            schema,
        )

    return asyncio.run(_async_workflow())


def devops_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """DevOps Agent - Deployment automation using ReAct workflow with Terraform tools."""
    log_agent_start(AGENT_NAME, "Running DevOps deployment with Terraform tools")

    template_content = state.get("final_template", "")
    conversation_history = state.get("conversation_history", [])

    # Verify Azure CLI authentication
    if not verify_azure_auth(AGENT_NAME):
        error_msg = "Azure CLI authentication required"
        log_warning(AGENT_NAME, error_msg)
        return add_error_to_state(state, f"DevOps agent error: {error_msg}")

    # Create deployment workspace
    deployment_dir = (
        Path.cwd() / "terraform_deployments" / f"deployment_{get_thread_id()}"
    )
    if not os.path.isdir(deployment_dir):
        os.makedirs(deployment_dir)
        with open(deployment_dir / ".gitignore", "w", encoding="utf-8") as f:
            f.write(".terraform/\n")
            f.write("*.tfstate\n")
            f.write("*.tfstate.backup\n")
            f.write(".terraform.lock.hcl\n")

    # Write Terraform configuration
    main_tf_path = deployment_dir / "main.tf"
    with open(main_tf_path, "w", encoding="utf-8") as f:
        f.write(template_content)

    log_info(AGENT_NAME, f"Created deployment workspace: {deployment_dir}")

    # get GitHub token from config
    github_token = get_github_token()
    if not github_token:
        error_msg = "GITHUB_TOKEN environment variable not set"
        log_warning(AGENT_NAME, error_msg)

    mcp_client = MultiMCPClient()
    mcp_client.add_server(
        "github",
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
    mcp_client.add_custom_tools("git_cli", get_git_tools(), git_tool_executor)
    mcp_client.add_custom_tools(
        "terraform_cli", get_terraform_tools(), terraform_tool_executor
    )

    try:
        # Load response schema
        schema = load_agent_response_schema()

        # Run the ReAct workflow
        response, _ = run_devops_react_workflow(
            mcp_client=mcp_client,
            conversation_history=conversation_history,
            schema=schema,
        )

        conversation_history.append(
            f"DevOps Engineer: {response}"
        )  # Append response to conversation history

        # Log the response
        log_agent_response(AGENT_NAME, response)

        # Determine deployment status from response
        deployment_status = (
            "deployed" if "successfully" in response.lower() else "failed"
        )

        result_state = {
            **state,
            "current_agent": AGENT_NAME,
            "conversation_history": conversation_history,
            "devops_response": response,
            "deployment_status": deployment_status,
            "terraform_workspace": str(deployment_dir),
        }

        return result_state

    except Exception as e:
        log_warning(AGENT_NAME, f"ReAct workflow failed: {str(e)}")
        return add_error_to_state(state, f"DevOps agent error: {str(e)}")
