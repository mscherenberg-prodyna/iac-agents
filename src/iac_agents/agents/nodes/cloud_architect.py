"""Cloud Architect Agent node for LangGraph workflow."""

import subprocess
import json
from typing import Dict, Any

from ...logging_system import log_agent_complete, log_agent_start, log_warning, log_agent_response
from ...templates.template_manager import template_manager
from ..state import InfrastructureStateDict
from ..utils import make_llm_call


def _get_azure_subscription_info() -> Dict[str, Any]:
    """Get Azure subscription information using Azure CLI."""
    try:
        # Run az account list command to get subscription information
        result = subprocess.run(
            ["az", "account", "list", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            subscriptions = json.loads(result.stdout)
            
            # Find the default subscription
            default_sub = None
            for sub in subscriptions:
                if sub.get("isDefault", False):
                    default_sub = sub
                    break
            
            if default_sub:
                return {
                    "default_subscription_name": default_sub.get("name", "Unknown"),
                    "default_subscription_id": default_sub.get("id", "Unknown"),
                    "total_subscriptions": len(subscriptions),
                    "available_subscriptions": [sub.get("name", "Unknown") for sub in subscriptions]
                }
            else:
                return {
                    "default_subscription_name": "None (not logged in)",
                    "default_subscription_id": "Unknown",
                    "total_subscriptions": 0,
                    "available_subscriptions": []
                }
        else:
            return {
                "default_subscription_name": "Azure CLI error",
                "default_subscription_id": "Unknown", 
                "total_subscriptions": 0,
                "available_subscriptions": []
            }
            
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return {
            "default_subscription_name": "Azure CLI not available",
            "default_subscription_id": "Unknown",
            "total_subscriptions": 0, 
            "available_subscriptions": []
        }


def cloud_architect_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Cloud Architect Agent - Main orchestrator and requirements analyzer."""
    log_agent_start(
        "Cloud Architect", "Analyzing requirements and orchestrating workflow"
    )

    user_input = state["user_input"]

    try:
        # Prepare context for the Cloud Architect
        context_info = _prepare_agent_context(state)
        
        # Extract configuration settings from state
        compliance_settings = state.get("compliance_settings", {})
        compliance_enforcement = "Enabled" if compliance_settings.get("enforce_compliance", False) else "Disabled"
        compliance_frameworks = ", ".join(compliance_settings.get("selected_frameworks", [])) or "None selected"
        approval_required = "Yes" if state.get("requires_approval", True) else "No"
        
        # Get Azure subscription information
        subscription_info = _get_azure_subscription_info()
        available_subscriptions = ", ".join(subscription_info["available_subscriptions"]) if subscription_info["available_subscriptions"] else "None available"

        # Load the cloud architect prompt with variable substitution
        system_prompt = template_manager.get_prompt(
            "cloud_architect",
            user_request=user_input,
            current_stage=state.get("current_stage", "initial"),
            completed_stages=", ".join(state.get("completed_stages", [])),
            agent_context=context_info,
            default_subscription_name=subscription_info["default_subscription_name"],
            available_subscriptions=available_subscriptions,
            should_respond_to_user="False",  # Will be determined after response analysis
            compliance_enforcement=compliance_enforcement,
            compliance_frameworks=compliance_frameworks,
            approval_required=approval_required,
        )

        # Make LLM call using utility function
        response_content = make_llm_call(system_prompt, user_input)

        # Determine workflow phase based on current state
        workflow_phase = _determine_workflow_phase(state)
        
        # Track phase iterations for loop detection
        phase_iterations = state.get("phase_iterations", {})
        current_iterations = phase_iterations.get(workflow_phase, 0)
        phase_iterations[workflow_phase] = current_iterations + 1

        # Set flags for specialized agents based on user input and LLM response
        needs_terraform_lookup = (
            "terraform" in user_input.lower() or "terraform" in response_content.lower()
        )
        needs_pricing_lookup = (
            "cost" in user_input.lower() or "pricing" in response_content.lower()
        )

        # Determine if this should be a user-facing response based on state AND response content
        should_respond_to_user = _should_generate_user_response(state, response_content)
        
        # Log the response content for debugging
        log_agent_response("Cloud Architect", response_content)
        log_agent_complete("Cloud Architect", f"Workflow phase: {workflow_phase}")

        result_state = {
            **state,
            "current_agent": "cloud_architect",
            "workflow_phase": workflow_phase,
            "phase_iterations": phase_iterations,
            "needs_terraform_lookup": needs_terraform_lookup,
            "needs_pricing_lookup": needs_pricing_lookup,
            "cloud_architect_analysis": response_content,
        }
        
        # Set final_response only when we should communicate with user
        if should_respond_to_user:
            result_state["final_response"] = response_content
            log_agent_complete("Cloud Architect", "Generated user response")
        else:
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


def _should_generate_user_response(state: InfrastructureStateDict, response_content: str) -> bool:
    """Determine if Cloud Architect should generate a user-facing response."""
    errors = state.get("errors", [])
    completed_stages = state.get("completed_stages", [])
    workflow_phase = state.get("workflow_phase", "planning")
    
    # 1. ERROR NOTIFICATION - if there are errors
    if errors:
        return True
    
    # 2. APPROVAL REQUEST - if validation is complete and approval workflow reached
    if workflow_phase == "approval":
        return True
    
    # 3. DEPLOYMENT COMPLETE - if deployment is finished
    if (workflow_phase == "deployment" and 
        state.get("deployment_status") == "completed"):
        return True
    
    # 4. WORKFLOW COMPLETE - if workflow has reached completion
    if workflow_phase == "complete":
        return True
    
    # 5. CLARIFICATION NEEDED - if LLM explicitly requests clarification
    if "CLARIFICATION_REQUIRED" in response_content:
        return True
    
    # All other cases: internal coordination only
    return False


def _prepare_agent_context(state: InfrastructureStateDict) -> str:
    """Prepare context information from other agents for Cloud Architect."""
    context_parts = []
    
    # Cloud Engineer Response
    cloud_engineer_response = state.get("cloud_engineer_response", "")
    if cloud_engineer_response:
        context_parts.append(f"Cloud Engineer Analysis: {cloud_engineer_response}")
    
    # SecOps/FinOps Analysis
    secops_analysis = state.get("secops_finops_analysis", "")
    if secops_analysis:
        context_parts.append(f"Security & Cost Analysis: {secops_analysis}")
    
    # Terraform Guidance
    terraform_guidance = state.get("terraform_guidance", "")
    if terraform_guidance:
        context_parts.append(f"Terraform Best Practices: {terraform_guidance}")
    
    # DevOps Response
    devops_response = state.get("devops_response", "")
    if devops_response:
        context_parts.append(f"Deployment Status: {devops_response}")
    
    # Errors
    errors = state.get("errors", [])
    if errors:
        context_parts.append(f"Errors Encountered: {'; '.join(errors)}")
    
    return "\n\n".join(context_parts) if context_parts else "No specialist agent context available yet."