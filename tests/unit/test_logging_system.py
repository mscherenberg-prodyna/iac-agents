"""Unit tests for logging_system module."""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.iac_agents.logging_system import (
    AgentLogEntry,
    AgentLogger,
    LogLevel,
    log_agent_complete,
    log_agent_start,
    log_error,
    log_info,
    log_user_update,
    log_warning,
)


class TestLogLevel:
    """Test LogLevel enum."""

    def test_log_levels_exist(self):
        """Test that all expected log levels exist."""
        expected_levels = [
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "AGENT_START",
            "AGENT_COMPLETE",
            "USER_UPDATE",
        ]

        for level in expected_levels:
            assert hasattr(LogLevel, level)

    def test_log_level_values(self):
        """Test log level string values."""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.AGENT_START.value == "AGENT_START"
        assert LogLevel.USER_UPDATE.value == "USER_UPDATE"


class TestAgentLogEntry:
    """Test AgentLogEntry dataclass."""

    def test_agent_log_entry_creation(self):
        """Test creating an AgentLogEntry."""
        timestamp = datetime.now()
        entry = AgentLogEntry(
            timestamp=timestamp,
            agent_name="TestAgent",
            activity="Testing",
            level=LogLevel.INFO,
            details={"key": "value"},
        )

        assert entry.timestamp == timestamp
        assert entry.agent_name == "TestAgent"
        assert entry.activity == "Testing"
        assert entry.level == LogLevel.INFO
        assert entry.details == {"key": "value"}
        assert entry.duration_ms == 0

    def test_agent_log_entry_with_duration(self):
        """Test creating an AgentLogEntry with duration."""
        entry = AgentLogEntry(
            timestamp=datetime.now(),
            agent_name="TestAgent",
            activity="Testing",
            level=LogLevel.AGENT_COMPLETE,
            details={},
            duration_ms=1500,
        )

        assert entry.duration_ms == 1500


