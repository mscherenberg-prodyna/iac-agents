"""Tests for ComplianceSettings configuration."""

import pytest

from iac_agents.config.settings import ComplianceSettings


class TestComplianceSettings:
    """Test suite for ComplianceSettings class."""

    def test_default_frameworks_initialization(self):
        """Test default compliance frameworks are set correctly."""
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

    def test_custom_frameworks_initialization(self):
        """Test custom compliance frameworks initialization."""
        custom_frameworks = {
            "NIST": "National Institute of Standards and Technology",
            "FedRAMP": "Federal Risk and Authorization Management Program",
        }

        settings = ComplianceSettings(available_frameworks=custom_frameworks)

        assert settings.available_frameworks == custom_frameworks

    def test_frameworks_not_overridden_when_provided(self):
        """Test that custom frameworks are not overridden."""
        custom_frameworks = {"Custom": "Custom Framework"}
        settings = ComplianceSettings(available_frameworks=custom_frameworks)

        assert "PCI DSS" not in settings.available_frameworks
        assert settings.available_frameworks["Custom"] == "Custom Framework"

    def test_empty_frameworks_initialization(self):
        """Test initialization with empty frameworks dictionary."""
        settings = ComplianceSettings(available_frameworks={})

        assert settings.available_frameworks == {}

    def test_frameworks_contains_expected_standards(self):
        """Test that default frameworks contain expected security standards."""
        settings = ComplianceSettings()
        frameworks = settings.available_frameworks

        assert "PCI DSS" in frameworks
        assert "HIPAA" in frameworks
        assert "GDPR" in frameworks
        assert "ISO 27001" in frameworks
        assert len(frameworks) == 6

    def test_framework_descriptions_are_strings(self):
        """Test that all framework descriptions are strings."""
        settings = ComplianceSettings()

        for framework, description in settings.available_frameworks.items():
            assert isinstance(framework, str)
            assert isinstance(description, str)
            assert len(description) > 0
