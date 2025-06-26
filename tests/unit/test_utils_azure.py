"""Unit tests for Azure utilities in agents.utils module."""

import json
from subprocess import TimeoutExpired
from unittest.mock import Mock, patch

import pytest

from src.iac_agents.agents.utils import get_azure_subscription_info


class TestGetAzureSubscriptionInfo:
    """Test get_azure_subscription_info function."""

    @patch("src.iac_agents.agents.utils.subprocess.run")
    def test_get_subscription_info_success(self, mock_run):
        """Test successful Azure subscription info retrieval."""
        mock_subscriptions = [
            {"id": "sub1", "name": "Test Subscription", "isDefault": True},
            {"id": "sub2", "name": "Other Subscription", "isDefault": False},
        ]

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(mock_subscriptions)
        mock_run.return_value = mock_result

        result = get_azure_subscription_info()

        assert result["default_subscription_name"] == "Test Subscription"
        assert result["default_subscription_id"] == "sub1"
        assert result["total_subscriptions"] == 2
        assert "Test Subscription" in result["available_subscriptions"]
        assert "Other Subscription" in result["available_subscriptions"]

    @patch("src.iac_agents.agents.utils.subprocess.run")
    def test_get_subscription_info_no_default(self, mock_run):
        """Test Azure subscription info with no default subscription."""
        mock_subscriptions = [
            {"id": "sub1", "name": "Test Subscription", "isDefault": False}
        ]

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(mock_subscriptions)
        mock_run.return_value = mock_result

        result = get_azure_subscription_info()

        assert result["default_subscription_name"] == "None (not logged in)"
        assert result["default_subscription_id"] == "Unknown"
        assert result["total_subscriptions"] == 0

    @patch("src.iac_agents.agents.utils.subprocess.run")
    def test_get_subscription_info_empty_list(self, mock_run):
        """Test Azure subscription info with empty subscription list."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([])
        mock_run.return_value = mock_result

        result = get_azure_subscription_info()

        assert result["default_subscription_name"] == "None (not logged in)"
        assert result["total_subscriptions"] == 0
        assert result["available_subscriptions"] == []

    @patch("src.iac_agents.agents.utils.subprocess.run")
    def test_get_subscription_info_command_failure(self, mock_run):
        """Test Azure subscription info with command failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "Error output"
        mock_run.return_value = mock_result

        result = get_azure_subscription_info()

        assert result["default_subscription_name"] == "Azure CLI error"
        assert result["total_subscriptions"] == 0

    @patch("src.iac_agents.agents.utils.subprocess.run")
    def test_get_subscription_info_timeout(self, mock_run):
        """Test Azure subscription info with timeout."""
        mock_run.side_effect = TimeoutExpired("az", 10)

        result = get_azure_subscription_info()

        assert result["default_subscription_name"] == "Azure CLI not available"
        assert result["total_subscriptions"] == 0

    @patch("src.iac_agents.agents.utils.subprocess.run")
    def test_get_subscription_info_file_not_found(self, mock_run):
        """Test Azure subscription info with Azure CLI not installed."""
        mock_run.side_effect = FileNotFoundError("az command not found")

        result = get_azure_subscription_info()

        assert result["default_subscription_name"] == "Azure CLI not available"
        assert result["total_subscriptions"] == 0

    @patch("src.iac_agents.agents.utils.subprocess.run")
    def test_get_subscription_info_invalid_json(self, mock_run):
        """Test Azure subscription info with invalid JSON response."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Invalid JSON"
        mock_run.return_value = mock_result

        result = get_azure_subscription_info()

        assert result["default_subscription_name"] == "Azure CLI not available"
        assert result["total_subscriptions"] == 0

    @patch("src.iac_agents.agents.utils.subprocess.run")
    def test_get_subscription_info_correct_command(self, mock_run):
        """Test that correct Azure CLI command is called."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([])
        mock_run.return_value = mock_result

        get_azure_subscription_info()

        mock_run.assert_called_once_with(
            ["az", "account", "list", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
