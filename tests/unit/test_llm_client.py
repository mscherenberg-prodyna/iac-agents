"""Tests for LLM client creation and usage."""

from unittest.mock import Mock, patch

import pytest

from iac_agents.agents.utils import create_llm_client, make_llm_call


class TestCreateLLMClient:
    """Test suite for create_llm_client function."""

    @patch("iac_agents.agents.utils.config")
    @patch("iac_agents.agents.utils.AzureChatOpenAI")
    def test_client_creation_with_config(self, mock_azure_openai, mock_config):
        """Test successful LLM client creation with configuration."""
        mock_config.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_config.azure_openai.deployment = {"test_agent": "gpt-4-deployment"}
        mock_config.azure_openai.api_version = "2023-12-01-preview"
        mock_config.azure_openai.api_key = "test-key"

        mock_client = Mock()
        mock_azure_openai.return_value = mock_client

        client = create_llm_client("test_agent", 0.7)

        assert client == mock_client
        mock_azure_openai.assert_called_once_with(
            azure_endpoint="https://test.openai.azure.com",
            azure_deployment="gpt-4-deployment",
            api_version="2023-12-01-preview",
            api_key="test-key",
            temperature=0.7,
        )

    @patch("iac_agents.agents.utils.config")
    @patch("iac_agents.agents.utils.AzureChatOpenAI")
    def test_client_creation_different_agent(self, mock_azure_openai, mock_config):
        """Test LLM client creation with different agent name."""
        mock_config.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_config.azure_openai.deployment = {"architect": "gpt-4-architect"}
        mock_config.azure_openai.api_version = "2023-12-01-preview"
        mock_config.azure_openai.api_key = "test-key"

        mock_client = Mock()
        mock_azure_openai.return_value = mock_client

        client = create_llm_client("architect", 0.2)

        assert client == mock_client
        mock_azure_openai.assert_called_once_with(
            azure_endpoint="https://test.openai.azure.com",
            azure_deployment="gpt-4-architect",
            api_version="2023-12-01-preview",
            api_key="test-key",
            temperature=0.2,
        )


class TestMakeLLMCall:
    """Test suite for make_llm_call function."""

    @patch("iac_agents.agents.utils.create_llm_client")
    @patch("iac_agents.agents.utils.config")
    def test_llm_call_with_custom_temperature(self, mock_config, mock_create_client):
        """Test LLM call with custom temperature."""
        mock_config.agents.default_temperature = 0.5

        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response
        mock_create_client.return_value = mock_llm

        response = make_llm_call(
            system_prompt="You are a helpful assistant",
            user_message="Hello world",
            agent_name="test_agent",
            temperature=0.7,
        )

        assert response == "Test response"
        mock_create_client.assert_called_once_with("test_agent", 0.7)
        mock_llm.invoke.assert_called_once_with(
            [("system", "You are a helpful assistant"), ("human", "Hello world")]
        )

    @patch("iac_agents.agents.utils.create_llm_client")
    @patch("iac_agents.agents.utils.config")
    def test_llm_call_with_default_parameters(self, mock_config, mock_create_client):
        """Test LLM call with default parameters."""
        mock_config.agents.default_temperature = 0.5

        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Default response"
        mock_llm.invoke.return_value = mock_response
        mock_create_client.return_value = mock_llm

        response = make_llm_call(
            system_prompt="System prompt", user_message="User message"
        )

        assert response == "Default response"
        mock_create_client.assert_called_once_with("default", 0.5)
