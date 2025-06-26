"""Basic unit tests for configuration settings."""

from unittest.mock import patch

import pytest

from src.iac_agents.config.settings import (
    AzureOpenAISettings,
    ComplianceSettings,
    Config,
    config,
)


class TestComplianceSettings:
    """Test compliance configuration."""

    def test_default_values(self):
        """Should have correct default values."""
        settings = ComplianceSettings()
        assert settings.minimum_score_enforced == 70.0
        assert settings.minimum_score_relaxed == 40.0

    def test_available_frameworks(self):
        """Should include standard compliance frameworks."""
        settings = ComplianceSettings()
        assert "PCI DSS" in settings.available_frameworks
        assert "GDPR" in settings.available_frameworks


class TestAzureOpenAISettings:
    """Test Azure OpenAI configuration."""

    def test_default_api_version(self):
        """Should have default API version."""
        settings = AzureOpenAISettings()
        assert settings.api_version == "2024-02-15-preview"

    @patch.dict(
        "os.environ",
        {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "test-key",
        },
    )
    def test_load_from_environment(self):
        """Should load values from environment variables."""
        settings = AzureOpenAISettings()
        assert settings.endpoint == "https://test.openai.azure.com"
        assert settings.api_key == "test-key"


class TestGlobalConfig:
    """Test global configuration instance."""

    def test_config_instance_exists(self):
        """Global config instance should exist."""
        assert isinstance(config, Config)
        assert hasattr(config, "compliance")
        assert hasattr(config, "azure_openai")

    def test_config_components_initialized(self):
        """All config components should be properly initialized."""
        assert isinstance(config.compliance, ComplianceSettings)
        assert isinstance(config.azure_openai, AzureOpenAISettings)
