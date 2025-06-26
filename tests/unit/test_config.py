"""Unit tests for config.settings module."""

import os
from unittest.mock import patch

import pytest

from src.iac_agents.config.settings import (
    AgentSettings,
    AzureAISettings,
    AzureOpenAISettings,
    ComplianceSettings,
    Config,
    LoggingSettings,
    UISettings,
    WorkflowSettings,
    config,
)


class TestComplianceSettings:
    """Test ComplianceSettings configuration."""

    def test_compliance_settings_defaults(self):
        """Test default values for ComplianceSettings."""
        settings = ComplianceSettings()
        assert settings.minimum_score_enforced == 70.0
        assert settings.minimum_score_relaxed == 40.0
        assert settings.max_violations_enforced == 3
        assert settings.max_violations_relaxed == 8

    def test_compliance_settings_frameworks(self):
        """Test available compliance frameworks."""
        settings = ComplianceSettings()
        expected_frameworks = {
            "PCI DSS": "Payment Card Industry Data Security Standard",
            "HIPAA": "Health Insurance Portability and Accountability Act",
            "SOX": "Sarbanes-Oxley Act",
            "GDPR": "General Data Protection Regulation",
            "ISO 27001": "Information Security Management",
            "SOC 2": "Service Organization Control 2",
        }
        assert settings.available_frameworks == expected_frameworks

    def test_compliance_settings_custom_frameworks(self):
        """Test ComplianceSettings with custom frameworks."""
        custom_frameworks = {"CUSTOM": "Custom Framework"}
        settings = ComplianceSettings(available_frameworks=custom_frameworks)
        assert settings.available_frameworks == custom_frameworks


class TestAzureOpenAISettings:
    """Test AzureOpenAISettings configuration."""

    def test_azure_openai_settings_defaults(self):
        """Test default values for AzureOpenAISettings."""
        settings = AzureOpenAISettings()
        assert settings.api_version == "2024-02-15-preview"

    @patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_DEPLOYMENT": "test-deployment",
            "AZURE_OPENAI_API_VERSION": "2024-03-01",
        },
    )
    def test_azure_openai_settings_from_env(self):
        """Test AzureOpenAISettings loading from environment variables."""
        settings = AzureOpenAISettings()
        assert settings.endpoint == "https://test.openai.azure.com"
        assert settings.api_key == "test-key"
        assert settings.deployment == "test-deployment"
        assert settings.api_version == "2024-03-01"

    def test_azure_openai_settings_explicit_values(self):
        """Test AzureOpenAISettings with explicit values."""
        settings = AzureOpenAISettings(
            endpoint="https://custom.openai.azure.com",
            api_key="custom-key",
            deployment="custom-deployment",
        )
        assert settings.endpoint == "https://custom.openai.azure.com"
        assert settings.api_key == "custom-key"
        assert settings.deployment == "custom-deployment"


