"""Unit tests for LLM-related utilities in agents.utils module."""

from unittest.mock import Mock, patch

import pytest

from src.iac_agents.agents.utils import create_llm_client, make_llm_call


class TestCreateLLMClient:
    """Test create_llm_client function."""

    @patch("src.iac_agents.agents.utils.AzureChatOpenAI")
    @patch("src.iac_agents.agents.utils.config")
    def test_create_llm_client_default_temperature(
        self, mock_config, mock_azure_client
    ):
        """Test creating LLM client with default temperature."""
        # Setup mocks
        mock_config.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_config.azure_openai.deployment = "gpt-4"
        mock_config.azure_openai.api_version = "2024-02-15-preview"
        mock_config.azure_openai.api_key = "test-key"
        mock_config.agents.default_temperature = 0.2
        mock_config.agents.max_response_tokens = 4000

        create_llm_client()

        mock_azure_client.assert_called_once_with(
            azure_endpoint="https://test.openai.azure.com",
            azure_deployment="gpt-4",
            api_version="2024-02-15-preview",
            api_key="test-key",
            temperature=0.2,
            max_tokens=4000,
        )

    @patch("src.iac_agents.agents.utils.AzureChatOpenAI")
    @patch("src.iac_agents.agents.utils.config")
    def test_create_llm_client_custom_temperature(self, mock_config, mock_azure_client):
        """Test creating LLM client with custom temperature."""
        # Setup mocks
        mock_config.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_config.azure_openai.deployment = "gpt-4"
        mock_config.azure_openai.api_version = "2024-02-15-preview"
        mock_config.azure_openai.api_key = "test-key"
        mock_config.agents.default_temperature = 0.2
        mock_config.agents.max_response_tokens = 4000

        create_llm_client(temperature=0.7)

        mock_azure_client.assert_called_once_with(
            azure_endpoint="https://test.openai.azure.com",
            azure_deployment="gpt-4",
            api_version="2024-02-15-preview",
            api_key="test-key",
            temperature=0.7,
            max_tokens=4000,
        )


class TestMakeLLMCall:
    """Test make_llm_call function."""

    @patch("src.iac_agents.agents.utils.create_llm_client")
    def test_make_llm_call_success(self, mock_create_client):
        """Test successful LLM call."""
        # Setup mock
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response
        mock_create_client.return_value = mock_llm

        result = make_llm_call("System prompt", "User message")

        assert result == "Test response"
        mock_llm.invoke.assert_called_once_with(
            [("system", "System prompt"), ("human", "User message")]
        )

    @patch("src.iac_agents.agents.utils.create_llm_client")
    def test_make_llm_call_with_custom_temperature(self, mock_create_client):
        """Test LLM call with custom temperature."""
        # Setup mock
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response
        mock_create_client.return_value = mock_llm

        result = make_llm_call("System prompt", "User message", temperature=0.5)

        assert result == "Test response"
        # Check that temperature was passed as positional argument
        mock_create_client.assert_called_once_with(0.5)
