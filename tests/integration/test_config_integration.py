"""Integration tests for configuration system."""

import pytest

from src.iac_agents.config.settings import config


class TestConfigIntegration:
    """Test configuration system integration."""

    def test_config_accessibility(self):
        """Test that config is accessible from global import."""
        # Should be able to access all config sections
        assert config.compliance.minimum_score_enforced > 0
        assert config.agents.default_temperature >= 0
        assert config.ui.page_title is not None
        assert config.workflow.max_workflow_stages > 0

    def test_config_values_reasonable(self):
        """Test that config values are within reasonable ranges."""
        # Temperature should be between 0 and 2
        assert 0 <= config.agents.default_temperature <= 2.0
        assert 0 <= config.agents.terraform_agent_temperature <= 2.0

        # Timeouts should be positive
        assert config.agents.request_timeout > 0
        assert config.workflow.stage_timeout > 0

        # UI values should be positive
        assert config.ui.max_chat_messages > 0
        assert config.ui.activity_log_entries > 0

    def test_compliance_frameworks_complete(self):
        """Test that compliance frameworks are properly configured."""
        frameworks = config.compliance.available_frameworks

        # Should have at least standard frameworks
        expected_frameworks = ["PCI DSS", "GDPR", "HIPAA", "SOX"]
        for framework in expected_frameworks:
            assert framework in frameworks
            assert isinstance(frameworks[framework], str)
            assert len(frameworks[framework]) > 0
