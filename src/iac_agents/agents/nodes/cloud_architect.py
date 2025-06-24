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
    TerraformVariableManager,
    enhance_terraform_template,
    run_terraform_command,
)
from ..utils import get_azure_subscription_info, make_llm_call


def cloud_architect_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Cloud Architect Agent - Main orchestrator and requirements analyzer."""
    log_agent_start(
        "Cloud Architect", "Analyzing requirements and orchestrating workflow"
    )

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
        workflow_phase = _determine_workflow_phase(state)

        # Track phase iterations for loop detection
        phase_iterations = state.get("phase_iterations", {})
        current_iterations = phase_iterations.get(workflow_phase, 0)
        phase_iterations[workflow_phase] = current_iterations + 1

        # Validate terraform template if available and in validation phase
        template_validation_result = None
        template_validation_failed = False
        if workflow_phase == "validation" and state.get("final_template"):
            # Always run validation when in validation phase, regardless of previous results
            log_info(
                "Cloud Architect", "Validating terraform template with terraform plan"
            )
            template_validation_result = _validate_terraform_template(
                state.get("final_template"), state.get("user_input", "")
            )

            # If template validation fails, route back to Cloud Engineer
            if not template_validation_result["valid"]:
                log_warning(
                    "Cloud Architect",
                    f"Template validation failed: {template_validation_result['error']}",
                )
                workflow_phase = (
                    "planning"  # Force back to planning to regenerate template
                )
                template_validation_failed = True
        elif workflow_phase == "validation" and not state.get("final_template"):
            # If we're in validation phase but no template exists, go back to planning
            log_warning(
                "Cloud Architect",
                "In validation phase but no template found, returning to planning",
            )
            workflow_phase = "planning"

        if template_validation_failed:

            response_content = (
                f"Template validation failed: {template_validation_result['error']}"
            )
            conversation_history.append(
                f"Cloud Architect: {response_content}"
            )  # Append response to conversation history
            should_respond_to_user = False

        else:

            # Load the cloud architect prompt with variable substitution
            system_prompt = template_manager.get_prompt(
                "cloud_architect",
                current_stage=state.get("current_stage", "initial"),
                completed_stages=", ".join(state.get("completed_stages", [])),
                default_subscription_name=subscription_info[
                    "default_subscription_name"
                ],
                available_subscriptions=available_subscriptions,
                compliance_enforcement=compliance_enforcement,
                compliance_frameworks=compliance_frameworks,
                approval_required=approval_required,
            )

            # Make LLM call using utility function
            response_content = make_llm_call(
                system_prompt, "\n\n###\n\n".join(conversation_history)
            )
            conversation_history.append(
                f"Cloud Architect: {response_content}"
            )  # Append response to conversation history

            # Determine if this should be a user-facing response based on state AND response content
            should_respond_to_user = _should_generate_user_response(
                state, response_content
            )

        # Log the response content for debugging
        log_agent_response("Cloud Architect", response_content)
        log_agent_complete("Cloud Architect", f"Workflow phase: {workflow_phase}")

        # Mark validation_and_compliance as completed only when template validation passes
        completed_stages = state.get("completed_stages", [])
        if (
            template_validation_result
            and template_validation_result.get("valid")
            and "validation_and_compliance" not in completed_stages
        ):
            completed_stages = completed_stages + ["validation_and_compliance"]

        result_state = {
            **state,
            "current_agent": "cloud_architect",
            "conversation_history": conversation_history,
            "workflow_phase": workflow_phase,
            "subscription_info": subscription_info,
            "phase_iterations": phase_iterations,
            "cloud_architect_analysis": response_content,
            "template_validation_result": template_validation_result,
            "completed_stages": completed_stages,
        }

        # Set final_response only when we should communicate with user
        if should_respond_to_user:
            result_state["final_response"] = response_content
            log_agent_complete("Cloud Architect", "Generated user response")
        else:
            result_state["final_response"] = None
            log_agent_complete("Cloud Architect", "Internal coordination only")

        return result_state

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
    current_phase = state.get("workflow_phase", "planning")

    # Loop detection: if we're in the same phase and have consulted Terraform multiple times
    phase_iterations = state.get("phase_iterations", {})
    current_iterations = phase_iterations.get(current_phase, 0)

    # If we've been in the same phase for too many iterations, force progression
    if current_iterations >= 3:
        if current_phase == "validation":
            # Force completion of validation if stuck
            return "approval" if state.get("requires_approval") else "complete"
        elif current_phase == "planning":
            return "validation"

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


def _should_generate_user_response(
    state: InfrastructureStateDict, response_content: str
) -> bool:
    """Determine if Cloud Architect should generate a user-facing response."""
    errors = state.get("errors", [])
    workflow_phase = state.get("workflow_phase", "planning")

    # 1. ERROR NOTIFICATION - if there are errors
    if errors:
        log_warning("Cloud Architect", f"Routing to User because of: {errors}")
        return True

    # 2. APPROVAL REQUEST - if validation is complete and approval workflow reached
    if workflow_phase == "approval":
        log_info("Cloud Architect", "Routing to User for approval request")
        return True

    # 3. DEPLOYMENT COMPLETE - if deployment is finished
    if workflow_phase == "deployment" and state.get("deployment_status") == "completed":
        log_info("Cloud Architect", "Routing to User for completed deployment")
        return True

    # 4. WORKFLOW COMPLETE - if workflow has reached completion
    if workflow_phase == "complete":
        log_info("Cloud Architect", "Routing to User for completed workflow")
        return True

    # 5. CLARIFICATION NEEDED - if LLM explicitly requests clarification
    if "CLARIFICATION_REQUIRED" in response_content:
        log_info("Cloud Architect", "Routing to User for clarification request")
        return True

    # All other cases: internal coordination only
    return False


def _validate_terraform_template(
    template_content: str, user_requirements: str = ""
) -> Dict[str, Any]:
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
            log_info(
                "Cloud Architect", f"Created validation workspace: {validation_dir}"
            )

            # Enhance template with variable management
            is_valid, issues = TerraformVariableManager.validate_template_variables(
                template_content
            )

            if not is_valid:
                log_info(
                    "Cloud Architect", f"Template validation issues found: {issues}"
                )
                # Infer variable values from user requirements
                inferred_values = (
                    TerraformVariableManager.infer_variable_values_from_requirements(
                        user_requirements
                    )
                )
                log_info(
                    "Cloud Architect", f"Inferred variable values: {inferred_values}"
                )

                # Enhance template with inferred defaults
                enhanced_template = (
                    TerraformVariableManager.enhance_template_with_defaults(
                        template_content, inferred_values
                    )
                )
                log_info(
                    "Cloud Architect",
                    "Template enhanced with inferred variable defaults",
                )
            else:
                enhanced_template = template_content
                log_info(
                    "Cloud Architect",
                    "Template validation passed, using original template",
                )

            # Add standard provider configuration if not present
            enhanced_template = enhance_terraform_template(
                enhanced_template, context="validation"
            )

            # Write terraform configuration
            main_tf_path = validation_dir / "main.tf"
            with open(main_tf_path, "w", encoding="utf-8") as f:
                f.write(enhanced_template)

            log_info(
                "Cloud Architect", "Terraform configuration written for validation"
            )

            # Run terraform init
            log_info("Cloud Architect", "Running terraform init for validation...")
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
            log_info("Cloud Architect", "Running terraform plan for validation...")
            plan_result = run_terraform_command(
                validation_dir, ["terraform", "plan"], timeout=120, context="Validation"
            )

            if plan_result["success"]:
                log_info("Cloud Architect", "Template validation successful!")
                return {
                    "valid": True,
                    "error": None,
                    "output": plan_result["stdout"],
                    "details": {
                        "phase": "plan",
                        "returncode": plan_result["returncode"],
                    },
                }
            else:
                log_warning(
                    "Cloud Architect",
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
        log_warning("Cloud Architect", f"Template validation exception: {str(e)}")
        return {
            "valid": False,
            "error": f"Validation process failed: {str(e)}",
            "output": "",
            "details": {"phase": "exception", "exception": str(e)},
        }
