"""Cloud Architect Agent node for LangGraph workflow."""

import tempfile
from pathlib import Path
from typing import Any, Dict

from ...logging_system import (
    log_agent_complete,
    log_agent_response,
    log_agent_start,
    log_info,
    log_warning,
)
from ...templates.template_manager import template_manager
from ..state import InfrastructureStateDict
from ..terraform_utils import (
    run_terraform_command,
)
from ..utils import get_azure_subscription_info, make_llm_call

AGENT_NAME = "cloud_architect"


def cloud_architect_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Cloud Architect Agent - Main orchestrator and requirements analyzer."""
    log_agent_start(AGENT_NAME, "Orchestrating workflow")

    conversation_history = state["conversation_history"]

    try:
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

        # Determine workflow phase based on current state
        workflow_phase = determine_workflow_phase(state)

        # Validate terraform template if available and in validation phase
        template_validation_result = None
        template_validation_failed = False
        secops_finops_analysis = state.get("secops_finops_analysis", "")
        if workflow_phase == "validation" and not secops_finops_analysis:
            # Always run validation when in validation phase, regardless of previous results
            log_info(AGENT_NAME, "Validating terraform template with terraform plan")
            template_validation_result = validate_terraform_template(
                state.get("final_template")
            )

            # If template validation fails, route back to Cloud Engineer
            if not template_validation_result["valid"]:
                log_warning(
                    AGENT_NAME,
                    f"Template validation failed: {template_validation_result['error']}",
                )
                workflow_phase = (
                    "planning"  # Force back to planning to regenerate template
                )
                template_validation_failed = True

        if template_validation_failed:
            response_content = (
                f"Template validation failed: {template_validation_result['error']}"
            )
            conversation_history.append(
                f"Cloud Architect: {response_content}"
            )  # Append response to conversation history

        else:
            # Load the cloud architect prompt with variable substitution
            system_prompt = template_manager.get_prompt(
                AGENT_NAME,
                current_stage=state.get("current_stage", "initial"),
                default_subscription_name=subscription_info[
                    "default_subscription_name"
                ],
                available_subscriptions=available_subscriptions,
                compliance_enforcement=compliance_enforcement,
                compliance_frameworks=compliance_frameworks,
                approval_required=approval_required,
                approval_received=approval_received,
            )

            # Make LLM call using utility function
            response_content = make_llm_call(
                system_prompt, "\n\n###\n\n".join(conversation_history)
            )
            conversation_history.append(
                f"Cloud Architect: {response_content}"
            )  # Append response to conversation history

        # Log the response content for debugging
        log_agent_response(AGENT_NAME, response_content)
        log_agent_complete(AGENT_NAME, f"Workflow phase: {workflow_phase}")

        result_state = {
            **state,
            "current_agent": "cloud_architect",
            "conversation_history": conversation_history,
            "workflow_phase": workflow_phase,
            "subscription_info": subscription_info,
            "cloud_architect_analysis": response_content,
            "template_validation_result": template_validation_result,
        }

        # Set final_response only when we should communicate with user
        if template_validation_failed:
            result_state["architect_target"] = "cloud_engineer"
            log_agent_complete(
                AGENT_NAME,
                "Routing to Cloud Engineer due to template validation failure",
            )
        else:
            result_state["architect_target"] = determine_architect_target(
                response_content
            )
            log_agent_complete(
                AGENT_NAME,
                f"Next target: {result_state['architect_target']}",
            )

        return result_state

    except Exception as e:
        log_warning(AGENT_NAME, f"Orchestration failed: {str(e)}")

        errors = state.get("errors", [])
        return {
            **state,
            "current_agent": "cloud_architect",
            "errors": errors + [f"Cloud Architect error: {str(e)}"],
        }


def determine_workflow_phase(state: InfrastructureStateDict) -> str:
    """Determine the next workflow phase based on current state."""
    final_template = state.get("final_template", "")

    if not final_template:
        return "planning"
    if state.get("approval_received"):
        return "deployment"
    else:
        return "validation"


def validate_terraform_template(template_content: str) -> Dict[str, Any]:
    """Validate terraform template using terraform plan command.

    Args:
        template_content: The terraform template to validate
        user_requirements: User requirements for variable inference

    Returns:
        Dict with validation results including 'valid', 'error', 'output', 'details'
    """
    try:
        # Create temporary directory for validation
        with tempfile.TemporaryDirectory(prefix="terraform_validation_") as temp_dir:
            validation_dir = Path(temp_dir)
            log_info(AGENT_NAME, f"Created validation workspace: {validation_dir}")

            # Write terraform configuration
            main_tf_path = validation_dir / "main.tf"
            with open(main_tf_path, "w", encoding="utf-8") as f:
                f.write(template_content)

            log_info(AGENT_NAME, "Terraform configuration written for validation")

            # Run terraform init
            log_info(AGENT_NAME, "Running terraform init for validation...")
            init_result = run_terraform_command(
                validation_dir, ["terraform", "init"], timeout=120, context="Validation"
            )

            if not init_result["success"]:
                return {
                    "valid": False,
                    "error": f"Terraform init failed: {init_result['stderr']}",
                    "output": init_result["stdout"],
                    "details": {
                        "phase": "init",
                        "returncode": init_result["returncode"],
                    },
                }

            # Run terraform plan for validation
            log_info(AGENT_NAME, "Running terraform plan for validation...")
            plan_result = run_terraform_command(
                validation_dir,
                ["terraform", "plan", "-no-color"],
                timeout=120,
                context="Validation",
            )

            if plan_result["success"]:
                log_info(AGENT_NAME, "Template validation successful!")
                return {
                    "valid": True,
                    "error": None,
                    "output": plan_result["stdout"],
                    "details": {
                        "phase": "plan",
                        "returncode": plan_result["returncode"],
                    },
                }
            log_warning(
                AGENT_NAME,
                f"Template validation failed: {plan_result['stderr']}",
            )
            return {
                "valid": False,
                "error": f"Terraform plan validation failed: {plan_result['stderr']}",
                "output": plan_result["stdout"],
                "details": {
                    "phase": "plan",
                    "returncode": plan_result["returncode"],
                },
            }

    except Exception as e:
        log_warning(AGENT_NAME, f"Template validation exception: {str(e)}")
        return {
            "valid": False,
            "error": f"Validation process failed: {str(e)}",
            "output": "",
            "details": {"phase": "exception", "exception": str(e)},
        }


def determine_architect_target(response_content: str) -> str | None:
    """Determine Cloud Architect target."""

    # Target Cloud Engineer
    if "INTERNAL_CLOUD_ENGINEER" in response_content:
        return "cloud_engineer"

    # Target Sec/FinOps
    if "INTERNAL_SECOPS_FINOPS" in response_content:
        return "secops_finops"

    # Target DevOps
    if "INTERNAL_DEVOPS" in response_content:
        return "devops"

    # Check for User Response
    target = determine_user_response(response_content)

    return target


def determine_user_response(response_content: str) -> str | None:
    """Determine if Cloud Architect should generate a user-facing response."""

    # 1. CLARIFICATION NEEDED
    if "CLARIFICATION_REQUIRED" in response_content:
        log_info(AGENT_NAME, "Routing to User for clarification request")
        return "user"

    # 2. ERROR NOTIFICATION
    if "ERROR_NOTIFICATION" in response_content:
        log_warning(AGENT_NAME, "Routing to User because of error in workflow")
        return "user"

    # 3. APPROVAL REQUEST
    if "APPROVAL_REQUEST" in response_content:
        log_info(AGENT_NAME, "Routing to User for approval request")
        return "human_approval"

    # 4. DEPLOYMENT COMPLETE
    if "DEPLOYMENT_COMPLETE" in response_content:
        log_info(AGENT_NAME, "Routing to User for completed deployment")
        return "user"

    # Return None if no valid architect target was found
    return None