class TestAzureAISettings:
    """Test AzureAISettings configuration."""

    @patch.dict(
        os.environ,
        {
            "AZURE_PROJECT_ENDPOINT": "https://test.project.azure.ai",
            "AZURE_AGENT_ID": "test-agent-123",
        },
    )
    def test_azure_ai_settings_from_env(self):
        """Test AzureAISettings loading from environment variables."""
        settings = AzureAISettings()
        assert settings.project_endpoint == "https://test.project.azure.ai"
        assert settings.agent_id == "test-agent-123"

    def test_azure_ai_settings_defaults(self):
        """Test AzureAISettings with no environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            settings = AzureAISettings()
            assert settings.project_endpoint is None
            assert settings.agent_id is None


class TestAgentSettings:
    """Test AgentSettings configuration."""

    def test_agent_settings_defaults(self):
        """Test default values for AgentSettings."""
        settings = AgentSettings()
        assert settings.default_temperature == 0.2
        assert settings.terraform_agent_temperature == 0.1
        assert settings.max_response_tokens == 4000
        assert settings.request_timeout == 120

    def test_agent_settings_custom_values(self):
        """Test AgentSettings with custom values."""
        settings = AgentSettings(
            default_temperature=0.5,
            terraform_agent_temperature=0.3,
            max_response_tokens=8000,
            request_timeout=300,
        )
        assert settings.default_temperature == 0.5
        assert settings.terraform_agent_temperature == 0.3
        assert settings.max_response_tokens == 8000
        assert settings.request_timeout == 300


class TestUISettings:
    """Test UISettings configuration."""

    def test_ui_settings_defaults(self):
        """Test default values for UISettings."""
        settings = UISettings()
        assert settings.max_chat_messages == 50
        assert settings.activity_log_entries == 5
        assert settings.auto_scroll_delay == 200
        assert settings.page_title == "Infrastructure as Prompts"
        assert settings.page_icon == "🤖"

    def test_ui_settings_custom_values(self):
        """Test UISettings with custom values."""
        settings = UISettings(
            max_chat_messages=100,
            activity_log_entries=10,
            auto_scroll_delay=500,
            page_title="Custom Title",
            page_icon="🔧",
        )
        assert settings.max_chat_messages == 100
        assert settings.activity_log_entries == 10
        assert settings.auto_scroll_delay == 500
        assert settings.page_title == "Custom Title"
        assert settings.page_icon == "🔧"


class TestLoggingSettings:
    """Test LoggingSettings configuration."""

    def test_logging_settings_defaults(self):
        """Test default values for LoggingSettings."""
        settings = LoggingSettings()
        assert settings.log_level == "INFO"
        assert settings.max_log_entries == 100
        assert settings.log_retention_hours == 24

    def test_logging_settings_custom_values(self):
        """Test LoggingSettings with custom values."""
        settings = LoggingSettings(
            log_level="DEBUG", max_log_entries=500, log_retention_hours=72
        )
        assert settings.log_level == "DEBUG"
        assert settings.max_log_entries == 500
        assert settings.log_retention_hours == 72


class TestWorkflowSettings:
    """Test WorkflowSettings configuration."""

    def test_workflow_settings_defaults(self):
        """Test default values for WorkflowSettings."""
        settings = WorkflowSettings()
        assert settings.max_workflow_stages == 10
        assert settings.stage_timeout == 300
        assert settings.max_template_regeneration_attempts == 2

    def test_workflow_settings_custom_values(self):
        """Test WorkflowSettings with custom values."""
        settings = WorkflowSettings(
            max_workflow_stages=15,
            stage_timeout=600,
            max_template_regeneration_attempts=5,
        )
        assert settings.max_workflow_stages == 15
        assert settings.stage_timeout == 600
        assert settings.max_template_regeneration_attempts == 5


class TestConfig:
    """Test Config class."""

    def test_config_initialization(self):
        """Test Config class initialization."""
        config_instance = Config()

        assert isinstance(config_instance.compliance, ComplianceSettings)
        assert isinstance(config_instance.azure_openai, AzureOpenAISettings)
        assert isinstance(config_instance.azure_ai, AzureAISettings)
        assert isinstance(config_instance.agents, AgentSettings)
        assert isinstance(config_instance.ui, UISettings)
        assert isinstance(config_instance.logging, LoggingSettings)
        assert isinstance(config_instance.workflow, WorkflowSettings)

    def test_config_load_from_env(self):
        """Test Config.load_from_env class method."""
        config_instance = Config.load_from_env()
        assert isinstance(config_instance, Config)

    def test_global_config_instance(self):
        """Test that global config instance exists and is properly initialized."""
        assert isinstance(config, Config)
        assert isinstance(config.compliance, ComplianceSettings)
        assert isinstance(config.azure_openai, AzureOpenAISettings)
        assert config.agents.default_temperature == 0.2
        assert config.ui.page_title == "Infrastructure as Prompts"


class TestIntegration:
    """Integration tests for configuration system."""

    def test_config_values_consistency(self):
        """Test that config values are consistent across components."""
        config_instance = Config()

        # Test that temperature settings are reasonable
        assert 0.0 <= config_instance.agents.default_temperature <= 2.0
        assert 0.0 <= config_instance.agents.terraform_agent_temperature <= 2.0

        # Test that timeout values are positive
        assert config_instance.agents.request_timeout > 0
        assert config_instance.workflow.stage_timeout > 0

        # Test that UI settings make sense
        assert config_instance.ui.max_chat_messages > 0
        assert config_instance.ui.activity_log_entries > 0
        assert config_instance.ui.auto_scroll_delay >= 0

    def test_compliance_framework_access(self):
        """Test accessing compliance frameworks from global config."""
        frameworks = config.compliance.available_frameworks
        assert "PCI DSS" in frameworks
        assert "GDPR" in frameworks
        assert len(frameworks) >= 6

    def test_agent_settings_access(self):
        """Test accessing agent settings from global config."""
        assert config.agents.default_temperature == 0.2
        assert config.agents.terraform_agent_temperature == 0.1
        assert config.agents.max_response_tokens == 4000
