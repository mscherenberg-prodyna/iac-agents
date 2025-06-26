"""Basic unit tests for logging system."""

from unittest.mock import Mock, patch

import pytest

from src.iac_agents.logging_system import AgentLogEntry, LogLevel, log_agent_start


class TestLogLevel:
    """Test LogLevel enum."""

    def test_log_levels_exist(self):
        """All expected log levels should exist."""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.AGENT_START.value == "AGENT_START"
        assert LogLevel.USER_UPDATE.value == "USER_UPDATE"


class TestAgentLogEntry:
    """Test AgentLogEntry dataclass."""

    def test_create_log_entry(self):
        """Should create log entry with required fields."""
        from datetime import datetime

        entry = AgentLogEntry(
            timestamp=datetime.now(),
            agent_name="TestAgent",
            activity="Testing",
            level=LogLevel.INFO,
            details={},
        )

        assert entry.agent_name == "TestAgent"
        assert entry.activity == "Testing"
        assert entry.level == LogLevel.INFO
        assert entry.duration_ms == 0


class TestConvenienceFunctions:
    """Test convenience logging functions."""

    @patch("src.iac_agents.logging_system.agent_logger")
    def test_log_agent_start_function(self, mock_logger):
        """Should call agent_logger.log_agent_start."""
        log_agent_start("TestAgent", "Test Activity")

        mock_logger.log_agent_start.assert_called_once_with(
            "TestAgent", "Test Activity", None
        )
