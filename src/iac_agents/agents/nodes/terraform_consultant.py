"""Terraform Consultant Agent node for LangGraph workflow."""

from ...logging_system import (
    log_agent_complete,
    log_agent_response,
    log_agent_start,
    log_warning,
)
from ...templates.template_manager import template_manager
from ..state import InfrastructureStateDict
from ..utils import get_agent_id, query_azure_agent

AGENT_NAME = "terraform_consultant"


def terraform_consultant_agent(
    state: InfrastructureStateDict,
) -> InfrastructureStateDict:
    """Terraform Consultant Agent - Documentation lookup and best practices via Azure AI."""
    log_agent_start(AGENT_NAME, "Providing Terraform guidance")

    system_prompt = template_manager.get_prompt(AGENT_NAME)
    conversation_history = state["conversation_history"]

    agent_id = state.get("terraform_consultant_id", None)

    # Initialize Azure AI Foundry agent if it does not exist
    try:
        if not agent_id:
            agent_id = get_agent_id(agent_name=AGENT_NAME, prompt=system_prompt)
    except Exception as e:
        log_warning(AGENT_NAME, f"Error: {str(e)}")
        errors = state.get("errors", [])

        # Clear both flags to prevent infinite loops
        result_state = {
            **state,
            "current_agent": "terraform_consultant",
            "errors": errors + [f"Terraform Consultant error: {str(e)}"],
            "needs_terraform_lookup": False,
            "terraform_consultant_id": agent_id,
        }

        return result_state

    try:
        # Query Azure AI Foundry agent
        azure_response = query_azure_agent(
            AGENT_NAME, agent_id, "\n\n###\n\n".join(conversation_history)
        )
        conversation_history.append(
            f"Terraform Consultant: {azure_response}"
        )  # Append response to conversation history

        if azure_response:
            log_agent_response(AGENT_NAME, azure_response)
            log_agent_complete(AGENT_NAME, "Terraform Consultant guidance provided")

            # Always clear both lookup flags to prevent infinite loops
            result_state = {
                **state,
                "current_agent": "terraform_consultant",
                "conversation_history": conversation_history,
                "terraform_guidance": azure_response,
                "needs_terraform_lookup": False,
                "terraform_consultant_id": agent_id,
            }

            return result_state

        log_warning(AGENT_NAME, "Azure AI unavailable")
        errors = state.get("errors", [])

        # Clear both flags to prevent infinite loops
        result_state = {
            **state,
            "current_agent": "terraform_consultant",
            "errors": errors
            + ["Terraform Consultant Azure AI integration unavailable"],
            "needs_terraform_lookup": False,
            "terraform_consultant_id": agent_id,
        }

        return result_state

    except Exception as e:
        log_warning(AGENT_NAME, f"Error: {str(e)}")
        errors = state.get("errors", [])

        # Clear both flags to prevent infinite loops
        result_state = {
            **state,
            "current_agent": "terraform_consultant",
            "errors": errors + [f"Terraform Consultant error: {str(e)}"],
            "needs_terraform_lookup": False,
            "terraform_consultant_id": agent_id,
        }

        return result_state
