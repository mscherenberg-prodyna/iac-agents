"""Real-time logging system for agent activities."""

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


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
        self.log_entries: List[AgentLogEntry] = []
        self.active_agents: Dict[str, datetime] = {}

    def setup_console_logging(self):
        """Setup enhanced console logging with colors and formatting."""
        # Create console handler with custom formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Custom formatter with colors and emojis
        class ColoredFormatter(logging.Formatter):

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
        self.logger.setLevel(logging.INFO)

        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        self.logger.addHandler(console_handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

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
        self.logger.info(f"🤖 {agent_name} STARTING: {activity}{details_str}")

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
            f"✅ {agent_name} COMPLETED: {activity}{duration_str}{details_str}"
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
        self.logger.info(f"💬 USER UPDATE: {message}")

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
        self.logger.info(f"ℹ️  {agent_name}: {message}")

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
        self.logger.warning(f"⚠️  {agent_name}: {message}")

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
        self.logger.error(f"❌ {agent_name}: {message}")

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


# Global logger instance
agent_logger = AgentLogger()


def log_agent_start(agent_name: str, activity: str, details: Dict[str, Any] = None):
    """Convenience function for logging agent start."""
    agent_logger.log_agent_start(agent_name, activity, details)


def log_agent_complete(agent_name: str, activity: str, details: Dict[str, Any] = None):
    """Convenience function for logging agent completion."""
    agent_logger.log_agent_complete(agent_name, activity, details)


def log_user_update(message: str, details: Dict[str, Any] = None):
    """Convenience function for logging user updates."""
    agent_logger.log_user_update(message, details)


def log_info(agent_name: str, message: str, details: Dict[str, Any] = None):
    """Convenience function for logging info."""
    agent_logger.log_info(agent_name, message, details)


def log_warning(agent_name: str, message: str, details: Dict[str, Any] = None):
    """Convenience function for logging warnings."""
    agent_logger.log_warning(agent_name, message, details)


def log_error(agent_name: str, message: str, details: Dict[str, Any] = None):
    """Convenience function for logging errors."""
    agent_logger.log_error(agent_name, message, details)
