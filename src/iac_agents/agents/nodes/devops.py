"""DevOps Engineer Agent node for LangGraph workflow."""

import asyncio
import subprocess
from pathlib import Path
from typing import List

from iac_agents.logging_system import get_thread_id

from ...logging_system import (
    log_agent_response,
    log_agent_start,
    log_info,
    log_warning,
)
from ...templates import template_manager
from ..react_agent import agent_react_step_with_tools
from ..state import InfrastructureStateDict
from ..terraform_utils import get_terraform_tools, terraform_tool_executor
from ..utils import add_error_to_state

AGENT_NAME = "devops"


def run_devops_react_workflow(
    system_prompt: str,
    conversation_history: List[str],
) -> str:
    """Sync wrapper for DevOps ReAct workflow."""

    async def _async_workflow():
        tools = get_terraform_tools()
        return await agent_react_step_with_tools(
            tools=tools,
            tool_executor=terraform_tool_executor,
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            agent_name=AGENT_NAME,
        )

    return asyncio.run(_async_workflow())


def devops_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """DevOps Agent - Deployment automation using ReAct workflow with Terraform tools."""
    log_agent_start(AGENT_NAME, "Running DevOps deployment with Terraform tools")

    template_content = state.get("final_template", "")
    conversation_history = state["conversation_history"]

    # Verify Azure CLI authentication
    if not verify_azure_auth():
        error_msg = "Azure CLI authentication required"
        log_warning(AGENT_NAME, error_msg)
        return add_error_to_state(state, f"DevOps agent error: {error_msg}")

    # Create deployment workspace
    deployment_dir = (
        Path.cwd() / "terraform_deployments" / f"deployment_{get_thread_id()}"
    )
    deployment_dir.mkdir(parents=True, exist_ok=True)

    # Write Terraform configuration
    main_tf_path = deployment_dir / "main.tf"
    with open(main_tf_path, "w", encoding="utf-8") as f:
        f.write(template_content)

    log_info(AGENT_NAME, f"Created deployment workspace: {deployment_dir}")

    # Get tools description for system prompt
    tools = get_terraform_tools()
    tools_description = "\n".join(
        [f"- {tool['name']}: {tool['description']}" for tool in tools]
    )

    system_prompt = template_manager.get_prompt(
        AGENT_NAME, tools_description=tools_description, working_dir=str(deployment_dir)
    )

    log_info(AGENT_NAME, "Starting ReAct workflow with Terraform tools")

    try:
        # Run the ReAct workflow
        response = run_devops_react_workflow(
            system_prompt=system_prompt,
            conversation_history=conversation_history,
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
            "workflow_phase": "complete",
        }

        return result_state

    except Exception as e:
        log_warning(AGENT_NAME, f"ReAct workflow failed: {str(e)}")
        return add_error_to_state(state, f"DevOps agent error: {str(e)}")


def verify_azure_auth() -> bool:
    """Verify Azure CLI authentication using active session."""
    try:
        # Check if Azure CLI is installed and authenticated
        result = subprocess.run(
            ["az", "account", "show"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if result.returncode == 0:
            log_agent_start(AGENT_NAME, "Azure CLI authentication verified")
            return True
        log_warning(AGENT_NAME, f"Azure CLI authentication failed: {result.stderr}")
        return False

    except subprocess.TimeoutExpired:
        log_warning(AGENT_NAME, "Azure CLI authentication check timed out")
        return False
    except FileNotFoundError:
        log_warning(AGENT_NAME, "Azure CLI not found - please install Azure CLI")
        return False
    except Exception as e:
        log_warning(AGENT_NAME, f"Azure authentication verification failed: {str(e)}")
        return False
