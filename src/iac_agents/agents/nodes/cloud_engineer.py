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
from ..state import InfrastructureStateDict, TemplateGenerationResult, WorkflowStage
from ..utils import (
    add_error_to_state,
    extract_terraform_template,
    make_llm_call,
    mark_stage_completed,
)

AGENT_NAME = "Cloud Engineer"


def cloud_engineer_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Generate infrastructure templates based on Cloud Architect requirements."""
    log_agent_start(AGENT_NAME, "Processing requirements and generating templates")

    conversation_history = state["conversation_history"]

    try:
        # Check if terraform research is enabled
        deployment_config = state.get("deployment_config", {})
        terraform_enabled = deployment_config.get("terraform_research_enabled", True)

        # Check for validation failures from previous attempts
        validation_result = state.get("template_validation_result", {})
        has_validation_failure = validation_result and not validation_result.get(
            "valid", True
        )
        validation_error = (
            validation_result.get("error", "") if has_validation_failure else ""
        )
        log_info(
            AGENT_NAME,
            f"Validation check: has_failure={has_validation_failure}, error_length={len(validation_error) if validation_error else 0}",
        )

        subscription_info = state["subscription_info"]
        current_date = str(date.today())

        # Load the cloud engineer prompt with Cloud Architect's analysis
        system_prompt = template_manager.get_prompt(
            "cloud_engineer",
            current_stage=state.get("current_stage", "template_generation"),
            terraform_consultant_available=terraform_enabled,
            validation_error=validation_error,
            current_date=current_date,
            default_subscription_name=subscription_info.get(
                "default_subscription_name"
            ),
            default_subscription_id=subscription_info.get("default_subscription_id"),
        )

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
            f"Consultation decision: explicit_request={'TERRAFORM_CONSULTATION_NEEDED' in response}, validation_failure={has_validation_failure}, final_decision={needs_terraform_consultation}",
        )

        # Create result with extracted template
        result = TemplateGenerationResult(
            status="completed",
            data={
                "full_response": response,
                "has_template": bool(template_content),
                "needs_terraform_consultation": needs_terraform_consultation,
            },
            template_content=template_content,
            provider="azure" if template_content else None,
            resources_count=(
                template_content.count("resource ") if template_content else 0
            ),
        )

        # Mark stage as completed
        new_completed_stages = mark_stage_completed(
            state, WorkflowStage.TEMPLATE_GENERATION.value
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
            "completed_stages": new_completed_stages,
            "template_generation_result": result.model_dump(),
            "final_template": template_content,
            "cloud_engineer_response": response,
            "needs_terraform_lookup": needs_terraform_lookup,
            # Clear caller if we were called back from Terraform Consultant
            "terraform_consultant_caller": (
                None
                if state.get("terraform_consultant_caller") == "cloud_engineer"
                else state.get("terraform_consultant_caller")
            ),
        }

        # Set caller info if requesting Terraform consultation
        if needs_terraform_lookup:
            result_state["terraform_consultant_caller"] = "cloud_engineer"
            # Clear validation failure after triggering consultation to prevent loops
            if has_validation_failure:
                result_state["template_validation_result"] = None

        return result_state

    except Exception as e:
        log_warning(AGENT_NAME, f"Template generation failed: {str(e)}")

        # Update errors
        new_errors = add_error_to_state(state, f"Cloud Engineer failed: {str(e)}")

        return {
            **state,
            "current_stage": WorkflowStage.TEMPLATE_GENERATION.value,
            "errors": new_errors,
        }
