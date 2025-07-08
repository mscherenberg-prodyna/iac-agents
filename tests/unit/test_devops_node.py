"""Tests for devops agent node."""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from iac_agents.agents.nodes.devops import (
    deploy_infrastructure,
    devops_agent,
    verify_azure_auth,
)


class TestDevopsAgent:
    """Test suite for devops agent node."""

    @patch("iac_agents.agents.nodes.devops.deploy_infrastructure")
    @patch("iac_agents.agents.nodes.devops.verify_azure_auth")
    def test_devops_agent_successful_deployment(
        self, mock_verify_auth, mock_deploy_infrastructure
    ):
        """Test successful deployment flow."""
        mock_verify_auth.return_value = True
        mock_deploy_infrastructure.return_value = {
            "success": True,
            "output": "Infrastructure deployed successfully!",
            "details": {"workspace_path": "/tmp/deployment"},
            "workspace_path": "/tmp/deployment",
        }

        state = {
            "conversation_history": ["User: Deploy infrastructure"],
            "final_template": 'resource "aws_instance" "test" {}',
            "errors": [],
        }

        result = devops_agent(state)

        assert result["deployment_status"] == "deployed"
        assert result["workflow_phase"] == "complete"
        assert "Infrastructure deployed successfully!" in result["devops_response"]
        assert result["terraform_workspace"] == "/tmp/deployment"

    @patch("iac_agents.agents.nodes.devops.verify_azure_auth")
    def test_devops_agent_auth_failure(self, mock_verify_auth):
        """Test deployment failure due to auth issues."""
        mock_verify_auth.return_value = False

        state = {
            "conversation_history": ["User: Deploy infrastructure"],
            "final_template": 'resource "aws_instance" "test" {}',
            "errors": [],
        }

        result = devops_agent(state)

        assert result["deployment_status"] == "failed"
        assert result["workflow_phase"] == "complete"
        assert "Azure CLI authentication is required" in result["devops_response"]
        assert "Azure CLI authentication required" in result["errors"]

    @patch("iac_agents.agents.nodes.devops.deploy_infrastructure")
    @patch("iac_agents.agents.nodes.devops.verify_azure_auth")
    def test_devops_agent_deployment_failure(
        self, mock_verify_auth, mock_deploy_infrastructure
    ):
        """Test deployment failure."""
        mock_verify_auth.return_value = True
        mock_deploy_infrastructure.return_value = {
            "success": False,
            "error": "Terraform plan failed: Resource not found",
            "output": "",
            "details": {},
            "workspace_path": "",
        }

        state = {
            "conversation_history": ["User: Deploy infrastructure"],
            "final_template": 'resource "aws_instance" "test" {}',
            "errors": [],
        }

        result = devops_agent(state)

        assert result["deployment_status"] == "failed"
        assert result["workflow_phase"] == "complete"
        assert "Deployment Failed" in result["devops_response"]
        assert "Terraform plan failed: Resource not found" in result["errors"]

    @patch("iac_agents.agents.nodes.devops.verify_azure_auth")
    def test_devops_agent_exception_handling(self, mock_verify_auth):
        """Test devops agent exception handling."""
        mock_verify_auth.side_effect = Exception("Unexpected error")

        state = {
            "conversation_history": ["User: Deploy infrastructure"],
            "final_template": 'resource "aws_instance" "test" {}',
            "errors": [],
        }

        result = devops_agent(state)

        assert result["deployment_status"] == "failed"
        assert result["workflow_phase"] == "complete"
        assert "Deployment Failed" in result["devops_response"]
        assert "Unexpected error" in result["errors"]


