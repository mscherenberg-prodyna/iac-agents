"""Tests for Azure AI Foundry agent management."""

from unittest.mock import Mock, patch

import pytest

from iac_agents.agents.utils import get_agent_id_base, get_agent_id_bing


class TestGetAgentIdBase:
    """Test suite for get_agent_id_base function."""

    @patch("iac_agents.agents.utils.DefaultAzureCredential")
    @patch("iac_agents.agents.utils.AgentsClient")
    @patch("iac_agents.agents.utils.config")
    def test_update_existing_agent(
        self, mock_config, mock_agents_client_cls, mock_credential
    ):
        """Test updating existing agent."""
        mock_config.azure_ai.project_endpoint = "https://test.endpoint.com"
        mock_config.agents.default_model = "gpt-4"
        mock_config.agents.default_temperature = 0.7

        mock_credential_instance = Mock()
        mock_credential.return_value = mock_credential_instance

        mock_agents_client = Mock()
        mock_agents_client_cls.return_value = mock_agents_client

        mock_agent = Mock()
        mock_agent.name = "test_agent"
        mock_agent.id = "agent-123"
        mock_agents_client.list_agents.return_value = [mock_agent]

        agent_id = get_agent_id_base("test_agent", "Test prompt")

        assert agent_id == "agent-123"
        mock_agents_client.update_agent.assert_called_once_with(
            agent_id="agent-123", instructions="Test prompt"
        )

    @patch("iac_agents.agents.utils.DefaultAzureCredential")
    @patch("iac_agents.agents.utils.AgentsClient")
    @patch("iac_agents.agents.utils.config")
    def test_create_new_agent(
        self, mock_config, mock_agents_client_cls, mock_credential
    ):
        """Test creating new agent."""
        mock_config.azure_ai.project_endpoint = "https://test.endpoint.com"
        mock_config.agents.default_model = "gpt-4"
        mock_config.agents.default_temperature = 0.7

        mock_credential_instance = Mock()
        mock_credential.return_value = mock_credential_instance

        mock_agents_client = Mock()
        mock_agents_client_cls.return_value = mock_agents_client

        mock_agents_client.list_agents.return_value = []
        mock_agents_client.create_agent.return_value = {"id": "new-agent-456"}

        agent_id = get_agent_id_base("new_agent", "New prompt")

        assert agent_id == "new-agent-456"
        mock_agents_client.create_agent.assert_called_once_with(
            name="new_agent", model="gpt-4", instructions="New prompt", temperature=0.7
        )


class TestGetAgentIdBing:
    """Test suite for get_agent_id_bing function."""

    @patch("iac_agents.agents.utils.DefaultAzureCredential")
    @patch("iac_agents.agents.utils.AgentsClient")
    @patch("iac_agents.agents.utils.BingGroundingTool")
    @patch("iac_agents.agents.utils.config")
    def test_create_bing_agent(
        self, mock_config, mock_bing_tool_cls, mock_agents_client_cls, mock_credential
    ):
        """Test creating new Bing agent."""
        mock_config.azure_ai.project_endpoint = "https://test.endpoint.com"
        mock_config.azure_ai.bing_connection = "bing-connection-123"
        mock_config.agents.default_model = "gpt-4"
        mock_config.agents.default_temperature = 0.7

        mock_credential_instance = Mock()
        mock_credential.return_value = mock_credential_instance

        mock_agents_client = Mock()
        mock_agents_client_cls.return_value = mock_agents_client

        mock_bing_tool = Mock()
        mock_bing_tool.definitions = [{"type": "bing_search"}]
        mock_bing_tool_cls.return_value = mock_bing_tool

        mock_agents_client.list_agents.return_value = []
        mock_agents_client.create_agent.return_value = {"id": "new-bing-agent-456"}

        agent_id = get_agent_id_bing("new_bing_agent", "New Bing prompt")

        assert agent_id == "new-bing-agent-456"
        mock_bing_tool_cls.assert_called_once_with(connection_id="bing-connection-123")
        mock_agents_client.create_agent.assert_called_once_with(
            name="new_bing_agent",
            model="gpt-4",
            instructions="New Bing prompt",
            tools=[{"type": "bing_search"}],
            temperature=0.7,
        )
