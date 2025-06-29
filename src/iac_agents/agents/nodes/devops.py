"""DevOps Engineer Agent node for LangGraph workflow."""

import json
import os
import re
import subprocess
from pathlib import Path

from ...logging_system import log_agent_complete, log_agent_start, log_info, log_warning
from ..state import InfrastructureStateDict
from ..terraform_utils import (
    TerraformVariableManager,
    enhance_terraform_template,
    run_terraform_command,
)

AGENT_NAME = "DevOps Engineer"


def devops_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """DevOps Agent - Deployment automation and Azure infrastructure deployment."""
    log_agent_start(AGENT_NAME, "Starting Azure infrastructure deployment")

    template_content = state.get("final_template", "")
    approval_received = state.get("approval_received", False)
    conversation_history = state["conversation_history"]

    try:
        if not approval_received:
            log_warning(AGENT_NAME, "Deployment cancelled - no approval received")
            devops_response = (
                "❌ **Deployment Cancelled**\n\nNo approval received for deployment."
            )
            conversation_history.append(f"DevOps Engineer: {devops_response}")
            return {
                **state,
                "current_agent": "devops",
                "conversation_history": conversation_history,
                "devops_response": devops_response,
                "deployment_status": "cancelled_no_approval",
                "workflow_phase": "complete",
            }

        if not template_content or not template_content.strip():
            log_warning(
                AGENT_NAME, "No infrastructure template available for deployment"
            )
            devops_response = "❌ **Deployment Failed**\n\nNo infrastructure template was provided for deployment. Please ensure the Cloud Engineer has generated a valid Terraform template."
            conversation_history.append(f"DevOps Engineer: {devops_response}")
            return {
                **state,
                "current_agent": "devops",
                "conversation_history": conversation_history,
                "devops_response": devops_response,
                "deployment_status": "failed",
                "workflow_phase": "complete",
                "errors": state.get("errors", [])
                + ["No infrastructure template provided"],
            }

        # Verify Azure CLI authentication
        if not _verify_azure_auth():
            devops_response = "❌ **Deployment Failed**\n\nAzure CLI authentication is required. Please run `az login` to authenticate with Azure before attempting deployment."
            conversation_history.append(f"DevOps Engineer: {devops_response}")
            return {
                **state,
                "current_agent": "devops",
                "conversation_history": conversation_history,
                "devops_response": devops_response,
                "deployment_status": "failed",
                "workflow_phase": "complete",
                "errors": state.get("errors", [])
                + ["Azure CLI authentication required"],
            }

        # Get user requirements for variable inference
        user_requirements = state.get("user_input", "")

        # Create deployment workspace with variable management
        deployment_result = _deploy_infrastructure(template_content, user_requirements)

        if deployment_result["success"]:
            log_agent_complete(
                AGENT_NAME, "Infrastructure deployed successfully to Azure"
            )
            devops_response = deployment_result["output"]
            conversation_history.append(f"DevOps Engineer: {devops_response}")
            return {
                **state,
                "current_agent": "devops",
                "conversation_history": conversation_history,
                "devops_response": devops_response,
                "deployment_status": "deployed",
                "deployment_details": deployment_result["details"],
                "terraform_workspace": deployment_result["workspace_path"],
                "workflow_phase": "complete",
            }
        error_message = deployment_result["error"]
        # Clean up ANSI color codes for better display
        clean_error = _clean_terraform_error(error_message)
        log_warning(AGENT_NAME, f"Deployment failed: {error_message}")
        devops_response = f"❌ **Deployment Failed**\n\nTerraform deployment encountered errors:\n\n```\n{clean_error}\n```\n\nPlease review the template and correct the issues before retrying deployment."
        conversation_history.append(f"DevOps Engineer: {devops_response}")
        return {
            **state,
            "current_agent": "devops",
            "conversation_history": conversation_history,
            "devops_response": devops_response,
            "deployment_status": "failed",
            "workflow_phase": "complete",
            "errors": state.get("errors", []) + [clean_error],
        }

    except Exception as e:
        log_warning(AGENT_NAME, f"Deployment failed with exception: {str(e)}")
        devops_response = f"❌ **Deployment Failed**\n\nAn unexpected error occurred during deployment:\n\n```\n{str(e)}\n```"
        conversation_history.append(f"DevOps Engineer: {devops_response}")
        return {
            **state,
            "current_agent": "devops",
            "conversation_history": conversation_history,
            "devops_response": devops_response,
            "deployment_status": "failed",
            "workflow_phase": "complete",
            "errors": state.get("errors", []) + [str(e)],
        }


def _clean_terraform_error(error_message: str) -> str:
    """Clean ANSI color codes and format terraform error messages."""

    # Remove ANSI color codes
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    clean_message = ansi_escape.sub("", error_message)

    # Remove extra whitespace and normalize line breaks
    clean_message = re.sub(r"\n\s*\n", "\n\n", clean_message.strip())

    return clean_message


