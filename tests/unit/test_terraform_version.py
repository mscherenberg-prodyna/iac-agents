"""Tests for get_terraform_version function."""

from pathlib import Path
from unittest.mock import patch

import pytest

from iac_agents.agents.terraform_utils import get_terraform_version


class TestGetTerraformVersion:
    """Test suite for get_terraform_version function."""

    @patch("iac_agents.agents.terraform_utils.run_terraform_command")
    def test_successful_version_retrieval(self, mock_run_command):
        """Test successful terraform version retrieval."""
        test_data_path = Path(__file__).parent.parent / "test_data"
        with open(test_data_path / "terraform_version_output.txt", "r") as f:
            version_output = f.read()

        mock_run_command.return_value = {
            "success": True,
            "stdout": version_output,
            "stderr": "",
            "returncode": 0,
        }

        version = get_terraform_version()

        assert version == "1.6.4"
        mock_run_command.assert_called_once_with(
            working_dir=Path.cwd(),
            command=["terraform", "version"],
            timeout=30,
            context="check",
        )

    @patch("iac_agents.agents.terraform_utils.run_terraform_command")
    def test_failed_version_command(self, mock_run_command):
        """Test failed terraform version command."""
        mock_run_command.return_value = {
            "success": False,
            "stdout": "",
            "stderr": "terraform: command not found",
            "returncode": 1,
        }

        version = get_terraform_version()

        assert version is None

    @patch("iac_agents.agents.terraform_utils.run_terraform_command")
    def test_version_pattern_not_found(self, mock_run_command):
        """Test when version pattern doesn't match."""
        mock_run_command.return_value = {
            "success": True,
            "stdout": "Invalid version output format",
            "stderr": "",
            "returncode": 0,
        }

        version = get_terraform_version()

        assert version is None

    @patch("iac_agents.agents.terraform_utils.run_terraform_command")
    def test_different_version_format(self, mock_run_command):
        """Test different terraform version format."""
        mock_run_command.return_value = {
            "success": True,
            "stdout": "Terraform v1.5.7\non darwin_amd64",
            "stderr": "",
            "returncode": 0,
        }

        version = get_terraform_version()

        assert version == "1.5.7"
