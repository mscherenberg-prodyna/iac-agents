"""Categorized display components for the log viewer."""

from typing import List

import streamlit as st

from iac_agents.templates.template_loader import template_loader


def render_categorized_log_window(
    title: str,
    emoji: str,
    lines: List[str],
    color_scheme: str,
    auto_scroll: bool = True,
    container_id: str = "",
) -> None:
    """
    Render a single categorized log window.

    Args:
        title: The title of the log window
        emoji: Emoji to display with the title
        lines: List of log lines to display
        color_scheme: CSS color scheme identifier
        auto_scroll: Whether to auto-scroll to bottom
        container_id: Unique ID for the container element
    """
    st.markdown(f"**{emoji} {title}** ({len(lines)} lines)")

    if not lines:
        st.info(f"No {title.lower()} found in the current log selection.")
        return

    log_text = "".join(lines)

    if auto_scroll and log_text.strip():
        # Use template-based log container with auto-scroll and custom styling
        try:
            log_container_template = template_loader.jinja_env.get_template(
                "html/categorized_log_container.html"
            )
            log_html = log_container_template.render(
                log_content=log_text,
                color_scheme=color_scheme,
                container_id=container_id,
            )
            st.markdown(log_html, unsafe_allow_html=True)
        except Exception:
            # Fallback to regular code block if template not available
            st.code(log_text, language="text", line_numbers=False)
    else:
        # Use regular code block when not auto-scrolling
        st.code(log_text, language="text", line_numbers=False)


def render_system_logs(lines: List[str], auto_scroll: bool = True) -> None:
    """Render system logs window."""
    render_categorized_log_window(
        title="System Logs",
        emoji="🏗️",
        lines=lines,
        color_scheme="system",
        auto_scroll=auto_scroll,
        container_id="system-log-container",
    )


def render_agent_logs(lines: List[str], auto_scroll: bool = True) -> None:
    """Render agent logs window."""
    render_categorized_log_window(
        title="Agent Logs",
        emoji="🤖",
        lines=lines,
        color_scheme="agent",
        auto_scroll=auto_scroll,
        container_id="agent-log-container",
    )


def render_tool_logs(lines: List[str], auto_scroll: bool = True) -> None:
    """Render tool logs window."""
    render_categorized_log_window(
        title="Tool Logs",
        emoji="🔧",
        lines=lines,
        color_scheme="tool",
        auto_scroll=auto_scroll,
        container_id="tool-log-container",
    )


def render_category_summary(
    system_count: int, agent_count: int, tool_count: int, total_lines: int
) -> None:
    """
    Render a summary of log categories.

    Args:
        system_count: Number of system log lines
        agent_count: Number of agent log lines
        tool_count: Number of tool log lines
        total_lines: Total number of lines in the log file
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🏗️ System", system_count)

    with col2:
        st.metric("🤖 Agent", agent_count)

    with col3:
        st.metric("🔧 Tool", tool_count)

    with col4:
        displayed_total = system_count + agent_count + tool_count
        st.metric("📊 Displayed/Total", f"{displayed_total}/{total_lines}")
