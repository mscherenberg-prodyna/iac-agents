"""Terraform Consultant Agent node for LangGraph workflow."""

from typing import Optional

from azure.ai.agents.models import ListSortOrder, MessageRole
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from ...config.settings import config
from ...logging_system import (
    log_agent_complete,
    log_agent_response,
    log_agent_start,
    log_warning,
)
from ..state import InfrastructureStateDict

AGENT_NAME = "Terraform Consultant"


def terraform_consultant_agent(
    state: InfrastructureStateDict,
) -> InfrastructureStateDict:
    """Terraform Consultant Agent - Documentation lookup and best practices via Azure AI."""
    log_agent_start(AGENT_NAME, "Providing Terraform guidance")

    conversation_history = state["conversation_history"]

    try:
        # Try to connect to Azure AI Foundry agent
        azure_response = _query_azure_agent("\n\n###\n\n".join(conversation_history))
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
        }

        return result_state


def _query_azure_agent(terraform_query: str) -> Optional[str]:
    """Query the Azure AI Foundry Terraform Consultant agent."""
    try:
        agent, project = get_azure_agent()

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
            log_warning(AGENT_NAME, f"Azure AI run failed: {run.last_error}")
            return None

        messages = project.agents.messages.list(
            thread_id=thread.id, order=ListSortOrder.ASCENDING
        )

        for message in messages:
            if message.text_messages and message.role == MessageRole.AGENT:
                return message.text_messages[-1].text.value

        return None

    except Exception as e:
        log_warning(AGENT_NAME, f"Azure AI query failed: {str(e)}")
        return None


def get_azure_agent(prompt_content: str) -> bool:
    """Update the remote Azure AI agent with current prompt content."""
    try:
        endpoint = config.azure_ai.project_endpoint
        agent_id = config.azure_ai.agent_id

        if not endpoint or not agent_id:
            log_warning(AGENT_NAME, "Azure AI configuration missing")
            return None

        if not terraform_query or not terraform_query.strip():
            log_warning(AGENT_NAME, "Empty query provided")
            return None

        project = AIProjectClient(
            credential=DefaultAzureCredential(), endpoint=endpoint
        )

        agent = project.agents.get_agent(agent_id)

        endpoint = config.azure_ai.project_endpoint
        agent_id = config.azure_ai.agent_id

        if not endpoint or not agent_id:
            log_warning(
                AGENT_NAME,
                "Azure AI configuration missing for prompt update",
            )
            return False

        project = AIProjectClient(
            credential=DefaultAzureCredential(), endpoint=endpoint
        )

        # Get current agent to preserve other settings
        current_agent = project.agents.get_agent(agent_id)

        # Update agent with new instructions while preserving other properties
        updated_agent = project.agents.update_agent(
            agent_id=agent_id,
            model=current_agent.model,
            name=current_agent.name,
            description=current_agent.description,
            instructions=prompt_content,
            tools=current_agent.tools,
            tool_resources=current_agent.tool_resources,
            metadata=current_agent.metadata,
            temperature=current_agent.temperature,
            top_p=current_agent.top_p,
            response_format=current_agent.response_format,
        )

        if updated_agent:
            log_agent_complete(
                AGENT_NAME,
                "Azure AI agent instructions updated successfully",
            )
            return True
        else:
            log_warning(AGENT_NAME, "Failed to update Azure AI agent instructions")
            return False

    except Exception as e:
        log_warning(AGENT_NAME, f"Prompt update failed: {str(e)}")
        return False
