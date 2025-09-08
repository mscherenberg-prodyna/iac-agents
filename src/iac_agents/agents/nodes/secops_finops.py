"""SecOps/FinOps Engineer Agent node for LangGraph workflow."""

from ...logging_system import log_agent_response, log_agent_start, log_warning
from ...templates.template_manager import template_manager
from ..state import InfrastructureStateDict, WorkflowStage
from ..utils import add_error_to_state, get_agent_id_bing, query_azure_agent

AGENT_NAME = "secops_finops"


def secops_finops_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """SecOps/FinOps Agent - Compliance validation and cost estimation."""
    log_agent_start(AGENT_NAME, "Validating compliance and estimating costs")

    template_content = state.get("final_template", "")
    compliance_settings = state.get("compliance_settings", {})
    compliance_enforcement = (
        "Enabled"
        if compliance_settings.get("enforce_compliance", False)
        else "Disabled"
    )
    compliance_frameworks = (
        ", ".join(compliance_settings.get("selected_frameworks", [])) or "None selected"
    )
    system_prompt = template_manager.get_prompt(
        AGENT_NAME,
        template_content=template_content,
        compliance_enforcement=compliance_enforcement,
        compliance_frameworks=compliance_frameworks,
        compliance_requirements=str(compliance_settings),
    )
    conversation_history = state["conversation_history"]

    try:
        agent_id = get_agent_id_bing(agent_name=AGENT_NAME, prompt=system_prompt)

    except Exception as e:
        log_warning(AGENT_NAME, f"AI Foundry error: {str(e)}")
        return add_error_to_state(state, f"SecOps/FinOps error: {str(e)}")

    try:
        # Query Azure AI Foundry agent
        azure_response = query_azure_agent(
            AGENT_NAME, agent_id, "\n\n###\n\n".join(conversation_history)
        )
        conversation_history.append(
            f"SecOps/FinOps: {azure_response}"
        )  # Append response to conversation history

        if azure_response:
            log_agent_response(AGENT_NAME, azure_response)

            # Always clear both lookup flags to prevent infinite loops
            result_state = {
                **state,
                "current_agent": "secops_finops",
                "conversation_history": conversation_history,
                "current_stage": WorkflowStage.VALIDATION_AND_COMPLIANCE.value,
                "secops_finops_analysis": azure_response,
            }

            return result_state

        log_warning(AGENT_NAME, "Azure AI unavailable")
        errors = state.get("errors", [])

        result_state = {
            **state,
            "current_agent": "secops_finops",
            "errors": errors + ["SecOps/FinOps Azure AI integration unavailable"],
        }

        return result_state

    except Exception as e:
        log_warning(AGENT_NAME, f"Validation failed: {str(e)}")
        return add_error_to_state(state, f"SecOps/FinOps error: {str(e)}")
