"""Tests for logging convenience functions."""

from unittest.mock import Mock, patch

import pytest

from iac_agents.logging_system import (
    get_log_file_path,
    get_thread_id,
    log_agent_complete,
    log_agent_response,
    log_agent_start,
    log_error,
    log_info,
    log_user_update,
    log_warning,
)


class TestLoggingConvenienceFunctions:
    """Test suite for logging convenience functions."""

    @patch("iac_agents.logging_system.agent_logger")
    def test_log_agent_start_function(self, mock_logger):
        """Test log_agent_start convenience function."""
        log_agent_start("test_agent", "test_activity", {"key": "value"})

        mock_logger.log_agent_start.assert_called_once_with(
            "test_agent", "test_activity", {"key": "value"}
        )

    @patch("iac_agents.logging_system.agent_logger")
    def test_log_agent_complete_function(self, mock_logger):
        """Test log_agent_complete convenience function."""
        log_agent_complete("test_agent", "test_activity", {"result": "success"})

        mock_logger.log_agent_complete.assert_called_once_with(
            "test_agent", "test_activity", {"result": "success"}
        )

    @patch("iac_agents.logging_system.agent_logger")
    def test_log_user_update_function(self, mock_logger):
        """Test log_user_update convenience function."""
        log_user_update("update message", {"status": "complete"})

        mock_logger.log_user_update.assert_called_once_with(
            "update message", {"status": "complete"}
        )

    @patch("iac_agents.logging_system.agent_logger")
    def test_log_info_function(self, mock_logger):
        """Test log_info convenience function."""
        log_info("test_agent", "info message", {"data": "test"})

        mock_logger.log_info.assert_called_once_with(
            "test_agent", "info message", {"data": "test"}
        )

    @patch("iac_agents.logging_system.agent_logger")
    def test_log_warning_function(self, mock_logger):
        """Test log_warning convenience function."""
        log_warning("test_agent", "warning message", {"level": "medium"})

        mock_logger.log_warning.assert_called_once_with(
            "test_agent", "warning message", {"level": "medium"}
        )

    @patch("iac_agents.logging_system.agent_logger")
    def test_log_error_function(self, mock_logger):
        """Test log_error convenience function."""
        log_error("test_agent", "error message", {"severity": "high"})

        mock_logger.log_error.assert_called_once_with(
            "test_agent", "error message", {"severity": "high"}
        )

    @patch("iac_agents.logging_system.agent_logger")
    def test_log_agent_response_function(self, mock_logger):
        """Test log_agent_response convenience function."""
        response = "This is a test response message"

        log_agent_response("test_agent", response, truncate_at=10)

        mock_logger.log_info.assert_called_once_with(
            "test_agent", "Response: This is a ..."
        )

    @patch("iac_agents.logging_system.agent_logger")
    def test_log_agent_response_no_truncation(self, mock_logger):
        """Test log_agent_response without truncation."""
        response = "Short"

        log_agent_response("test_agent", response, truncate_at=200)

        mock_logger.log_info.assert_called_once_with("test_agent", "Response: Short")

    @patch("iac_agents.logging_system.agent_logger")
    def test_get_log_file_path_function(self, mock_logger):
        """Test get_log_file_path convenience function."""
        mock_logger.get_log_file_path.return_value = "/path/to/log.log"

        path = get_log_file_path()

        assert path == "/path/to/log.log"
        mock_logger.get_log_file_path.assert_called_once()

    @patch("iac_agents.logging_system.agent_logger")
    def test_get_thread_id_function(self, mock_logger):
        """Test get_thread_id convenience function."""
        mock_logger.get_thread_id.return_value = 12345

        thread_id = get_thread_id()

        assert thread_id == 12345
        mock_logger.get_thread_id.assert_called_once()
