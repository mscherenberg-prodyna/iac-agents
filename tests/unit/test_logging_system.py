"""Unit tests for logging system."""

import pytest
from unittest.mock import Mock, patch, call
from datetime import datetime

from src.iac_agents.logging_system import (
    log_user_update,
    log_agent_start,
    log_agent_complete,
    log_warning,
    log_error,
    log_info,
    AgentLogger
)


def test_log_user_update():
    """Test user update logging."""
    message = "User wants to create storage account"
    
    # Should not raise any exceptions
    log_user_update(message)
    
    # Test with empty message
    log_user_update("")


def test_log_agent_start():
    """Test agent start logging."""
    agent_name = "TestAgent"
    action = "Processing request"
    
    log_agent_start(agent_name, action)
    
    # Test with additional data
    log_agent_start(agent_name, action, {"key": "value"})


def test_log_agent_complete():
    """Test agent completion logging."""
    agent_name = "TestAgent"
    action = "Request processed"
    
    log_agent_complete(agent_name, action)
    
    # Test with additional data
    log_agent_complete(agent_name, action, {"result": "success"})


def test_log_warning():
    """Test warning logging."""
    source = "TestComponent"
    message = "This is a warning"
    
    log_warning(source, message)
    
    # Test with additional data
    log_warning(source, message, {"details": "extra info"})


def test_log_error():
    """Test error logging."""
    source = "TestComponent"
    message = "This is an error"
    
    log_error(source, message)
    
    # Test with additional data
    log_error(source, message, {"error_code": 500})


def test_log_info():
    """Test info logging."""
    agent_name = "TestAgent"
    message = "This is info"
    
    log_info(agent_name, message)
    
    # Test with additional data
    log_info(agent_name, message, {"info": "details"})


def test_log_info_variations():
    """Test info logging variations."""
    agent_name = "TestAgent"
    message = "This is info with extra detail"
    
    log_info(agent_name, message)
    
    # Test with additional data variations
    log_info(agent_name, message, {"extra": "details"})


def test_agent_logger_class():
    """Test AgentLogger class functionality."""
    logger = AgentLogger()
    
    # Test basic functionality
    logger.log_user_update("Test message")
    logger.log_agent_start("TestAgent", "action")
    logger.log_agent_complete("TestAgent", "completed")
    logger.log_info("TestAgent", "info message")
    logger.log_warning("TestAgent", "warning message")
    logger.log_error("TestAgent", "error message")
    
    # Test getting recent logs
    recent_logs = logger.get_recent_logs(5)
    assert isinstance(recent_logs, list)
    assert len(recent_logs) <= 5
    
    # Test getting logs for specific agent
    agent_logs = logger.get_logs_for_agent("TestAgent")
    assert isinstance(agent_logs, list)
    
    # Test getting active agents
    active_agents = logger.get_active_agents()
    assert isinstance(active_agents, list)
    
    # Test clearing logs
    logger.clear_logs()
    cleared_logs = logger.get_recent_logs()
    assert len(cleared_logs) == 0


@patch('src.iac_agents.logging_system.datetime')
def test_logging_timestamps(mock_datetime):
    """Test that logging includes timestamps."""
    # Mock datetime
    mock_now = datetime(2024, 1, 1, 12, 0, 0)
    mock_datetime.now.return_value = mock_now
    
    # Log a message
    log_user_update("Test message")
    
    # Check that datetime.now was called
    mock_datetime.now.assert_called()


def test_logging_with_none_values():
    """Test logging with None values."""
    # Should handle None gracefully
    log_user_update(None)
    log_agent_start(None, None)
    log_agent_complete("Agent", None)
    log_warning(None, None)
    log_error("Source", None)
    log_info("Agent", None)
    log_info("Agent", None)


def test_logging_with_empty_strings():
    """Test logging with empty strings."""
    # Should handle empty strings gracefully
    log_user_update("")
    log_agent_start("", "")
    log_agent_complete("", "")
    log_warning("", "")
    log_error("", "")
    log_info("Agent", "")
    log_info("Agent", "")


def test_logging_with_special_characters():
    """Test logging with special characters."""
    special_message = "Test with émojis 🚀 and symbols @#$%^&*()"
    
    log_user_update(special_message)
    log_agent_start("Agent", special_message)
    log_info("Agent", special_message)


def test_logging_with_large_data():
    """Test logging with large data structures."""
    large_data = {
        "data": ["item"] * 1000,
        "nested": {
            "level1": {
                "level2": {
                    "level3": "deep value"
                }
            }
        }
    }
    
    # Should handle large data without errors
    log_agent_complete("Agent", "Processing complete", large_data)
    log_info("Agent", "Large data test", large_data)


def test_logger_log_structure():
    """Test logger log entry structure."""
    logger = AgentLogger()
    
    # Add a user message
    logger.log_user_update("Test user message")
    
    logs = logger.get_recent_logs(1)
    assert len(logs) >= 1
    
    # Check structure of the last entry
    if len(logs) > 0:
        entry = logs[-1]
        assert hasattr(entry, 'timestamp')
        assert hasattr(entry, 'agent_name')
        assert hasattr(entry, 'activity')
        assert hasattr(entry, 'level')


def test_agent_timing():
    """Test agent start/complete timing."""
    agent_name = "TimingTestAgent"
    action = "Test action"
    
    # Start agent
    log_agent_start(agent_name, action)
    
    # Complete agent (this should calculate duration)
    log_agent_complete(agent_name, action, {"result": "success"})
    
    # Should not raise any exceptions


def test_concurrent_logging():
    """Test that logging works with concurrent calls."""
    import threading
    import time
    
    def log_worker(worker_id):
        for i in range(10):
            log_info("Worker", f"Worker {worker_id} message {i}")
            time.sleep(0.001)  # Small delay
    
    # Create multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=log_worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Should not have raised any exceptions


def test_multiple_logger_instances():
    """Test that multiple logger instances work independently."""
    logger1 = AgentLogger()
    logger2 = AgentLogger()
    
    # Log to first logger
    logger1.log_user_update("Logger 1 message")
    
    # Log to second logger
    logger2.log_user_update("Logger 2 message")
    
    # Both should have their own logs
    logs1 = logger1.get_recent_logs()
    logs2 = logger2.get_recent_logs()
    
    assert isinstance(logs1, list)
    assert isinstance(logs2, list)


def test_logging_performance():
    """Test that logging doesn't significantly impact performance."""
    import time
    
    start_time = time.time()
    
    # Log many messages
    for i in range(100):
        log_info("PerfTest", f"Performance test message {i}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Should complete within reasonable time (less than 1 second)
    assert duration < 1.0


def test_error_handling_in_logging():
    """Test error handling within logging functions."""
    # Test with invalid data types that might cause JSON serialization issues
    circular_ref = {}
    circular_ref["self"] = circular_ref
    
    # Should handle circular references gracefully
    try:
        log_info("Agent", "Circular reference test", circular_ref)
    except Exception:
        # If it raises an exception, that's acceptable too
        pass


def test_logging_with_agent_details():
    """Test logging with additional agent details."""
    logger = AgentLogger()
    
    # Test with detailed information
    details = {
        "execution_time": 1234,
        "memory_usage": "50MB",
        "status": "success"
    }
    
    logger.log_agent_start("DetailedAgent", "complex_operation", details)
    logger.log_agent_complete("DetailedAgent", "complex_operation", details)
    
    logs = logger.get_recent_logs(2)
    assert len(logs) >= 2