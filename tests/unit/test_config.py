"""Unit tests for configuration management."""

import pytest

from src.iac_agents.config.settings import (AgentSettings, ComplianceSettings,
                                            UISettings, config)


@pytest.mark.unit
def test_config_initialization():
    """Test that configuration initializes with expected defaults."""
    assert config.compliance.minimum_score_enforced == 70.0
    assert config.compliance.minimum_score_relaxed == 40.0
    assert config.agents.default_temperature == 0.2
    assert config.ui.page_title == "Infrastructure as Prompts AI Agent"


@pytest.mark.unit
def test_compliance_settings():
    """Test compliance settings structure."""
    compliance = ComplianceSettings()

    assert compliance.minimum_score_enforced > compliance.minimum_score_relaxed
    assert compliance.max_violations_enforced < compliance.max_violations_relaxed

    # Test available frameworks
    assert "PCI DSS" in compliance.available_frameworks
    assert "GDPR" in compliance.available_frameworks
    assert "HIPAA" in compliance.available_frameworks


@pytest.mark.unit
def test_agent_settings():
    """Test agent configuration settings."""
    agents = AgentSettings()

    assert 0 <= agents.default_temperature <= 1
    assert 0 <= agents.terraform_agent_temperature <= 1
    assert agents.max_response_tokens > 0
    assert agents.request_timeout > 0


@pytest.mark.unit
def test_ui_settings():
    """Test UI configuration settings."""
    ui = UISettings()

    assert ui.max_chat_messages > 0
    assert ui.activity_log_entries > 0
    assert ui.auto_scroll_delay > 0
    assert ui.page_title
    assert ui.page_icon
