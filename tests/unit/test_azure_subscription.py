"""Tests for Azure subscription information retrieval."""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from iac_agents.agents.utils import get_azure_subscription_info


class TestGetAzureSubscriptionInfo:
    """Test suite for get_azure_subscription_info function."""

    @patch("subprocess.run")
    def test_successful_subscription_retrieval(self, mock_run):
        """Test successful Azure subscription info retrieval."""
        test_data_path = Path(__file__).parent.parent / "test_data"
        with open(test_data_path / "azure_subscription_response.json", "r") as f:
            subscription_data = f.read()

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = subscription_data
        mock_run.return_value = mock_result

        subscription_info = get_azure_subscription_info()

        expected = {
            "default_subscription_name": "Test Subscription",
            "default_subscription_id": "sub-123456",
            "total_subscriptions": 2,
            "available_subscriptions": ["Test Subscription", "Another Subscription"],
        }

        assert subscription_info == expected

    @patch("subprocess.run")
    def test_no_default_subscription(self, mock_run):
        """Test Azure subscription info when no default subscription."""
        subscriptions = [
            {"name": "Subscription 1", "id": "sub-123", "isDefault": False},
            {"name": "Subscription 2", "id": "sub-456", "isDefault": False},
        ]

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(subscriptions)
        mock_run.return_value = mock_result

        subscription_info = get_azure_subscription_info()

        expected = {
            "default_subscription_name": "None (not logged in)",
            "default_subscription_id": "Unknown",
            "total_subscriptions": 0,
            "available_subscriptions": [],
        }

        assert subscription_info == expected

    @patch("subprocess.run")
    def test_command_execution_failure(self, mock_run):
        """Test Azure subscription info when command fails."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        subscription_info = get_azure_subscription_info()

        expected = {
            "default_subscription_name": "Azure CLI error",
            "default_subscription_id": "Unknown",
            "total_subscriptions": 0,
            "available_subscriptions": [],
        }

        assert subscription_info == expected

    @patch("subprocess.run")
    def test_command_timeout(self, mock_run):
        """Test Azure subscription info with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["az", "account", "list"], timeout=10
        )

        subscription_info = get_azure_subscription_info()

        expected = {
            "default_subscription_name": "Azure CLI not available",
            "default_subscription_id": "Unknown",
            "total_subscriptions": 0,
            "available_subscriptions": [],
        }

        assert subscription_info == expected

    @patch("subprocess.run")
    def test_azure_cli_not_found(self, mock_run):
        """Test Azure subscription info when az command not found."""
        mock_run.side_effect = FileNotFoundError("az command not found")

        subscription_info = get_azure_subscription_info()

        expected = {
            "default_subscription_name": "Azure CLI not available",
            "default_subscription_id": "Unknown",
            "total_subscriptions": 0,
            "available_subscriptions": [],
        }

        assert subscription_info == expected
