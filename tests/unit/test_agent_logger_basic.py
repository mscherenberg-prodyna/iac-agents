"""Tests for AgentLogger basic functionality."""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from iac_agents.logging_system import AgentLogger, LogLevel


class TestAgentLoggerBasic:
    """Test suite for AgentLogger basic functionality."""

    def test_logger_initialization(self):
        """Test AgentLogger initialization."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            assert hasattr(logger, "log_entries")
            assert hasattr(logger, "active_agents")
            assert isinstance(logger.log_entries, list)
            assert isinstance(logger.active_agents, dict)
            assert len(logger.log_entries) == 0
            assert len(logger.active_agents) == 0

    def test_log_agent_start(self):
        """Test logging agent start."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            logger.log_agent_start("test_agent", "test_activity")

            assert len(logger.log_entries) == 1
            assert "test_agent" in logger.active_agents

            entry = logger.log_entries[0]
            assert entry.agent_name == "test_agent"
            assert entry.activity == "test_activity"
            assert entry.level == LogLevel.AGENT_START

    def test_log_agent_complete(self):
        """Test logging agent completion."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            logger.log_agent_start("test_agent", "test_activity")
            logger.log_agent_complete("test_agent", "test_activity")

            assert len(logger.log_entries) == 2
            assert "test_agent" not in logger.active_agents

            complete_entry = logger.log_entries[1]
            assert complete_entry.level == LogLevel.AGENT_COMPLETE
            assert complete_entry.duration_ms >= 0

    def test_log_info(self):
        """Test logging info message."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            logger.log_info("test_agent", "info message")

            assert len(logger.log_entries) == 1
            entry = logger.log_entries[0]
            assert entry.level == LogLevel.INFO
            assert entry.activity == "info message"

    def test_log_warning(self):
        """Test logging warning message."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            logger.log_warning("test_agent", "warning message")

            assert len(logger.log_entries) == 1
            entry = logger.log_entries[0]
            assert entry.level == LogLevel.WARNING
            assert entry.activity == "warning message"

    def test_log_error(self):
        """Test logging error message."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            logger.log_error("test_agent", "error message")

            assert len(logger.log_entries) == 1
            entry = logger.log_entries[0]
            assert entry.level == LogLevel.ERROR
            assert entry.activity == "error message"

    def test_log_user_update(self):
        """Test logging user update."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            logger.log_user_update("user update message")

            assert len(logger.log_entries) == 1
            entry = logger.log_entries[0]
            assert entry.level == LogLevel.USER_UPDATE
            assert entry.agent_name == "SYSTEM"
            assert entry.activity == "user update message"
