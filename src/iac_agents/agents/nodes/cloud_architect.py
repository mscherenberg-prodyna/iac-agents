"""Cloud Architect Agent node for LangGraph workflow."""

import asyncio
import json
from typing import List, Tuple

from ...logging_system import (log_agent_complete, log_agent_response,
                               log_agent_start, log_warning)
from ...templates.template_manager import template_manager
from ..iap_workflow_utils import get_iap_tools, iap_tool_executor
from ..mcp_utils import MultiMCPClient
from ..react_agent import agent_react_step
from ..state import InfrastructureStateDict
from ..terraform_utils import get_terraform_tools, terraform_tool_executor
from ..utils import (add_error_to_state, get_azure_subscription_info,
                     load_agent_response_schema, verify_azure_auth)

AGENT_NAME = "cloud_architect"


def run_cloud_architect_react_workflow(
    mcp_client: MultiMCPClient,
    conversation_history: List[str],
    state: InfrastructureStateDict,
    schema: dict,
) -> Tuple[str, str | None]:
    """Sync wrapper for Cloud Architect ReAct workflow."""

    async def _async_workflow():
        # Get tools description within session context
        async with mcp_client.session() as session:
            tools_list = await mcp_client.list_tools(session)

        # Format tools for consistency
        tools_description = "\n".join(
            [f"- {tool['name']}: {tool['description']}" for tool in tools_list]
        )

        # Extract configuration settings from state
        compliance_settings = state.get("compliance_settings", {})
        compliance_enforcement = (
            "Enabled"
            if compliance_settings.get("enforce_compliance", False)
            else "Disabled"
        )
        compliance_frameworks = (
            ", ".join(compliance_settings.get("selected_frameworks", []))
            or "None selected"
        )
        approval_required = "Yes" if state.get("requires_approval", True) else "No"
        approval_received = "Yes" if state.get("approval_received", False) else "No"

        # Get Azure subscription information
        if not state.get("subscription_info", {}):
            subscription_info = get_azure_subscription_info()
        else:
            subscription_info = state["subscription_info"]

        available_subscriptions = (
            ", ".join(subscription_info["available_subscriptions"])
            if subscription_info["available_subscriptions"]
            else "None available"
        )

        # Load the cloud architect prompt with variable substitution
        system_prompt = template_manager.get_prompt(
            AGENT_NAME,
            tools_description=tools_description,
            current_stage=state.get("current_stage", "initial"),
            default_subscription_name=subscription_info["default_subscription_name"],
            available_subscriptions=available_subscriptions,
            compliance_enforcement=compliance_enforcement,
            compliance_frameworks=compliance_frameworks,
            approval_required=approval_required,
            approval_received=approval_received,
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


def cloud_architect_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Cloud Architect Agent - Main orchestrator and requirements analyzer."""
    log_agent_start(AGENT_NAME, "Orchestrating workflow")

    conversation_history = state["conversation_history"]

    # Verify Azure CLI authentication
    if not verify_azure_auth(AGENT_NAME):
        error_msg = "Azure CLI authentication required"
        log_warning(AGENT_NAME, error_msg)
        return add_error_to_state(state, f"Cloud Architect error: {error_msg}")

    mcp_client = MultiMCPClient()
    mcp_client.add_custom_tools(
        "terraform_cli", get_terraform_tools(), terraform_tool_executor
    )
    mcp_client.add_custom_tools("iap_workflow", get_iap_tools(), iap_tool_executor)

    try:
        # Load response schema
        schema = load_agent_response_schema()

        # Run the ReAct workflow
        response, routing = run_cloud_architect_react_workflow(
            mcp_client=mcp_client,
            conversation_history=conversation_history,
            state=state,
            schema=schema,
        )
        conversation_history.append(
            f"Cloud Architect: {response}"
        )  # Append response to conversation history

        # Log the response content for debugging
        log_agent_response(AGENT_NAME, response)
        architect_target = determine_architect_target(routing)
        log_agent_complete(AGENT_NAME, f"Architect Target: {architect_target}")

        result_state = {
            **state,
            "current_agent": "cloud_architect",
            "conversation_history": conversation_history,
            "subscription_info": state.get("subscription_info", {}),
            "cloud_architect_analysis": response,
            "architect_target": architect_target,
        }

        return result_state

    except Exception as e:
        log_warning(AGENT_NAME, f"Orchestration failed: {str(e)}")

        errors = state.get("errors", [])
        return {
            **state,
            "current_agent": "cloud_architect",
            "errors": errors + [f"Cloud Architect error: {str(e)}"],
        }


def determine_architect_target(routing: str) -> str | None:
    """Determine Cloud Architect target."""

    routing_dictionary = {
        "INTERNAL_CLOUD_ENGINEER": "cloud_engineer",
        "INTERNAL_SECOPS_FINOPS": "secops_finops",
        "INTERNAL_DEVOPS": "devops",
        "APPROVAL_REQUEST": "human_approval",
        "CLARIFICATION_REQUIRED": "user",
        "ERROR_NOTIFICATION": "user",
        "DEPLOYMENT_COMPLETE": "user",
    }

    return routing_dictionary.get(routing, None)
