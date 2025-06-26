"""Unit tests for terraform command execution."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.iac_agents.agents.terraform_utils import run_terraform_command


class TestRunTerraformCommand:
    """Test terraform command execution."""

    @patch("src.iac_agents.agents.terraform_utils.subprocess.run")
    def test_successful_command(self, mock_run):
        """Should handle successful command execution."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = run_terraform_command(Path("/tmp"), ["terraform", "init"])

        assert result["success"] is True
        assert result["stdout"] == "Success"

    @patch("src.iac_agents.agents.terraform_utils.subprocess.run")
    def test_failed_command(self, mock_run):
        """Should handle failed command execution."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error"
        mock_run.return_value = mock_result

        result = run_terraform_command(Path("/tmp"), ["terraform", "plan"])

        assert result["success"] is False
        assert result["stderr"] == "Error"

    @patch("src.iac_agents.agents.terraform_utils.subprocess.run")
    def test_timeout_handling(self, mock_run):
        """Should handle command timeout."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("terraform", 10)

        result = run_terraform_command(Path("/tmp"), ["terraform", "apply"], timeout=10)

        assert result["success"] is False
        assert "timed out" in result["stderr"]
