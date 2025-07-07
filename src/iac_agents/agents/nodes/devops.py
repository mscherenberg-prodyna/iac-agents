"""DevOps Engineer Agent node for LangGraph workflow."""

import json
import os
import subprocess
from pathlib import Path

from ...logging_system import log_agent_complete, log_agent_start, log_info, log_warning
from ..state import InfrastructureStateDict
from ..terraform_utils import (
    run_terraform_command,
)

AGENT_NAME = "devops"


def devops_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """DevOps Agent - Deployment automation and Azure infrastructure deployment."""
    log_agent_start(AGENT_NAME, "Starting Azure infrastructure deployment")

    template_content = state.get("final_template", "")
    conversation_history = state["conversation_history"]

    try:
        # Verify Azure CLI authentication
        if not verify_azure_auth():
            devops_response = (
                "❌ **Deployment Failed**\n\nAzure CLI authentication is required. "
                "Please run `az login` to authenticate with Azure before attempting deployment."
            )
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

        # Create deployment workspace with variable management
        deployment_result = deploy_infrastructure(template_content)

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
        log_warning(AGENT_NAME, f"Deployment failed: {error_message}")
        devops_response = (
            f"❌ **Deployment Failed**\n\nTerraform deployment encountered errors:\n\n```\n{error_message}"
            f"\n```\n\nPlease review the template and correct the issues before retrying deployment."
        )
        conversation_history.append(f"DevOps Engineer: {devops_response}")
        return {
            **state,
            "current_agent": "devops",
            "conversation_history": conversation_history,
            "devops_response": devops_response,
            "deployment_status": "failed",
            "workflow_phase": "complete",
            "errors": state.get("errors", []) + [error_message],
        }

    except Exception as e:
        log_warning(AGENT_NAME, f"Deployment failed with exception: {str(e)}")
        devops_response = (
            f"❌ **Deployment Failed**\n\nAn unexpected error occurred "
            f"during deployment:\n\n```\n{str(e)}\n```"
        )
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


def verify_azure_auth() -> bool:
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


def deploy_infrastructure(template_content: str) -> dict:
    """Deploy infrastructure using Terraform with Azure CLI authentication."""
    try:
        # Create deployment workspace
        deployment_dir = (
            Path.cwd() / "terraform_deployments" / f"deployment_{os.getpid()}"
        )
        deployment_dir.mkdir(parents=True, exist_ok=True)

        log_info(AGENT_NAME, f"Created deployment workspace: {deployment_dir}")

        # Write Terraform configuration
        main_tf_path = deployment_dir / "main.tf"
        with open(main_tf_path, "w", encoding="utf-8") as f:
            f.write(template_content)

        log_info(AGENT_NAME, "Terraform configuration written")

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
            "Terraform init successful!",
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
            timeout=600,
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
