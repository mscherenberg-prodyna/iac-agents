"""Tests for AzureOpenAISettings configuration."""

import os
from unittest.mock import patch

import pytest

from iac_agents.config.settings import AzureOpenAISettings


class TestAzureOpenAISettings:
    """Test suite for AzureOpenAISettings class."""

    @patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT": "gpt-4-deployment",
            "AZURE_OPENAI_API_VERSION": "2023-12-01-preview",
            "CODEX_DEPLOYMENT": "codex-deployment",
        },
    )
    def test_initialization_from_environment(self):
        """Test initialization from environment variables."""
        settings = AzureOpenAISettings()

        assert settings.endpoint == "https://test.openai.azure.com"
        assert settings.api_key == "test-api-key"
        assert settings.deployment["default"] == "gpt-4-deployment"
        assert settings.deployment["cloud_engineer"] == "codex-deployment"
        assert settings.api_version == "2023-12-01-preview"

    @patch.dict(
        os.environ,
        {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "test-api-key",
            "AZURE_OPENAI_DEPLOYMENT": "gpt-4-deployment",
            "AZURE_OPENAI_API_VERSION": "2023-12-01-preview",
        },
    )
    def test_initialization_without_codex_deployment(self):
        """Test initialization without CODEX_DEPLOYMENT set."""
        settings = AzureOpenAISettings()

        assert settings.deployment["default"] == "gpt-4-deployment"
        assert settings.deployment["cloud_engineer"] == "gpt-4-deployment"

    def test_initialization_with_explicit_values(self):
        """Test initialization with explicitly provided values."""
        custom_deployment = {
            "default": "custom-deployment",
            "cloud_engineer": "custom-codex",
        }

        settings = AzureOpenAISettings(
            endpoint="https://custom.endpoint.com",
            api_key="custom-key",
            deployment=custom_deployment,
            api_version="2023-11-01-preview",
        )

        assert settings.endpoint == "https://custom.endpoint.com"
        assert settings.api_key == "custom-key"
        assert settings.deployment == custom_deployment
        assert settings.api_version == "2023-11-01-preview"

    @patch.dict(os.environ, {}, clear=True)
    def test_initialization_with_missing_environment_variables(self):
        """Test initialization when environment variables are missing."""
        settings = AzureOpenAISettings()

        assert settings.endpoint is None
        assert settings.api_key is None
        assert settings.deployment["default"] is None
        assert settings.deployment["cloud_engineer"] is None
        assert settings.api_version is None

    def test_deployment_structure(self):
        """Test that deployment dictionary has correct structure."""
        settings = AzureOpenAISettings()

        assert isinstance(settings.deployment, dict)
        assert "default" in settings.deployment
        assert "cloud_engineer" in settings.deployment
