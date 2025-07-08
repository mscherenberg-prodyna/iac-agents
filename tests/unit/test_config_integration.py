"""Tests for Config class and integration."""

import os
from unittest.mock import patch

import pytest

from iac_agents.config.settings import Config


class TestConfig:
    """Test suite for Config class."""

    @patch("iac_agents.config.settings.load_dotenv")
    def test_config_initialization(self, mock_load_dotenv):
        """Test Config class initialization."""
        config = Config()

        mock_load_dotenv.assert_called_once()
        assert hasattr(config, "compliance")
        assert hasattr(config, "azure_openai")
        assert hasattr(config, "azure_ai")
        assert hasattr(config, "agents")
        assert hasattr(config, "ui")
        assert hasattr(config, "logging")
        assert hasattr(config, "workflow")

    @patch("iac_agents.config.settings.load_dotenv")
    def test_load_from_env_classmethod(self, mock_load_dotenv):
        """Test Config.load_from_env class method."""
        config = Config.load_from_env()

        mock_load_dotenv.assert_called_once()
        assert isinstance(config, Config)

    def test_config_attributes_types(self):
        """Test that config attributes have correct types."""
        config = Config()

        from iac_agents.config.settings import (
            AgentSettings,
            AzureAISettings,
            AzureOpenAISettings,
            ComplianceSettings,
            LoggingSettings,
            UISettings,
            WorkflowSettings,
        )

        assert isinstance(config.compliance, ComplianceSettings)
        assert isinstance(config.azure_openai, AzureOpenAISettings)
        assert isinstance(config.azure_ai, AzureAISettings)
        assert isinstance(config.agents, AgentSettings)
        assert isinstance(config.ui, UISettings)
        assert isinstance(config.logging, LoggingSettings)
        assert isinstance(config.workflow, WorkflowSettings)

    @patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_ENDPOINT": "https://integration.test.com",
            "AZURE_OPENAI_API_KEY": "integration-key",
        },
    )
    @patch("iac_agents.config.settings.load_dotenv")
    def test_config_environment_integration(self, mock_load_dotenv):
        """Test Config integration with environment variables."""
        config = Config()

        assert config.azure_openai.endpoint == "https://integration.test.com"
        assert config.azure_openai.api_key == "integration-key"

    def test_config_default_values(self):
        """Test Config default values are set correctly."""
        config = Config()

        assert config.agents.default_temperature == 0
        assert config.agents.default_model == "gpt-4.1"
        assert config.ui.page_title == "Infrastructure as Prompts"
        assert config.ui.page_icon == "🤖"
        assert config.logging.log_level == "INFO"
        assert config.workflow.max_workflow_stages == 10
