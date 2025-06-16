"""Azure deployment automation with Terraform integration."""

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class DeploymentStatus:
    """Status of a deployment operation."""

    deployment_id: str
    status: str  # planning, applying, completed, failed
    resources_created: List[str]
    resources_modified: List[str]
    resources_destroyed: List[str]
    output_values: Dict[str, str]
    logs: List[str]
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class TerraformDeploymentManager:
    """Manages Terraform deployments for Azure infrastructure."""

    def __init__(self, working_directory: str = None):
        self.working_dir = working_directory or tempfile.mkdtemp(prefix="terraform_")
        self.deployments: Dict[str, DeploymentStatus] = {}

    def create_deployment_workspace(
        self, deployment_id: str, template: str, variables: Dict[str, str] = None
    ) -> str:
        """Create a workspace for Terraform deployment."""
        workspace_dir = os.path.join(self.working_dir, deployment_id)
        os.makedirs(workspace_dir, exist_ok=True)

        # Write main Terraform template
        template_path = os.path.join(workspace_dir, "main.tf")
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template)

        # Write variables if provided
        if variables:
            vars_path = os.path.join(workspace_dir, "terraform.tfvars")
            with open(vars_path, "w", encoding="utf-8") as f:
                for key, value in variables.items():
                    f.write(f'{key} = "{value}"\n')

        # Write backend configuration
        backend_config = self._generate_backend_config(deployment_id)
        backend_path = os.path.join(workspace_dir, "backend.tf")
        with open(backend_path, "w", encoding="utf-8") as f:
            f.write(backend_config)

        return workspace_dir

    def _generate_backend_config(self, deployment_id: str) -> str:
        """Generate Terraform backend configuration for Azure Storage."""
        return f"""
terraform {{
  backend "azurerm" {{
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstate{deployment_id[:8]}"
    container_name       = "tfstate"
    key                  = "{deployment_id}.tfstate"
  }}
}}
"""

    def plan_deployment(
        self, deployment_id: str, template: str, variables: Dict[str, str] = None
    ) -> DeploymentStatus:
        """Plan a Terraform deployment."""
        workspace_dir = self.create_deployment_workspace(
            deployment_id, template, variables
        )

        deployment_status = DeploymentStatus(
            deployment_id=deployment_id,
            status="planning",
            resources_created=[],
            resources_modified=[],
            resources_destroyed=[],
            output_values={},
            logs=[],
            started_at=datetime.now(),
        )

        self.deployments[deployment_id] = deployment_status

        try:
            # Initialize Terraform
            self._run_terraform_command(workspace_dir, ["init"], deployment_status)

            # Run terraform plan
            plan_output = self._run_terraform_command(
                workspace_dir,
                ["plan", "-out=tfplan", "-detailed-exitcode"],
                deployment_status,
            )

            # Parse plan output
            self._parse_plan_output(plan_output, deployment_status)

            deployment_status.status = "planned"

        except subprocess.CalledProcessError as e:
            deployment_status.status = "plan_failed"
            deployment_status.error_message = str(e)
            deployment_status.logs.append(f"Plan failed: {e}")

        return deployment_status

    def apply_deployment(
        self, deployment_id: str, auto_approve: bool = False
    ) -> DeploymentStatus:
        """Apply a planned Terraform deployment."""
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment {deployment_id} not found")

        deployment_status = self.deployments[deployment_id]
        workspace_dir = os.path.join(self.working_dir, deployment_id)

        if deployment_status.status != "planned":
            raise ValueError(f"Deployment {deployment_id} is not in planned state")

        deployment_status.status = "applying"

        try:
            # Apply the planned changes
            apply_args = ["apply", "tfplan"]
            if auto_approve:
                apply_args.append("-auto-approve")

            _ = self._run_terraform_command(
                workspace_dir, apply_args, deployment_status
            )

            # Get outputs
            output_result = self._run_terraform_command(
                workspace_dir, ["output", "-json"], deployment_status
            )

            if output_result:
                deployment_status.output_values = json.loads(output_result)

            deployment_status.status = "completed"
            deployment_status.completed_at = datetime.now()

        except subprocess.CalledProcessError as e:
            deployment_status.status = "failed"
            deployment_status.error_message = str(e)
            deployment_status.logs.append(f"Apply failed: {e}")

        return deployment_status

    def destroy_deployment(
        self, deployment_id: str, auto_approve: bool = False
    ) -> DeploymentStatus:
        """Destroy a Terraform deployment."""
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment {deployment_id} not found")

        deployment_status = self.deployments[deployment_id]
        workspace_dir = os.path.join(self.working_dir, deployment_id)

        deployment_status.status = "destroying"

        try:
            destroy_args = ["destroy"]
            if auto_approve:
                destroy_args.append("-auto-approve")

            self._run_terraform_command(workspace_dir, destroy_args, deployment_status)

            deployment_status.status = "destroyed"
            deployment_status.completed_at = datetime.now()

        except subprocess.CalledProcessError as e:
            deployment_status.status = "destroy_failed"
            deployment_status.error_message = str(e)
            deployment_status.logs.append(f"Destroy failed: {e}")

        return deployment_status

    def _run_terraform_command(
        self, workspace_dir: str, args: List[str], deployment_status: DeploymentStatus
    ) -> str:
        """Run a Terraform command and capture output."""
        cmd = ["terraform"] + args
        deployment_status.logs.append(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=workspace_dir,
                capture_output=True,
                text=True,
                check=True,
                timeout=600,  # 10 minute timeout
            )

            deployment_status.logs.append(f"Success: {result.stdout}")
            if result.stderr:
                deployment_status.logs.append(f"Stderr: {result.stderr}")

            return result.stdout

        except subprocess.CalledProcessError as e:
            deployment_status.logs.append(f"Error: {e.stderr}")
            raise

    def _parse_plan_output(self, plan_output: str, deployment_status: DeploymentStatus):
        """Parse Terraform plan output to extract resource changes."""
        lines = plan_output.split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("# ") and " will be created" in line:
                resource = line.split(" ")[1]
                deployment_status.resources_created.append(resource)
            elif line.startswith("# ") and " will be updated" in line:
                resource = line.split(" ")[1]
                deployment_status.resources_modified.append(resource)
            elif line.startswith("# ") and " will be destroyed" in line:
                resource = line.split(" ")[1]
                deployment_status.resources_destroyed.append(resource)

    def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentStatus]:
        """Get the status of a deployment."""
        return self.deployments.get(deployment_id)

    def list_deployments(self) -> List[DeploymentStatus]:
        """List all deployments."""
        return list(self.deployments.values())

    def cleanup_workspace(self, deployment_id: str):
        """Clean up the workspace for a deployment."""
        workspace_dir = os.path.join(self.working_dir, deployment_id)
        if os.path.exists(workspace_dir):
            shutil.rmtree(workspace_dir)

    def generate_deployment_summary(self, deployment_id: str) -> str:
        """Generate a human-readable deployment summary."""
        status = self.get_deployment_status(deployment_id)
        if not status:
            return f"Deployment {deployment_id} not found"

        summary = f"""
# Deployment Summary: {deployment_id}

**Status**: {status.status.upper()}
**Started**: {status.started_at.strftime('%Y-%m-%d %H:%M:%S')}
"""

        if status.completed_at:
            duration = status.completed_at - status.started_at
            summary += (
                f"**Completed**: {status.completed_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            summary += f"**Duration**: {duration.total_seconds():.1f} seconds\n"

        if status.resources_created:
            summary += f"\n## Resources Created ({len(status.resources_created)})\n"
            for resource in status.resources_created:
                summary += f"- ✅ {resource}\n"

        if status.resources_modified:
            summary += f"\n## Resources Modified ({len(status.resources_modified)})\n"
            for resource in status.resources_modified:
                summary += f"- 🔄 {resource}\n"

        if status.resources_destroyed:
            summary += f"\n## Resources Destroyed ({len(status.resources_destroyed)})\n"
            for resource in status.resources_destroyed:
                summary += f"- ❌ {resource}\n"

        if status.output_values:
            summary += "\n## Outputs\n"
            for key, value in status.output_values.items():
                summary += f"- **{key}**: {value}\n"

        if status.error_message:
            summary += f"\n## Error\n```\n{status.error_message}\n```\n"

        return summary
