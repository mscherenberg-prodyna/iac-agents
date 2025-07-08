"""Tests for AgentLogger log retrieval functionality."""

from unittest.mock import patch

import pytest

from iac_agents.logging_system import AgentLogger, LogLevel


class TestAgentLoggerRetrieval:
    """Test suite for AgentLogger log retrieval functionality."""

    def test_get_recent_logs(self):
        """Test getting recent log entries."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            # Add multiple log entries
            for i in range(15):
                logger.log_info(f"agent_{i}", f"message_{i}")

            recent_logs = logger.get_recent_logs(10)

            assert len(recent_logs) == 10
            # Should get the last 10 entries
            assert recent_logs[0].activity == "message_5"
            assert recent_logs[-1].activity == "message_14"

    def test_get_recent_logs_fewer_than_limit(self):
        """Test getting recent logs when fewer entries exist."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            logger.log_info("agent_1", "message_1")
            logger.log_info("agent_2", "message_2")

            recent_logs = logger.get_recent_logs(10)

            assert len(recent_logs) == 2

    def test_get_logs_for_agent(self):
        """Test getting logs for specific agent."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            logger.log_info("agent_1", "message_1")
            logger.log_info("agent_2", "message_2")
            logger.log_info("agent_1", "message_3")
            logger.log_info("agent_2", "message_4")

            agent_1_logs = logger.get_logs_for_agent("agent_1")

            assert len(agent_1_logs) == 2
            assert all(log.agent_name == "agent_1" for log in agent_1_logs)
            assert agent_1_logs[0].activity == "message_1"
            assert agent_1_logs[1].activity == "message_3"

    def test_get_logs_for_nonexistent_agent(self):
        """Test getting logs for agent that doesn't exist."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            logger.log_info("agent_1", "message_1")

            nonexistent_logs = logger.get_logs_for_agent("nonexistent_agent")

            assert len(nonexistent_logs) == 0

    def test_get_active_agents(self):
        """Test getting list of active agents."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            logger.log_agent_start("agent_1", "activity_1")
            logger.log_agent_start("agent_2", "activity_2")

            active_agents = logger.get_active_agents()

            assert len(active_agents) == 2
            assert "agent_1" in active_agents
            assert "agent_2" in active_agents

    def test_clear_logs(self):
        """Test clearing all logs and active agents."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            logger.log_info("agent_1", "message_1")
            logger.log_agent_start("agent_2", "activity_2")

            assert len(logger.log_entries) > 0
            assert len(logger.active_agents) > 0

            logger.clear_logs()

            assert len(logger.log_entries) == 0
            assert len(logger.active_agents) == 0

    def test_get_thread_id(self):
        """Test getting current thread ID."""
        with patch("iac_agents.logging_system.Path.mkdir"):
            logger = AgentLogger()

            thread_id = logger.get_thread_id()

            assert isinstance(thread_id, int)
            assert thread_id > 0
