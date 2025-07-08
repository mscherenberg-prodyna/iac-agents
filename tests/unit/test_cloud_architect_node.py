"""Tests for cloud_architect agent node."""

from unittest.mock import Mock, patch

import pytest

from iac_agents.agents.nodes.cloud_architect import (
    determine_architect_target,
    determine_user_response,
    determine_workflow_phase,
    validate_terraform_template,
)


class TestCloudArchitectNode:
    """Test suite for cloud architect agent node functions."""

    def test_determine_workflow_phase_planning(self):
        """Test workflow phase determination for planning."""
        state = {"final_template": ""}

        phase = determine_workflow_phase(state)
        assert phase == "planning"

    def test_determine_workflow_phase_deployment(self):
        """Test workflow phase determination for deployment."""
        state = {
            "final_template": "resource 'aws_instance' 'test' {}",
            "approval_received": True,
        }

        phase = determine_workflow_phase(state)
        assert phase == "deployment"

    def test_determine_workflow_phase_validation(self):
        """Test workflow phase determination for validation."""
        state = {
            "final_template": "resource 'aws_instance' 'test' {}",
            "approval_received": False,
        }

        phase = determine_workflow_phase(state)
        assert phase == "validation"

    def test_determine_workflow_phase_no_template(self):
        """Test workflow phase determination for no template."""
        state = {}

        phase = determine_workflow_phase(state)
        assert phase == "planning"

    @patch("iac_agents.agents.nodes.cloud_architect.run_terraform_command")
    def test_validate_terraform_template_success(self, mock_run_command):
        """Test successful terraform template validation."""
        mock_run_command.side_effect = [
            {
                "success": True,
                "stdout": "Terraform initialized",
                "stderr": "",
                "returncode": 0,
            },
            {
                "success": True,
                "stdout": "Plan: 2 to add, 0 to change, 0 to destroy.",
                "stderr": "",
                "returncode": 0,
            },
        ]

        template = 'resource "aws_instance" "test" { ami = "ami-123" }'
        result = validate_terraform_template(template)

        assert result["valid"] is True
        assert "Plan:" in result["output"]

    @patch("iac_agents.agents.nodes.cloud_architect.run_terraform_command")
    def test_validate_terraform_template_failure(self, mock_run_command):
        """Test failed terraform template validation."""
        mock_run_command.return_value = {
            "success": False,
            "stdout": "",
            "stderr": "Error: Invalid configuration",
            "returncode": 1,
        }

        template = "invalid terraform"
        result = validate_terraform_template(template)

        assert result["valid"] is False
        assert "Error:" in result["error"]

    def test_determine_architect_target_engineer(self):
        """Test architect target determination for engineer."""
        response = (
            "Please coordinate with INTERNAL_CLOUD_ENGINEER for template generation."
        )

        target = determine_architect_target(response)
        assert target == "cloud_engineer"

    def test_determine_architect_target_secops(self):
        """Test architect target determination for secops."""
        response = "Please coordinate with INTERNAL_SECOPS_FINOPS for security review."

        target = determine_architect_target(response)
        assert target == "secops_finops"

    def test_determine_architect_target_devops(self):
        """Test architect target determination for devops."""
        response = "Please coordinate with INTERNAL_DEVOPS for deployment."

        target = determine_architect_target(response)
        assert target == "devops"

    def test_determine_user_response_approval_needed(self):
        """Test user response determination when approval needed."""
        response = "APPROVAL_REQUEST: Please approve the deployment."

        target = determine_user_response(response)
        assert target == "human_approval"

    def test_determine_user_response_completed(self):
        """Test user response determination when completed."""
        response = (
            "DEPLOYMENT_COMPLETE: The infrastructure has been deployed successfully."
        )

        target = determine_user_response(response)
        assert target == "user"

    def test_determine_architect_target_no_match(self):
        """Test architect target determination with no matching keywords."""
        response = "This is just a regular response without special tokens."

        target = determine_architect_target(response)
        assert target is None

    def test_determine_user_response_clarification(self):
        """Test user response determination for clarification."""
        response = (
            "CLARIFICATION_REQUIRED: Please provide more details about the deployment."
        )

        target = determine_user_response(response)
        assert target == "user"
