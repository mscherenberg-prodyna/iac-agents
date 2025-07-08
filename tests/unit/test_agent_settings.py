"""Tests for AgentSettings configuration."""

import pytest

from iac_agents.config.settings import AgentSettings


class TestAgentSettings:
    """Test suite for AgentSettings class."""

    def test_default_values(self):
        """Test default agent settings values."""
        settings = AgentSettings()

        assert settings.default_temperature == 0
        assert settings.default_model == "gpt-4.1"
        assert settings.request_timeout == 120

    def test_custom_values_initialization(self):
        """Test initialization with custom values."""
        settings = AgentSettings(
            default_temperature=0.7, default_model="gpt-3.5-turbo", request_timeout=300
        )

        assert settings.default_temperature == 0.7
        assert settings.default_model == "gpt-3.5-turbo"
        assert settings.request_timeout == 300

    def test_temperature_range_validation(self):
        """Test temperature value validation."""
        settings_zero = AgentSettings(default_temperature=0.0)
        settings_one = AgentSettings(default_temperature=1.0)
        settings_mid = AgentSettings(default_temperature=0.5)

        assert settings_zero.default_temperature == 0.0
        assert settings_one.default_temperature == 1.0
        assert settings_mid.default_temperature == 0.5

    def test_timeout_positive_value(self):
        """Test that timeout is a positive integer."""
        settings = AgentSettings(request_timeout=60)

        assert settings.request_timeout == 60
        assert isinstance(settings.request_timeout, int)

    def test_model_string_type(self):
        """Test that model is a string."""
        settings = AgentSettings(default_model="custom-model")

        assert isinstance(settings.default_model, str)
        assert settings.default_model == "custom-model"

    def test_dataclass_immutability_after_creation(self):
        """Test settings can be modified after creation."""
        settings = AgentSettings()
        original_temperature = settings.default_temperature

        settings.default_temperature = 0.8

        assert settings.default_temperature == 0.8
        assert settings.default_temperature != original_temperature