class TestAgentLogger:
    """Test AgentLogger class."""

    @patch("src.iac_agents.logging_system.logging")
    @patch("src.iac_agents.logging_system.Path")
    def test_agent_logger_initialization(self, mock_path, mock_logging):
        """Test AgentLogger initialization."""
        mock_path.return_value.mkdir = Mock()

        logger = AgentLogger()

        assert logger.log_entries == []
        assert logger.active_agents == {}

    @patch("src.iac_agents.logging_system.logging")
    @patch("src.iac_agents.logging_system.Path")
    def test_log_agent_start(self, mock_path, mock_logging):
        """Test logging agent start."""
        mock_path.return_value.mkdir = Mock()
        logger = AgentLogger()

        logger.log_agent_start("TestAgent", "Test Activity", {"key": "value"})

        assert len(logger.log_entries) == 1
        assert "TestAgent" in logger.active_agents

        entry = logger.log_entries[0]
        assert entry.agent_name == "TestAgent"
        assert entry.activity == "Test Activity"
        assert entry.level == LogLevel.AGENT_START
        assert entry.details == {"key": "value"}

    @patch("src.iac_agents.logging_system.logging")
    @patch("src.iac_agents.logging_system.Path")
    def test_log_agent_complete(self, mock_path, mock_logging):
        """Test logging agent completion."""
        mock_path.return_value.mkdir = Mock()
        logger = AgentLogger()

        # Start an agent first
        logger.log_agent_start("TestAgent", "Test Activity")

        # Complete the agent
        logger.log_agent_complete("TestAgent", "Test Activity", {"result": "success"})

        assert len(logger.log_entries) == 2
        assert "TestAgent" not in logger.active_agents

        complete_entry = logger.log_entries[1]
        assert complete_entry.agent_name == "TestAgent"
        assert complete_entry.level == LogLevel.AGENT_COMPLETE
        assert complete_entry.duration_ms > 0  # Should have calculated duration

    @patch("src.iac_agents.logging_system.logging")
    @patch("src.iac_agents.logging_system.Path")
    def test_log_user_update(self, mock_path, mock_logging):
        """Test logging user updates."""
        mock_path.return_value.mkdir = Mock()
        logger = AgentLogger()

        logger.log_user_update("User message", {"context": "test"})

        assert len(logger.log_entries) == 1

        entry = logger.log_entries[0]
        assert entry.agent_name == "SYSTEM"
        assert entry.activity == "User message"
        assert entry.level == LogLevel.USER_UPDATE

    @patch("src.iac_agents.logging_system.logging")
    @patch("src.iac_agents.logging_system.Path")
    def test_get_recent_logs(self, mock_path, mock_logging):
        """Test getting recent log entries."""
        mock_path.return_value.mkdir = Mock()
        logger = AgentLogger()

        # Add multiple log entries
        for i in range(15):
            logger.log_info(f"Agent{i}", f"Message {i}")

        recent_logs = logger.get_recent_logs(limit=5)
        assert len(recent_logs) == 5
        # Should return the most recent entries
        assert recent_logs[-1].activity == "Message 14"

    @patch("src.iac_agents.logging_system.logging")
    @patch("src.iac_agents.logging_system.Path")
    def test_get_logs_for_agent(self, mock_path, mock_logging):
        """Test getting logs for specific agent."""
        mock_path.return_value.mkdir = Mock()
        logger = AgentLogger()

        logger.log_info("Agent1", "Message from Agent1")
        logger.log_info("Agent2", "Message from Agent2")
        logger.log_info("Agent1", "Another message from Agent1")

        agent1_logs = logger.get_logs_for_agent("Agent1")
        assert len(agent1_logs) == 2
        assert all(log.agent_name == "Agent1" for log in agent1_logs)

    @patch("src.iac_agents.logging_system.logging")
    @patch("src.iac_agents.logging_system.Path")
    def test_clear_logs(self, mock_path, mock_logging):
        """Test clearing all logs."""
        mock_path.return_value.mkdir = Mock()
        logger = AgentLogger()

        logger.log_info("TestAgent", "Test message")
        logger.log_agent_start("TestAgent", "Test activity")

        assert len(logger.log_entries) > 0
        assert len(logger.active_agents) > 0

        logger.clear_logs()

        assert len(logger.log_entries) == 0
        assert len(logger.active_agents) == 0


class TestConvenienceFunctions:
    """Test convenience logging functions."""

    @patch("src.iac_agents.logging_system.agent_logger")
    def test_log_agent_start_function(self, mock_logger):
        """Test log_agent_start convenience function."""
        log_agent_start("TestAgent", "Test Activity", {"key": "value"})

        mock_logger.log_agent_start.assert_called_once_with(
            "TestAgent", "Test Activity", {"key": "value"}
        )

    @patch("src.iac_agents.logging_system.agent_logger")
    def test_log_agent_complete_function(self, mock_logger):
        """Test log_agent_complete convenience function."""
        log_agent_complete("TestAgent", "Test Activity", {"result": "success"})

        mock_logger.log_agent_complete.assert_called_once_with(
            "TestAgent", "Test Activity", {"result": "success"}
        )

    @patch("src.iac_agents.logging_system.agent_logger")
    def test_log_info_function(self, mock_logger):
        """Test log_info convenience function."""
        log_info("TestAgent", "Info message", {"context": "test"})

        mock_logger.log_info.assert_called_once_with(
            "TestAgent", "Info message", {"context": "test"}
        )

    @patch("src.iac_agents.logging_system.agent_logger")
    def test_log_warning_function(self, mock_logger):
        """Test log_warning convenience function."""
        log_warning("TestAgent", "Warning message")

        mock_logger.log_warning.assert_called_once_with(
            "TestAgent", "Warning message", None
        )

    @patch("src.iac_agents.logging_system.agent_logger")
    def test_log_error_function(self, mock_logger):
        """Test log_error convenience function."""
        log_error("TestAgent", "Error message", {"error_code": 500})

        mock_logger.log_error.assert_called_once_with(
            "TestAgent", "Error message", {"error_code": 500}
        )