def _verify_azure_auth() -> bool:
    """Verify Azure CLI authentication using active session."""
    try:
        # Check if Azure CLI is installed and authenticated
        result = subprocess.run(
            ["az", "account", "show"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if result.returncode == 0:
            log_agent_start(AGENT_NAME, "Azure CLI authentication verified")
            return True
        log_warning(AGENT_NAME, f"Azure CLI authentication failed: {result.stderr}")
        return False

    except subprocess.TimeoutExpired:
        log_warning(AGENT_NAME, "Azure CLI authentication check timed out")
        return False
    except FileNotFoundError:
        log_warning(AGENT_NAME, "Azure CLI not found - please install Azure CLI")
        return False
    except Exception as e:
        log_warning(AGENT_NAME, f"Azure authentication verification failed: {str(e)}")
        return False


def _deploy_infrastructure(template_content: str, user_requirements: str = "") -> dict:
    """Deploy infrastructure using Terraform with Azure CLI authentication."""
    try:
        # Create deployment workspace
        deployment_dir = (
            Path.cwd() / "terraform_deployments" / f"deployment_{os.getpid()}"
        )
        deployment_dir.mkdir(parents=True, exist_ok=True)

        log_info(AGENT_NAME, f"Created deployment workspace: {deployment_dir}")

        # Validate and enhance template with variable management
        is_valid, issues = TerraformVariableManager.validate_template_variables(
            template_content
        )

        if not is_valid:
            log_info(AGENT_NAME, f"Template validation issues found: {issues}")
            # Infer variable values from user requirements
            inferred_values = (
                TerraformVariableManager.infer_variable_values_from_requirements(
                    user_requirements
                )
            )
            log_info(AGENT_NAME, f"Inferred variable values: {inferred_values}")

            # Enhance template with inferred defaults
            enhanced_template = TerraformVariableManager.enhance_template_with_defaults(
                template_content, inferred_values
            )
            log_info(AGENT_NAME, "Template enhanced with inferred variable defaults")
        else:
            enhanced_template = template_content
            log_info(AGENT_NAME, "Template validation passed, using original template")

        # Apply standard enhancements (provider config, etc.)
        enhanced_template = enhance_terraform_template(
            enhanced_template,
            project_name="iap-agent",
            default_location="West Europe",
        )

        # Write Terraform configuration
        main_tf_path = deployment_dir / "main.tf"
        with open(main_tf_path, "w", encoding="utf-8") as f:
            f.write(enhanced_template)

        log_info(AGENT_NAME, "Terraform configuration written")

        # Log the template being deployed for debugging
        log_info(AGENT_NAME, f"Template content:\n{enhanced_template}")

        # Execute Terraform commands
        deployment_result = {
            "success": False,
            "output": "",
            "error": "",
            "details": {},
            "workspace_path": str(deployment_dir),
        }

        # Terraform init
        log_info(AGENT_NAME, "Running terraform init...")
        init_result = run_terraform_command(
            deployment_dir, ["terraform", "init"], timeout=300, context="Deployment"
        )
        log_info(
            AGENT_NAME,
            f"Terraform init output:\nSTDOUT:\n{init_result['stdout']}\nSTDERR:\n{init_result['stderr']}",
        )
        if not init_result["success"]:
            deployment_result["error"] = (
                f"Terraform init failed: {init_result['stderr']}"
            )
            return deployment_result

        # Terraform plan
        log_info(AGENT_NAME, "Running terraform plan...")
        plan_result = run_terraform_command(
            deployment_dir,
            ["terraform", "plan", "-out=tfplan", "-no-color"],
            timeout=300,
            context="Deployment",
        )
        log_info(
            AGENT_NAME,
            f"Terraform plan output:\nSTDOUT:\n{plan_result['stdout']}\nSTDERR:\n{plan_result['stderr']}",
        )
        if not plan_result["success"]:
            deployment_result["error"] = (
                f"Terraform plan failed: {plan_result['stderr']}"
            )
            return deployment_result

        # Terraform apply
        log_info(AGENT_NAME, "Running terraform apply...")
        apply_result = run_terraform_command(
            deployment_dir,
            ["terraform", "apply", "-no-color", "-auto-approve", "tfplan"],
            timeout=300,
            context="Deployment",
        )
        log_info(
            AGENT_NAME,
            f"Terraform apply output:\nSTDOUT:\n{apply_result['stdout']}\nSTDERR:\n{apply_result['stderr']}",
        )
        if not apply_result["success"]:
            deployment_result["error"] = (
                f"Terraform apply failed: {apply_result['stderr']}"
            )
            return deployment_result

        # Get output values
        output_result = run_terraform_command(
            deployment_dir,
            ["terraform", "output", "-json"],
            timeout=300,
            context="Deployment",
        )
        terraform_outputs = {}
        if output_result["success"]:
            try:
                terraform_outputs = json.loads(output_result["stdout"])
            except json.JSONDecodeError:
                terraform_outputs = {}

        deployment_result.update(
            {
                "success": True,
                "output": f"Infrastructure deployed successfully!\n\nTerraform Apply Output:\n{apply_result['stdout']}",
                "details": {
                    "workspace_path": str(deployment_dir),
                    "terraform_outputs": terraform_outputs,
                    "deployment_summary": "Azure infrastructure deployed via Terraform",
                },
            }
        )

        return deployment_result

    except Exception as e:
        return {
            "success": False,
            "error": f"Deployment process failed: {str(e)}",
            "output": "",
            "details": {},
            "workspace_path": "",
        }
