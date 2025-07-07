"""Cloud Engineer Agent node for LangGraph workflow."""

from datetime import date

from ...logging_system import (
    log_agent_complete,
    log_agent_response,
    log_agent_start,
    log_info,
    log_warning,
)
from ...templates.template_manager import template_manager
from ..state import InfrastructureStateDict, WorkflowStage
from ..terraform_utils import extract_terraform_template
from ..utils import add_error_to_state, make_llm_call

AGENT_NAME = "cloud_engineer"


def cloud_engineer_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Generate infrastructure templates based on Cloud Architect requirements."""
    log_agent_start(AGENT_NAME, "Processing requirements and generating templates")

    # Check for validation failures from previous attempts
    validation_result = state.get("template_validation_result", {})
    has_validation_failure = validation_result and not validation_result.get(
        "valid", True
    )
    validation_error = (
        validation_result.get("error", "") if has_validation_failure else ""
    )
    subscription_info = state["subscription_info"]
    current_date = str(date.today())
    system_prompt = template_manager.get_prompt(
        "cloud_engineer",
        current_stage=state.get("current_stage", "template_generation"),
        validation_error=validation_error,
        current_date=current_date,
        default_subscription_name=subscription_info.get("default_subscription_name"),
        default_subscription_id=subscription_info.get("default_subscription_id"),
    )
    conversation_history = state["conversation_history"]

    try:
        response = make_llm_call(
            system_prompt, "\n\n###\n\n".join(conversation_history)
        )
        conversation_history.append(
            f"Cloud Engineer: {response}"
        )  # Append response to conversation history

        # Extract Terraform template (needed for deployment)
        template_content = extract_terraform_template(response)

        # Consultation upon request
        needs_terraform_consultation = "TERRAFORM_CONSULTATION_NEEDED" in response

        # Debug logging
        log_info(
            AGENT_NAME,
            (
                f"Consultation decision: explicit_request={'TERRAFORM_CONSULTATION_NEEDED' in response}, "
                f"validation_failure={has_validation_failure}, final_decision={needs_terraform_consultation}"
            ),
        )

        # Log the response content for debugging
        log_agent_response(AGENT_NAME, response)

        log_agent_complete(
            AGENT_NAME,
            f"Response generated {'with template' if template_content else 'without template'}, "
            f"consultation {'required' if needs_terraform_consultation else 'not required'}",
        )

        # Determine if we need Terraform consultation
        needs_terraform_lookup = needs_terraform_consultation

        result_state = {
            **state,
            "current_stage": WorkflowStage.TEMPLATE_GENERATION.value,
            "conversation_history": conversation_history,
            "final_template": template_content,
            "secops_finops_analysis": "",
            "cloud_engineer_response": response,
            "needs_terraform_lookup": needs_terraform_lookup,
        }

        if needs_terraform_lookup and has_validation_failure:
            result_state["template_validation_result"] = None

        return result_state

    except Exception as e:
        log_warning(AGENT_NAME, f"Template generation failed: {str(e)}")
        return add_error_to_state(state, f"Cloud Engineer error: {str(e)}")
