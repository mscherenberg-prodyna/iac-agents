"""Test utilities and helper functions."""

from datetime import datetime
from typing import Optional

from src.iac_agents.deployment_automation import DeploymentStatus


def extract_hcl_template_from_response(response: str) -> Optional[str]:
    """Extract HCL template from agent response.

    Args:
        response: The agent response containing HCL code blocks

    Returns:
        Extracted template string or None if not found
    """
    if "```hcl" not in response:
        return None

    start = response.find("```hcl") + 6
    end = response.find("```", start)

    if end <= start:
        return None

    return response[start:end].strip()


def validate_terraform_template(template: str) -> None:
    """Validate that a template contains expected Terraform content.

    Args:
        template: The template string to validate

    Raises:
        AssertionError: If validation fails
    """
    assert template, "Template should not be empty"
    assert len(template) > 50, "Template should be substantial"
    assert (
        "terraform" in template.lower()
        or "provider" in template.lower()
        or "resource" in template.lower()
    ), "Template should contain terraform configuration"
    assert (
        "azurerm" in template.lower() or "azure" in template.lower()
    ), "Template should use Azure provider"


def create_deployment_status(
    deployment_id: str = "test-deployment", status: str = "planning"
) -> DeploymentStatus:
    """Create a standard DeploymentStatus for testing.

    Args:
        deployment_id: ID for the deployment
        status: Status of the deployment

    Returns:
        DeploymentStatus instance
    """
    return DeploymentStatus(
        deployment_id=deployment_id,
        status=status,
        resources_created=[],
        resources_modified=[],
        resources_destroyed=[],
        output_values={},
        logs=[],
        started_at=datetime.now(),
    )
