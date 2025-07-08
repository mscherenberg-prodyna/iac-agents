"""Tests for AgentLogEntry dataclass."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from iac_agents.logging_system import AgentLogEntry, LogLevel


class TestAgentLogEntry:
    """Test suite for AgentLogEntry dataclass."""

    def test_log_entry_creation(self):
        """Test AgentLogEntry creation with all fields."""
        timestamp = datetime.now()
        details = {"key": "value"}

        entry = AgentLogEntry(
            timestamp=timestamp,
            agent_name="test_agent",
            activity="test_activity",
            level=LogLevel.INFO,
            details=details,
            duration_ms=100,
        )

        assert entry.timestamp == timestamp
        assert entry.agent_name == "test_agent"
        assert entry.activity == "test_activity"
        assert entry.level == LogLevel.INFO
        assert entry.details == details
        assert entry.duration_ms == 100

    def test_log_entry_default_duration(self):
        """Test AgentLogEntry with default duration."""
        entry = AgentLogEntry(
            timestamp=datetime.now(),
            agent_name="test_agent",
            activity="test_activity",
            level=LogLevel.INFO,
            details={},
        )

        assert entry.duration_ms == 0

    def test_log_entry_with_different_log_levels(self):
        """Test AgentLogEntry with different log levels."""
        timestamp = datetime.now()

        entries = []
        for level in LogLevel:
            entry = AgentLogEntry(
                timestamp=timestamp,
                agent_name="test_agent",
                activity=f"activity_{level.value}",
                level=level,
                details={},
            )
            entries.append(entry)

        assert len(entries) == 7
        assert all(isinstance(entry.level, LogLevel) for entry in entries)

    def test_log_entry_with_complex_details(self):
        """Test AgentLogEntry with complex details dictionary."""
        complex_details = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "string": "test",
            "number": 42,
            "boolean": True,
        }

        entry = AgentLogEntry(
            timestamp=datetime.now(),
            agent_name="test_agent",
            activity="complex_test",
            level=LogLevel.INFO,
            details=complex_details,
        )

        assert entry.details == complex_details
        assert entry.details["nested"]["key"] == "value"
        assert entry.details["list"] == [1, 2, 3]

    def test_log_entry_equality(self):
        """Test AgentLogEntry equality comparison."""
        timestamp = datetime.now()
        details = {"key": "value"}

        entry1 = AgentLogEntry(
            timestamp=timestamp,
            agent_name="test_agent",
            activity="test_activity",
            level=LogLevel.INFO,
            details=details,
        )

        entry2 = AgentLogEntry(
            timestamp=timestamp,
            agent_name="test_agent",
            activity="test_activity",
            level=LogLevel.INFO,
            details=details,
        )

        assert entry1 == entry2

    def test_log_entry_string_representation(self):
        """Test AgentLogEntry string representation."""
        entry = AgentLogEntry(
            timestamp=datetime.now(),
            agent_name="test_agent",
            activity="test_activity",
            level=LogLevel.INFO,
            details={"key": "value"},
        )

        string_repr = str(entry)

        assert "test_agent" in string_repr
        assert "test_activity" in string_repr
        assert "INFO" in string_repr
