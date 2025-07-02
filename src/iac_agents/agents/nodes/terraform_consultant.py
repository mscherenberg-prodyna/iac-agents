"""Terraform Consultant Agent node for LangGraph workflow."""

from typing import Optional

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import ListSortOrder, MessageRole
from azure.identity import DefaultAzureCredential

from ...config.settings import config
from ...logging_system import (
    log_agent_complete,
    log_agent_response,
    log_agent_start,
    log_warning,
)
from ...templates.template_manager import template_manager
from ..state import InfrastructureStateDict
from ..utils import get_agent_id

AGENT_NAME = "terraform_consultant"


def terraform_consultant_agent(
    state: InfrastructureStateDict,
) -> InfrastructureStateDict:
    """Terraform Consultant Agent - Documentation lookup and best practices via Azure AI."""
    log_agent_start(AGENT_NAME, "Providing Terraform guidance")

    system_prompt = template_manager.get_prompt(AGENT_NAME)
    conversation_history = state["conversation_history"]

    agent_id = state.get("terraform_consultant_id", None)

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
            "needs_pricing_lookup": False,
            "needs_terraform_lookup": False,
            "terraform_consultant_id": agent_id,
        }

        return result_state

    try:
        # Connect to Azure AI Foundry agent
        azure_response = query_azure_agent(
            agent_id, "\n\n###\n\n".join(conversation_history)
        )
        conversation_history.append(
            f"Terraform Consultant: {azure_response}"
        )  # Append response to conversation history

        if azure_response:
            log_agent_response(AGENT_NAME, azure_response)
            log_agent_complete(AGENT_NAME, "Azure AI guidance provided")

            # Always clear both lookup flags to prevent infinite loops
            result_state = {
                **state,
                "current_agent": "terraform_consultant",
                "conversation_history": conversation_history,
                "terraform_guidance": azure_response,
                "needs_pricing_lookup": False,
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
            "needs_pricing_lookup": False,
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
            "needs_pricing_lookup": False,
            "needs_terraform_lookup": False,
            "terraform_consultant_id": agent_id,
        }

        return result_state


def query_azure_agent(agent_id: str, terraform_query: str) -> Optional[str]:
    """Query the Azure AI Foundry Terraform Consultant agent."""
    try:
        credential = DefaultAzureCredential()
        agents_client = AgentsClient(
            endpoint=config.azure_ai.project_endpoint, credential=credential
        )

        thread = agents_client.threads.create()

        # Send terraform query to the agent
        message = agents_client.messages.create(
            thread_id=thread.id,
            role="user",
            content=terraform_query,
        )

        run = agents_client.runs.create_and_process(
            thread_id=thread.id, agent_id=agent_id
        )

        if run.status == "failed":
            log_warning(AGENT_NAME, f"Azure AI run failed: {run.last_error}")
            return None

        messages = agents_client.messages.list(
            thread_id=thread.id, order=ListSortOrder.ASCENDING
        )

        for message in messages:
            if message.text_messages and message.role == MessageRole.AGENT:
                return message.text_messages[-1].text.value

        return None

    except Exception as e:
        log_warning(AGENT_NAME, f"Azure AI query failed: {str(e)}")
        return None
