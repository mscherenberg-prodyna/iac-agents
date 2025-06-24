"""Terraform Consultant Agent node for LangGraph workflow."""

from typing import Optional

from azure.ai.agents.models import ListSortOrder, MessageRole
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from ...config.settings import config
from ...logging_system import log_agent_complete, log_agent_start, log_warning
from ..state import InfrastructureStateDict


def terraform_consultant_agent(
    state: InfrastructureStateDict,
) -> InfrastructureStateDict:
    """Terraform Consultant Agent - Documentation lookup and best practices via Azure AI."""
    log_agent_start("Terraform Consultant", "Providing Terraform guidance")

    # Get the specific query from the calling agent
    terraform_query = ""
    query_source = ""

    # Check if this is a Cloud Engineer query
    if state.get("needs_terraform_lookup"):
        terraform_query = state.get("cloud_engineer_response", "")
        query_source = "Cloud Engineer"

    # Check if this is a SecOps/FinOps pricing query
    elif state.get("needs_pricing_lookup"):
        terraform_query = state.get("secops_finops_analysis", "")
        query_source = "SecOps/FinOps"

    # If we don't have a meaningful query, this is an error in the workflow
    if not terraform_query or not terraform_query.strip():
        log_warning(
            "Terraform Consultant",
            f"No meaningful query from {query_source or 'unknown source'}",
        )
        errors = state.get("errors", [])

        # Clear both lookup flags to prevent infinite loops
        result_state = {
            **state,
            "current_agent": "terraform_consultant",
            "errors": errors
            + [
                f"Terraform Consultant called without valid query from {query_source or 'unknown source'}"
            ],
            "needs_terraform_lookup": False,
            "needs_pricing_lookup": False,
        }

        # Clear the specific query fields to avoid reusing them
        if "terraform_pricing_query" in result_state:
            del result_state["terraform_pricing_query"]

        return result_state

    try:
        # Try to connect to Azure AI Foundry agent
        azure_response = _query_azure_agent(terraform_query)

        if azure_response:
            log_agent_complete("Terraform Consultant", "Azure AI guidance provided")

            # Always clear both lookup flags to prevent infinite loops
            result_state = {
                **state,
                "current_agent": "terraform_consultant",
                "terraform_guidance": azure_response,
                "needs_pricing_lookup": False,
                "needs_terraform_lookup": False,
                # Keep terraform_consultant_caller for routing - will be cleared by receiving agent
            }

            return result_state
        else:
            log_warning("Terraform Consultant", "Azure AI unavailable")
            errors = state.get("errors", [])

            # Clear both flags to prevent infinite loops
            result_state = {
                **state,
                "current_agent": "terraform_consultant",
                "errors": errors
                + ["Terraform Consultant Azure AI integration unavailable"],
                "needs_pricing_lookup": False,
                "needs_terraform_lookup": False,
            }

            return result_state

    except Exception as e:
        log_warning("Terraform Consultant", f"Error: {str(e)}")
        errors = state.get("errors", [])

        # Clear both flags to prevent infinite loops
        result_state = {
            **state,
            "current_agent": "terraform_consultant",
            "errors": errors + [f"Terraform Consultant error: {str(e)}"],
            "needs_pricing_lookup": False,
            "needs_terraform_lookup": False,
        }

        return result_state


def _query_azure_agent(terraform_query: str) -> Optional[str]:
    """Query the Azure AI Foundry Terraform Consultant agent."""
    try:
        endpoint = config.azure_ai.project_endpoint
        agent_id = config.azure_ai.agent_id

        if not endpoint or not agent_id:
            log_warning("Terraform Consultant", "Azure AI configuration missing")
            return None

        if not terraform_query or not terraform_query.strip():
            log_warning("Terraform Consultant", "Empty query provided")
            return None

        project = AIProjectClient(
            credential=DefaultAzureCredential(), endpoint=endpoint
        )

        agent = project.agents.get_agent(agent_id)
        thread = project.agents.threads.create()

        # Send terraform query to the agent
        message = project.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content=terraform_query,
        )

        run = project.agents.runs.create_and_process(
            thread_id=thread.id, agent_id=agent.id
        )

        if run.status == "failed":
            log_warning(
                "Terraform Consultant", f"Azure AI run failed: {run.last_error}"
            )
            return None

        messages = project.agents.messages.list(
            thread_id=thread.id, order=ListSortOrder.ASCENDING
        )

        for message in messages:
            if message.text_messages and message.role == MessageRole.AGENT:
                return message.text_messages[-1].text.value

        return None

    except Exception as e:
        log_warning("Terraform Consultant", f"Azure AI query failed: {str(e)}")
        return None


# TODO: Use this function to update the Azure AI agent prompt dynamically
# def update_azure_agent_prompt(prompt_content: str) -> bool:
#     """Update the remote Azure AI agent with current prompt content."""
#     try:
#         endpoint = config.azure_ai.project_endpoint
#         agent_id = config.azure_ai.agent_id

#         if not endpoint or not agent_id:
#             log_warning(
#                 "Terraform Consultant",
#                 "Azure AI configuration missing for prompt update",
#             )
#             return False

#         project = AIProjectClient(
#             credential=DefaultAzureCredential(), endpoint=endpoint
#         )

#         # Get current agent to preserve other settings
#         current_agent = project.agents.get_agent(agent_id)

#         # Update agent with new instructions while preserving other properties
#         updated_agent = project.agents.update_agent(
#             agent_id=agent_id,
#             model=current_agent.model,
#             name=current_agent.name,
#             description=current_agent.description,
#             instructions=prompt_content,
#             tools=current_agent.tools,
#             tool_resources=current_agent.tool_resources,
#             metadata=current_agent.metadata,
#             temperature=current_agent.temperature,
#             top_p=current_agent.top_p,
#             response_format=current_agent.response_format,
#         )

#         if updated_agent:
#             log_agent_complete(
#                 "Terraform Consultant",
#                 "Azure AI agent instructions updated successfully",
#             )
#             return True
#         else:
#             log_warning(
#                 "Terraform Consultant", "Failed to update Azure AI agent instructions"
#             )
#             return False

#     except Exception as e:
#         log_warning("Terraform Consultant", f"Prompt update failed: {str(e)}")
#         return False