class TestVerifyAzureAuth:
    """Test suite for verify_azure_auth function."""

    @patch("iac_agents.agents.nodes.devops.subprocess.run")
    def test_verify_azure_auth_success(self, mock_run):
        """Test successful Azure auth verification."""
        mock_run.return_value = Mock(returncode=0, stderr="")

        result = verify_azure_auth()

        assert result is True
        mock_run.assert_called_once_with(
            ["az", "account", "show"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    @patch("iac_agents.agents.nodes.devops.subprocess.run")
    def test_verify_azure_auth_failure(self, mock_run):
        """Test Azure auth verification failure."""
        mock_run.return_value = Mock(returncode=1, stderr="Not logged in")

        result = verify_azure_auth()

        assert result is False

    @patch("iac_agents.agents.nodes.devops.subprocess.run")
    def test_verify_azure_auth_timeout(self, mock_run):
        """Test Azure auth verification timeout."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired(cmd=["az", "account", "show"], timeout=30)

        result = verify_azure_auth()

        assert result is False

    @patch("iac_agents.agents.nodes.devops.subprocess.run")
    def test_verify_azure_auth_file_not_found(self, mock_run):
        """Test Azure auth verification when Azure CLI not found."""
        mock_run.side_effect = FileNotFoundError("Azure CLI not found")

        result = verify_azure_auth()

        assert result is False

    @patch("iac_agents.agents.nodes.devops.subprocess.run")
    def test_verify_azure_auth_generic_exception(self, mock_run):
        """Test Azure auth verification with generic exception."""
        mock_run.side_effect = Exception("Generic error")

        result = verify_azure_auth()

        assert result is False


class TestDeployInfrastructure:
    """Test suite for deploy_infrastructure function."""

    @patch("iac_agents.agents.nodes.devops.run_terraform_command")
    @patch("iac_agents.agents.nodes.devops.os.getpid")
    @patch("builtins.open")
    def test_deploy_infrastructure_success(
        self, mock_open, mock_getpid, mock_run_terraform
    ):
        """Test successful infrastructure deployment."""
        mock_getpid.return_value = 12345

        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__ = Mock(return_value=mock_file)
        mock_open.return_value.__exit__ = Mock(return_value=None)

        with patch("iac_agents.agents.nodes.devops.Path") as mock_path_class:
            # Mock path operations
            mock_deployment_dir = Mock()
            mock_deployment_dir.mkdir = Mock()
            mock_deployment_dir.__truediv__ = Mock(return_value=Mock())
            mock_deployment_dir.__str__ = Mock(return_value="/tmp/deployment")

            mock_path_class.cwd.return_value = Mock()
            mock_path_class.cwd.return_value.__truediv__ = Mock(return_value=Mock())
            mock_path_class.cwd.return_value.__truediv__.return_value.__truediv__ = (
                Mock(return_value=mock_deployment_dir)
            )

            # Mock terraform commands
            mock_run_terraform.side_effect = [
                {"success": True, "stdout": "init success", "stderr": ""},
                {"success": True, "stdout": "plan success", "stderr": ""},
                {"success": True, "stdout": "apply success", "stderr": ""},
                {
                    "success": True,
                    "stdout": '{"output1": {"value": "test"}}',
                    "stderr": "",
                },
            ]

            result = deploy_infrastructure('resource "aws_instance" "test" {}')

            assert result["success"] is True
            assert "Infrastructure deployed successfully!" in result["output"]
            assert (
                result["details"]["deployment_summary"]
                == "Azure infrastructure deployed via Terraform"
            )

    @patch("iac_agents.agents.nodes.devops.run_terraform_command")
    @patch("iac_agents.agents.nodes.devops.os.getpid")
    @patch("builtins.open")
    def test_deploy_infrastructure_init_failure(
        self, mock_open, mock_getpid, mock_run_terraform
    ):
        """Test infrastructure deployment with init failure."""
        mock_getpid.return_value = 12345

        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__ = Mock(return_value=mock_file)
        mock_open.return_value.__exit__ = Mock(return_value=None)

        with patch("iac_agents.agents.nodes.devops.Path") as mock_path_class:
            # Mock path operations
            mock_deployment_dir = Mock()
            mock_deployment_dir.mkdir = Mock()
            mock_deployment_dir.__truediv__ = Mock(return_value=Mock())
            mock_deployment_dir.__str__ = Mock(return_value="/tmp/deployment")

            mock_path_class.cwd.return_value = Mock()
            mock_path_class.cwd.return_value.__truediv__ = Mock(return_value=Mock())
            mock_path_class.cwd.return_value.__truediv__.return_value.__truediv__ = (
                Mock(return_value=mock_deployment_dir)
            )

            # Mock terraform init failure
            mock_run_terraform.return_value = {
                "success": False,
                "stderr": "Init failed: provider not found",
            }

            result = deploy_infrastructure('resource "aws_instance" "test" {}')

            assert result["success"] is False
            assert (
                "Terraform init failed: Init failed: provider not found"
                in result["error"]
            )

    @patch("iac_agents.agents.nodes.devops.run_terraform_command")
    @patch("iac_agents.agents.nodes.devops.os.getpid")
    @patch("builtins.open")
    def test_deploy_infrastructure_plan_failure(
        self, mock_open, mock_getpid, mock_run_terraform
    ):
        """Test infrastructure deployment with plan failure."""
        mock_getpid.return_value = 12345

        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__ = Mock(return_value=mock_file)
        mock_open.return_value.__exit__ = Mock(return_value=None)

        with patch("iac_agents.agents.nodes.devops.Path") as mock_path_class:
            # Mock path operations
            mock_deployment_dir = Mock()
            mock_deployment_dir.mkdir = Mock()
            mock_deployment_dir.__truediv__ = Mock(return_value=Mock())
            mock_deployment_dir.__str__ = Mock(return_value="/tmp/deployment")

            mock_path_class.cwd.return_value = Mock()
            mock_path_class.cwd.return_value.__truediv__ = Mock(return_value=Mock())
            mock_path_class.cwd.return_value.__truediv__.return_value.__truediv__ = (
                Mock(return_value=mock_deployment_dir)
            )

            # Mock terraform commands - init success, plan failure
            mock_run_terraform.side_effect = [
                {"success": True, "stdout": "init success", "stderr": ""},
                {
                    "success": False,
                    "stdout": "",
                    "stderr": "Plan failed: invalid resource",
                },
            ]

            result = deploy_infrastructure('resource "aws_instance" "test" {}')

            assert result["success"] is False
            assert (
                "Terraform plan failed: Plan failed: invalid resource"
                in result["error"]
            )

    @patch("iac_agents.agents.nodes.devops.Path")
    def test_deploy_infrastructure_exception(self, mock_path):
        """Test infrastructure deployment with exception."""
        mock_path.cwd.side_effect = Exception("Path operation failed")

        result = deploy_infrastructure('resource "aws_instance" "test" {}')

        assert result["success"] is False
        assert "Deployment process failed: Path operation failed" in result["error"]
