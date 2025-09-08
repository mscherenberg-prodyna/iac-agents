"""Cloud Engineer Agent node for LangGraph workflow."""

import asyncio
import json
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from ...logging_system import (log_agent_response, log_agent_start, log_info,
                               log_warning)
from ...templates.template_manager import template_manager
from ..iap_workflow_utils import get_iap_tools, iap_tool_executor
from ..mcp_utils import MultiMCPClient
from ..react_agent import agent_react_step
from ..state import InfrastructureStateDict, WorkflowStage
from ..terraform_utils import get_terraform_tools, terraform_tool_executor
from ..utils import (add_error_to_state, get_azure_subscription_info,
                     load_agent_response_schema, verify_azure_auth)

AGENT_NAME = "cloud_engineer"


def run_cloud_engineer_react_workflow(
    mcp_client: MultiMCPClient,
    conversation_history: List[str],
    state: InfrastructureStateDict,
    schema: dict,
) -> Tuple[str, str | None]:
    """Sync wrapper for Cloud Engineer ReAct workflow."""

    async def _async_workflow():
        # Get tools description within session context
        async with mcp_client.session() as session:
            tools_list = await mcp_client.list_tools(session)

        # Format tools for consistency
        tools_description = "\n".join(
            [f"- {tool['name']}: {tool['description']}" for tool in tools_list]
        )

        # Get Azure subscription information
        if not state.get("subscription_info", {}):
            subscription_info = get_azure_subscription_info()
        else:
            subscription_info = state["subscription_info"]

        system_prompt = template_manager.get_prompt(
            AGENT_NAME,
            tools_description=tools_description,
            azure_info=subscription_info,
            working_dir=f"{Path.cwd()}/tmp_data",
            current_date=datetime.now().strftime("%Y-%m-%d"),
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


def cloud_engineer_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Generate infrastructure templates based on Cloud Architect requirements."""
    log_agent_start(AGENT_NAME, "Generating infrastructure template")

    conversation_history = state.get("conversation_history", [])

    # Verify Azure CLI authentication
    if not verify_azure_auth(AGENT_NAME):
        error_msg = "Azure CLI authentication required"
        log_warning(AGENT_NAME, error_msg)
        return add_error_to_state(state, f"Cloud Engineer agent error: {error_msg}")

    mcp_client = MultiMCPClient()
    mcp_client.add_custom_tools(
        "terraform_cli", get_terraform_tools(), terraform_tool_executor
    )
    mcp_client.add_custom_tools("iap_workflow", get_iap_tools(), iap_tool_executor)

    try:
        # Load response schema
        schema = load_agent_response_schema()

        # Run the ReAct workflow
        response, routing = run_cloud_engineer_react_workflow(
            mcp_client=mcp_client,
            conversation_history=conversation_history,
            state=state,
            schema=schema,
        )
        conversation_history.append(
            f"Cloud Engineer: {response}"
        )  # Append response to conversation history

        # Consultation upon request
        needs_terraform_lookup = (
            "TERRAFORM_CONSULTATION_NEEDED" in routing if routing else False
        )

        # Save template in state if generated
        if os.path.exists(f"{Path.cwd()}/tmp_data/main.tf"):
            with open(f"{Path.cwd()}/tmp_data/main.tf", "r", encoding="utf-8") as f:
                template_content = f.read()
            state["final_template"] = template_content
            log_info(AGENT_NAME, "Terraform template generated successfully")
        else:
            log_warning(AGENT_NAME, "No Terraform template was generated")

        # Debug logging
        log_info(
            AGENT_NAME,
            f"Consultation decision: explicit_request={needs_terraform_lookup}",
        )

        # Log the response
        log_agent_response(AGENT_NAME, response)

        result_state = {
            **state,
            "current_stage": WorkflowStage.TEMPLATE_GENERATION.value,
            "conversation_history": conversation_history,
            "secops_finops_analysis": "",
            "cloud_engineer_response": response,
            "needs_terraform_lookup": needs_terraform_lookup,
        }

        return result_state

    except Exception as e:
        log_warning(AGENT_NAME, f"Template generation failed: {str(e)}")
        log_warning(AGENT_NAME, f"Stack trace: {traceback.format_exc()}")
        return add_error_to_state(state, f"Cloud Engineer error: {str(e)}")
