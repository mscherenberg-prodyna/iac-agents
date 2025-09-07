"""Real-time logging system for agent activities."""

import logging
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st


class LogLevel(Enum):
    """Log levels for agent activities."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    AGENT_START = "AGENT_START"
    AGENT_COMPLETE = "AGENT_COMPLETE"
    USER_UPDATE = "USER_UPDATE"


@dataclass
class AgentLogEntry:
    """Log entry for agent activities."""

    timestamp: datetime
    agent_name: str
    activity: str
    level: LogLevel
    details: Dict[str, Any]
    duration_ms: int = 0


class AgentLogger:
    """Centralized logging system for all agent activities."""

    def __init__(self):
        self.setup_console_logging()
        self.setup_file_logging()
        self.log_entries: List[AgentLogEntry] = []
        self.active_agents: Dict[str, datetime] = {}

    def setup_console_logging(self):
        """Setup enhanced console logging with colors and formatting."""
        # Create console handler with custom formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Custom formatter with colors and emojis
        class ColoredFormatter(logging.Formatter):
            """Custom formatter with colors and emojis for enhanced logging."""

            COLORS = {
                "DEBUG": "\033[36m",  # Cyan
                "INFO": "\033[32m",  # Green
                "WARNING": "\033[33m",  # Yellow
                "ERROR": "\033[31m",  # Red
                "AGENT_START": "\033[35m",  # Magenta
                "AGENT_COMPLETE": "\033[34m",  # Blue
                "USER_UPDATE": "\033[96m",  # Light Cyan
                "ENDC": "\033[0m",  # End color
            }

            EMOJIS = {
                "DEBUG": "🔍",
                "INFO": "ℹ️",
                "WARNING": "⚠️",
                "ERROR": "❌",
                "AGENT_START": "🚀",
                "AGENT_COMPLETE": "✅",
                "USER_UPDATE": "💬",
            }

            def format(self, record):
                level = record.levelname
                color = self.COLORS.get(level, "")
                emoji = self.EMOJIS.get(level, "•")

                timestamp = datetime.now().strftime("%H:%M:%S")

                formatted = f"{color}{emoji} [{timestamp}] {record.getMessage()}{self.COLORS['ENDC']}"
                return formatted

        console_handler.setFormatter(ColoredFormatter())

        # Get or create logger
        self.logger = logging.getLogger("agent_system")
        self.logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels

        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Store console handler reference
        self.console_handler = console_handler

        # Prevent propagation to root logger
        self.logger.propagate = False

    def setup_file_logging(self):
        """Setup file-based logging indexed by thread ID."""
        # Get current thread ID
        thread_id = threading.current_thread().ident

        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Create log file path indexed by thread ID
        log_file_path = log_dir / f"agent_workflow_{thread_id}.log"

        # Create file handler
        file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # Capture all levels in file

        # File formatter (without colors, more detailed)
        class FileFormatter(logging.Formatter):
            """Detailed formatter for file logging without ANSI codes."""

            def format(self, record):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                thread_id = threading.current_thread().ident
                level = record.levelname

                formatted = f"[{timestamp}] [Thread-{thread_id}] [{level}] {record.getMessage()}"
                return formatted

        file_handler.setFormatter(FileFormatter())

        # Add both console and file handlers to logger
        self.logger.addHandler(self.console_handler)
        self.logger.addHandler(file_handler)

        # Store file handler reference for potential cleanup
        self.file_handler = file_handler
        self.log_file_path = log_file_path

        # Log the initialization
        self.logger.info("🗂️ LOGGING: File logging initialized - %s", log_file_path)

    def log_agent_start(
        self, agent_name: str, activity: str, details: Dict[str, Any] = None
    ):
        """Log when an agent starts an activity."""
        self.active_agents[agent_name] = datetime.now()

        entry = AgentLogEntry(
            timestamp=datetime.now(),
            agent_name=agent_name,
            activity=activity,
            level=LogLevel.AGENT_START,
            details=details or {},
        )

        self.log_entries.append(entry)

        details_str = f" | {details}" if details else ""
        self.logger.info("🤖 %s STARTING: %s%s", agent_name, activity, details_str)

    def log_agent_complete(
        self, agent_name: str, activity: str, details: Dict[str, Any] = None
    ):
        """Log when an agent completes an activity."""
        start_time = self.active_agents.get(agent_name)
        duration_ms = 0

        if start_time:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            del self.active_agents[agent_name]

        entry = AgentLogEntry(
            timestamp=datetime.now(),
            agent_name=agent_name,
            activity=activity,
            level=LogLevel.AGENT_COMPLETE,
            details=details or {},
            duration_ms=duration_ms,
        )

        self.log_entries.append(entry)

        duration_str = f" ({duration_ms}ms)" if duration_ms > 0 else ""
        details_str = f" | {details}" if details else ""
        self.logger.info(
            "✅ %s COMPLETED: %s%s%s", agent_name, activity, duration_str, details_str
        )

    def log_user_update(self, message: str, details: Dict[str, Any] = None):
        """Log updates meant for the user."""
        entry = AgentLogEntry(
            timestamp=datetime.now(),
            agent_name="SYSTEM",
            activity=message,
            level=LogLevel.USER_UPDATE,
            details=details or {},
        )

        self.log_entries.append(entry)
        self.logger.info("💬 USER UPDATE: %s", message)

    def log_info(self, agent_name: str, message: str, details: Dict[str, Any] = None):
        """Log general information."""
        entry = AgentLogEntry(
            timestamp=datetime.now(),
            agent_name=agent_name,
            activity=message,
            level=LogLevel.INFO,
            details=details or {},
        )

        self.log_entries.append(entry)
        self.logger.info("ℹ️  %s: %s", agent_name, message)

    def log_warning(
        self, agent_name: str, message: str, details: Dict[str, Any] = None
    ):
        """Log warnings."""
        entry = AgentLogEntry(
            timestamp=datetime.now(),
            agent_name=agent_name,
            activity=message,
            level=LogLevel.WARNING,
            details=details or {},
        )

        self.log_entries.append(entry)
        self.logger.warning("⚠️  %s: %s", agent_name, message)

    def log_error(self, agent_name: str, message: str, details: Dict[str, Any] = None):
        """Log errors."""
        entry = AgentLogEntry(
            timestamp=datetime.now(),
            agent_name=agent_name,
            activity=message,
            level=LogLevel.ERROR,
            details=details or {},
        )

        self.log_entries.append(entry)
        self.logger.error("❌ %s: %s", agent_name, message)

    def get_recent_logs(self, limit: int = 10) -> List[AgentLogEntry]:
        """Get recent log entries."""
        return self.log_entries[-limit:]

    def get_logs_for_agent(
        self, agent_name: str, limit: int = 10
    ) -> List[AgentLogEntry]:
        """Get recent logs for a specific agent."""
        agent_logs = [log for log in self.log_entries if log.agent_name == agent_name]
        return agent_logs[-limit:]

    def get_active_agents(self) -> List[str]:
        """Get list of currently active agents."""
        return list(self.active_agents.keys())

    def clear_logs(self):
        """Clear all log entries."""
        self.log_entries.clear()
        self.active_agents.clear()

    def get_log_file_path(self) -> str:
        """Get the current log file path."""
        return str(self.log_file_path) if hasattr(self, "log_file_path") else ""

    def get_thread_id(self) -> int:
        """Get the current thread ID."""
        return threading.current_thread().ident

    def close_file_handler(self):
        """Close the file handler to ensure logs are written."""
        if hasattr(self, "file_handler"):
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)


# Global logger instance
agent_logger = AgentLogger()


def log_agent_start(agent_name: str, activity: str, details: Dict[str, Any] = None):
    """Convenience function for logging agent start."""
    agent_logger.log_agent_start(agent_name, activity, details)

    # Update Streamlit session state for real-time UI updates
    try:
        if hasattr(st, "session_state") and hasattr(
            st.session_state, "workflow_active"
        ):
            st.session_state.current_agent_status = agent_name
            st.session_state.current_workflow_phase = activity
            st.session_state.workflow_status = f"{agent_name} - {activity}"
    except (ImportError, AttributeError):
        # Streamlit not available or session_state not initialized
        pass


def log_agent_complete(agent_name: str, activity: str, details: Dict[str, Any] = None):
    """Convenience function for logging agent completion."""
    agent_logger.log_agent_complete(agent_name, activity, details)


def log_user_update(message: str, details: Dict[str, Any] = None):
    """Convenience function for logging user updates."""
    agent_logger.log_user_update(message, details)


def log_info(agent_name: str, message: str, details: Dict[str, Any] = None):
    """Convenience function for logging info."""
    agent_logger.log_info(agent_name, message.replace("\n", " "), details)


def log_warning(agent_name: str, message: str, details: Dict[str, Any] = None):
    """Convenience function for logging warnings."""
    agent_logger.log_warning(agent_name, message, details)


def log_error(agent_name: str, message: str, details: Dict[str, Any] = None):
    """Convenience function for logging errors."""
    agent_logger.log_error(agent_name, message, details)


def log_agent_response(agent_name: str, response: str, truncate_at: int = 200):
    """Log agent response content (truncated for readability)."""
    if response:
        truncated = (
            response[:truncate_at] + "..." if len(response) > truncate_at else response
        )
        truncated = truncated.replace("\n", " ")  # Single line for logs
        agent_logger.log_info(agent_name, f"RESPONSE: {truncated}")


def get_log_file_path() -> str:
    """Get the current log file path."""
    return agent_logger.get_log_file_path()


def get_thread_id() -> int:
    """Get the current thread ID."""
    return agent_logger.get_thread_id()


def close_file_handler():
    """Close the file handler to ensure logs are written."""
    agent_logger.close_file_handler()
