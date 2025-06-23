"""DevOps Engineer Agent node for LangGraph workflow."""

import os
import subprocess
import tempfile
from pathlib import Path

from ...logging_system import log_agent_complete, log_agent_start, log_warning
from ...templates.template_manager import template_manager
from ..state import InfrastructureStateDict
from ..utils import add_error_to_state, make_llm_call


def devops_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """DevOps Agent - Deployment automation and Azure infrastructure deployment."""
    log_agent_start("DevOps", "Starting Azure infrastructure deployment")

    user_input = state["user_input"]
    template_content = state.get("final_template", "")
    approval_received = state.get("approval_received", False)
    secops_finops_analysis = state.get("secops_finops_analysis", "")
    cloud_architect_analysis = state.get("cloud_architect_analysis", "")

    try:
        if not approval_received:
            log_warning("DevOps", "Deployment cancelled - no approval received")
            return {
                **state,
                "current_agent": "devops",
                "deployment_status": "cancelled_no_approval",
                "workflow_phase": "complete",
            }

        if not template_content or not template_content.strip():
            log_warning("DevOps", "No infrastructure template available for deployment")
            return add_error_to_state(state, "DevOps deployment failed: No infrastructure template provided")

        # Verify Azure CLI authentication
        # TODO: Add option to configure different authentication methods later
        if not _verify_azure_auth():
            return add_error_to_state(state, "DevOps deployment failed: Azure CLI authentication required (run 'az login')")

        # Create deployment workspace
        deployment_result = _deploy_infrastructure(template_content, user_input)
        
        if deployment_result["success"]:
            log_agent_complete("DevOps", f"Infrastructure deployed successfully to Azure")
            
            return {
                **state,
                "current_agent": "devops",
                "devops_response": deployment_result["output"],
                "deployment_status": "deployed",
                "deployment_details": deployment_result["details"],
                "terraform_workspace": deployment_result["workspace_path"],
                "workflow_phase": "complete",
            }
        else:
            log_warning("DevOps", f"Deployment failed: {deployment_result['error']}")
            return add_error_to_state(state, f"DevOps deployment failed: {deployment_result['error']}")

    except Exception as e:
        log_warning("DevOps", f"Deployment failed with exception: {str(e)}")
        return add_error_to_state(state, f"DevOps deployment error: {str(e)}")


def _verify_azure_auth() -> bool:
    """Verify Azure CLI authentication using active session."""
    try:
        # Check if Azure CLI is installed and authenticated
        result = subprocess.run(
            ["az", "account", "show"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            log_agent_start("DevOps", "Azure CLI authentication verified")
            return True
        else:
            log_warning("DevOps", f"Azure CLI authentication failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        log_warning("DevOps", "Azure CLI authentication check timed out")
        return False
    except FileNotFoundError:
        log_warning("DevOps", "Azure CLI not found - please install Azure CLI")
        return False
    except Exception as e:
        log_warning("DevOps", f"Azure authentication verification failed: {str(e)}")
        return False


def _deploy_infrastructure(template_content: str, user_request: str) -> dict:
    """Deploy infrastructure using Terraform with Azure CLI authentication."""
    try:
        # Create deployment workspace
        # TODO: Add proper state management with Azure Storage backend later
        deployment_dir = Path.cwd() / "terraform_deployments" / f"deployment_{os.getpid()}"
        deployment_dir.mkdir(parents=True, exist_ok=True)
        
        log_agent_start("DevOps", f"Created deployment workspace: {deployment_dir}")
        
        # Enhance template with standard tags and provider configuration
        enhanced_template = _enhance_terraform_template(template_content)
        
        # Write Terraform configuration
        main_tf_path = deployment_dir / "main.tf"
        with open(main_tf_path, "w", encoding="utf-8") as f:
            f.write(enhanced_template)
        
        log_agent_start("DevOps", "Terraform configuration written")
        
        # Execute Terraform commands
        deployment_result = {
            "success": False,
            "output": "",
            "error": "",
            "details": {},
            "workspace_path": str(deployment_dir)
        }
        
        # Terraform init
        log_agent_start("DevOps", "Running terraform init...")
        init_result = _run_terraform_command(deployment_dir, ["terraform", "init"])
        if not init_result["success"]:
            deployment_result["error"] = f"Terraform init failed: {init_result['stderr']}"
            return deployment_result
        
        # Terraform plan
        log_agent_start("DevOps", "Running terraform plan...")
        plan_result = _run_terraform_command(deployment_dir, ["terraform", "plan", "-out=tfplan"])
        if not plan_result["success"]:
            deployment_result["error"] = f"Terraform plan failed: {plan_result['stderr']}"
            return deployment_result
        
        # Terraform apply
        log_agent_start("DevOps", "Running terraform apply...")
        apply_result = _run_terraform_command(deployment_dir, ["terraform", "apply", "-auto-approve", "tfplan"])
        if not apply_result["success"]:
            deployment_result["error"] = f"Terraform apply failed: {apply_result['stderr']}"
            return deployment_result
        
        # Get output values
        output_result = _run_terraform_command(deployment_dir, ["terraform", "output", "-json"])
        terraform_outputs = {}
        if output_result["success"]:
            import json
            try:
                terraform_outputs = json.loads(output_result["stdout"])
            except json.JSONDecodeError:
                terraform_outputs = {}
        
        deployment_result.update({
            "success": True,
            "output": f"Infrastructure deployed successfully!\n\nTerraform Apply Output:\n{apply_result['stdout']}",
            "details": {
                "workspace_path": str(deployment_dir),
                "terraform_outputs": terraform_outputs,
                "deployment_summary": "Azure infrastructure deployed via Terraform"
            }
        })
        
        return deployment_result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Deployment process failed: {str(e)}",
            "output": "",
            "details": {},
            "workspace_path": ""
        }


def _enhance_terraform_template(template_content: str) -> str:
    """Enhance Terraform template with provider configuration and standard tags."""
    
    # Check if template already has proper provider configuration
    if "terraform {" not in template_content:
        provider_config = '''
terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  # TODO: Add Azure Storage backend for state management
}

provider "azurerm" {
  features {}
  # Uses active Azure CLI session authentication
  # TODO: Add option to configure different authentication methods
}

'''
        template_content = provider_config + template_content
    
    # Add common variables if not present
    if "variable \"environment\"" not in template_content:
        common_vars = '''
variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "iap-agent"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

'''
        template_content = template_content + "\n" + common_vars
    
    return template_content


def _run_terraform_command(working_dir: Path, command: list) -> dict:
    """Run a Terraform command in the specified directory."""
    try:
        result = subprocess.run(
            command,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out after 5 minutes",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command execution failed: {str(e)}",
            "returncode": -1
        }
