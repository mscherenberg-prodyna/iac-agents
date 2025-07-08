"""Tests for run_terraform_command function."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from iac_agents.agents.terraform_utils import run_terraform_command


class TestRunTerraformCommand:
    """Test suite for run_terraform_command function."""

    @patch("subprocess.run")
    def test_successful_command_execution(self, mock_run):
        """Test successful terraform command execution."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Success output",
            stderr="",
        )

        result = run_terraform_command(
            working_dir=Path("/tmp"),
            command=["terraform", "init"],
            timeout=30,
            context="test",
        )

        assert result["success"] is True
        assert result["stdout"] == "Success output"
        assert result["stderr"] == ""
        assert result["returncode"] == 0

    @patch("subprocess.run")
    def test_failed_command_execution(self, mock_run):
        """Test failed terraform command execution."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error occurred",
        )

        result = run_terraform_command(
            working_dir=Path("/tmp"),
            command=["terraform", "plan"],
            timeout=30,
            context="test",
        )

        assert result["success"] is False
        assert result["returncode"] == 1
        assert result["stderr"] == "Error occurred"

    @patch("subprocess.run")
    def test_command_timeout_handling(self, mock_run):
        """Test terraform command timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["terraform", "init"], timeout=30
        )

        result = run_terraform_command(
            working_dir=Path("/tmp"),
            command=["terraform", "init"],
            timeout=30,
            context="test",
        )

        assert result["success"] is False
        assert result["returncode"] == -1
        assert "test command timed out after 30 seconds" in result["stderr"]

    @patch("subprocess.run")
    def test_command_exception_handling(self, mock_run):
        """Test terraform command exception handling."""
        mock_run.side_effect = Exception("System error")

        result = run_terraform_command(
            working_dir=Path("/tmp"),
            command=["terraform", "init"],
            timeout=30,
            context="test",
        )

        assert result["success"] is False
        assert result["returncode"] == -1
        assert "test command failed: System error" in result["stderr"]

    @patch("subprocess.run")
    def test_command_with_custom_timeout(self, mock_run):
        """Test terraform command with custom timeout."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Custom timeout test",
            stderr="",
        )

        run_terraform_command(
            working_dir=Path("/tmp"),
            command=["terraform", "init"],
            timeout=60,
            context="custom",
        )

        mock_run.assert_called_once_with(
            ["terraform", "init"],
            cwd=Path("/tmp"),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
