"""Log categorization utilities for the log viewer."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple


class LogCategory(Enum):
    """Categories for log entries."""

    SYSTEM = "system"
    AGENT = "agent"
    TOOL = "tool"


@dataclass
class CategorizedLogs:
    """Container for categorized log lines."""

    system_logs: List[str]
    agent_logs: List[str]
    tool_logs: List[str]

    @property
    def total_lines(self) -> int:
        """Get total number of log lines across all categories."""
        return len(self.system_logs) + len(self.agent_logs) + len(self.tool_logs)


def categorize_log_line(line: str) -> LogCategory:
    """
    Categorize a single log line based on its content.

    System Logs: Info logs with "STARTING:", "RESPONSE:", "COMPLETED:" or any warning logs
    Tool Logs: Info logs with "Tool Result:" or "Calling tool:"
    Agent Logs: All other info logs
    """
    line_stripped = line.strip()

    # Check if it's a warning log (goes to System)
    if "[WARNING]" in line or "⚠️" in line:
        return LogCategory.SYSTEM

    # Check if it's an info log
    if "[INFO]" in line or "ℹ️" in line:
        # System logs - specific patterns
        system_patterns = ["STARTING:", "RESPONSE:", "COMPLETED:"]
        if any(pattern in line_stripped for pattern in system_patterns):
            return LogCategory.SYSTEM

        # Tool logs - specific patterns
        tool_patterns = ["Tool Result:", "Calling tool:"]
        if any(pattern in line_stripped for pattern in tool_patterns):
            return LogCategory.TOOL

        # All other info logs go to Agent
        return LogCategory.AGENT

    # Default to System for other log types (ERROR, DEBUG, etc.)
    return LogCategory.SYSTEM


def categorize_log_lines(lines: List[str]) -> CategorizedLogs:
    """
    Categorize a list of log lines into system, agent, and tool logs.

    Args:
        lines: List of log lines to categorize

    Returns:
        CategorizedLogs object with lines sorted into appropriate categories
    """
    system_logs = []
    agent_logs = []
    tool_logs = []

    for line in lines:
        category = categorize_log_line(line)

        if category == LogCategory.SYSTEM:
            system_logs.append(line)
        elif category == LogCategory.AGENT:
            agent_logs.append(line)
        elif category == LogCategory.TOOL:
            tool_logs.append(line)

    return CategorizedLogs(
        system_logs=system_logs, agent_logs=agent_logs, tool_logs=tool_logs
    )


def apply_max_lines_per_category(
    categorized_logs: CategorizedLogs, max_lines_per_category: int
) -> CategorizedLogs:
    """
    Apply maximum line limits to each category.

    Args:
        categorized_logs: The categorized logs to limit
        max_lines_per_category: Maximum lines to keep per category

    Returns:
        New CategorizedLogs object with limited lines per category
    """
    return CategorizedLogs(
        system_logs=(
            categorized_logs.system_logs[-max_lines_per_category:]
            if len(categorized_logs.system_logs) > max_lines_per_category
            else categorized_logs.system_logs
        ),
        agent_logs=(
            categorized_logs.agent_logs[-max_lines_per_category:]
            if len(categorized_logs.agent_logs) > max_lines_per_category
            else categorized_logs.agent_logs
        ),
        tool_logs=(
            categorized_logs.tool_logs[-max_lines_per_category:]
            if len(categorized_logs.tool_logs) > max_lines_per_category
            else categorized_logs.tool_logs
        ),
    )


def get_category_stats(categorized_logs: CategorizedLogs) -> Tuple[int, int, int]:
    """
    Get statistics for each category.

    Returns:
        Tuple of (system_count, agent_count, tool_count)
    """
    return (
        len(categorized_logs.system_logs),
        len(categorized_logs.agent_logs),
        len(categorized_logs.tool_logs),
    )
