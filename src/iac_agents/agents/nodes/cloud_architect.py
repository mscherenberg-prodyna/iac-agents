"""Cloud Architect Agent node for LangGraph workflow."""

from langchain_openai import AzureChatOpenAI

from ...config.settings import config
from ...logging_system import log_agent_complete, log_agent_start, log_warning
from ...templates.template_manager import template_manager
from ..state import InfrastructureStateDict


def cloud_architect_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Cloud Architect Agent - Main orchestrator and requirements analyzer."""
    log_agent_start(
        "Cloud Architect", "Analyzing requirements and orchestrating workflow"
    )

    user_input = state["user_input"]

    try:
        # Load the cloud architect prompt with variable substitution
        system_prompt = template_manager.get_prompt(
            "cloud_architect",
            user_request=user_input,
            current_stage=state.get("current_stage", "initial"),
            completed_stages=", ".join(state.get("completed_stages", [])),
        )

        # Initialize Azure OpenAI with config
        llm = AzureChatOpenAI(
            azure_endpoint=config.azure_openai.endpoint,
            azure_deployment=config.azure_openai.deployment,
            api_version=config.azure_openai.api_version,
            api_key=config.azure_openai.api_key,
            temperature=config.agents.default_temperature,
            max_tokens=config.agents.max_response_tokens,
        )

        # Make LLM call
        messages = [("system", system_prompt), ("human", user_input)]
        response = llm.invoke(messages)

        # Determine workflow phase based on current state
        workflow_phase = _determine_workflow_phase(state)

        # Set flags for specialized agents based on user input and LLM response
        needs_terraform_lookup = (
            "terraform" in user_input.lower() or "terraform" in response.content.lower()
        )
        needs_pricing_lookup = (
            "cost" in user_input.lower() or "pricing" in response.content.lower()
        )

        log_agent_complete("Cloud Architect", f"Workflow phase: {workflow_phase}")

        return {
            **state,
            "current_agent": "cloud_architect",
            "workflow_phase": workflow_phase,
            "needs_terraform_lookup": needs_terraform_lookup,
            "needs_pricing_lookup": needs_pricing_lookup,
            "cloud_architect_analysis": response.content,
        }

    except Exception as e:
        log_warning("Cloud Architect", f"Orchestration failed: {str(e)}")

        errors = state.get("errors", [])
        return {
            **state,
            "current_agent": "cloud_architect",
            "errors": errors + [f"Cloud Architect error: {str(e)}"],
        }


def _determine_workflow_phase(state: InfrastructureStateDict) -> str:
    """Determine the next workflow phase based on current state."""
    completed_stages = state.get("completed_stages", [])

    if not completed_stages:
        return "planning"

    if (
        "template_generation" in completed_stages
        and "validation_and_compliance" not in completed_stages
    ):
        return "validation"

    if "validation_and_compliance" in completed_stages and not state.get(
        "approval_received"
    ):
        return "approval"

    if state.get("approval_received"):
        return "deployment"

    return "complete"
