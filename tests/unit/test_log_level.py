"""Tests for LogLevel enum."""

import pytest

from iac_agents.logging_system import LogLevel


class TestLogLevel:
    """Test suite for LogLevel enum."""

    def test_log_level_values(self):
        """Test LogLevel enum has expected values."""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.AGENT_START.value == "AGENT_START"
        assert LogLevel.AGENT_COMPLETE.value == "AGENT_COMPLETE"
        assert LogLevel.USER_UPDATE.value == "USER_UPDATE"

    def test_log_level_count(self):
        """Test LogLevel enum has expected number of values."""
        log_levels = list(LogLevel)
        assert len(log_levels) == 7

    def test_log_level_string_representation(self):
        """Test LogLevel enum string representation."""
        assert str(LogLevel.INFO) == "LogLevel.INFO"
        assert str(LogLevel.ERROR) == "LogLevel.ERROR"
        assert str(LogLevel.AGENT_START) == "LogLevel.AGENT_START"

    def test_log_level_equality(self):
        """Test LogLevel enum equality comparison."""
        assert LogLevel.DEBUG == LogLevel.DEBUG
        assert LogLevel.INFO != LogLevel.WARNING
        assert LogLevel.AGENT_START != LogLevel.AGENT_COMPLETE

    def test_log_level_iteration(self):
        """Test LogLevel enum can be iterated."""
        expected_values = [
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "AGENT_START",
            "AGENT_COMPLETE",
            "USER_UPDATE",
        ]

        actual_values = [level.value for level in LogLevel]

        assert actual_values == expected_values

    def test_log_level_membership(self):
        """Test LogLevel enum membership."""
        assert LogLevel.DEBUG in LogLevel
        assert LogLevel.INFO in LogLevel
        assert LogLevel.AGENT_START in LogLevel
