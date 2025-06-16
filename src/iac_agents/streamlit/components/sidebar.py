"""Sidebar components for the Streamlit interface."""

from typing import Any, Dict, List

import streamlit as st

from ...agents import SupervisorAgent
from ...config.settings import config
from ...logging_system import agent_logger
from ...templates.ui_loader import ui_loader


def display_agent_status():
    """Display real-time agent status in sidebar."""
    st.sidebar.markdown(
        ui_loader.format_sidebar_section("🤖 Agent Status", ""),
        unsafe_allow_html=True,
    )

    # Get active agents from logger
    try:
        active_agents = agent_logger.get_active_agents()
        recent_logs = agent_logger.get_recent_logs(10)
    except Exception:
        active_agents = []
        recent_logs = []

    # Agent status indicators
    agents = [
        ("Supervisor Agent", "🎯", "supervisor"),
        ("Terraform Agent", "🏗️", "terraform"),
        ("Research Agent", "🔍", "research"),
        ("Compliance Agent", "⚖️", "compliance"),
        ("Cost Agent", "💰", "cost"),
    ]

    for agent_name, emoji, agent_key in agents:
        is_active = any(agent_key.lower() in active.lower() for active in active_agents)

        if is_active:
            status_class = "working"
            status_text = "WORKING"
            subtext = "Processing your request..."
        else:
            status_class = "idle"
            status_text = "READY"
            subtext = "Standing by for tasks"

        st.sidebar.markdown(
            ui_loader.format_agent_status(
                emoji, agent_name, status_class, status_text, subtext
            ),
            unsafe_allow_html=True,
        )

    # Recent activity
    _display_recent_activity(recent_logs)


def _display_recent_activity(recent_logs: List[Any]):
    """Display recent activity logs in sidebar."""
    st.sidebar.markdown("### 📊 Recent Activity")

    if recent_logs:
        with st.sidebar.container():
            for log in recent_logs[-config.ui.activity_log_entries :]:
                timestamp = log.timestamp.strftime("%H:%M:%S")
                activity_snippet = log.activity[:50] + (
                    "..." if len(log.activity) > 50 else ""
                )

                # Use emoji for different log levels
                level_emoji = "ℹ️"
                if hasattr(log, "level"):
                    level_str = (
                        str(log.level).rsplit(".", maxsplit=1)[-1]
                        if hasattr(log, "level")
                        else "INFO"
                    )
                    level_emoji = {
                        "AGENT_START": "🚀",
                        "AGENT_COMPLETE": "✅",
                        "USER_UPDATE": "💬",
                        "INFO": "ℹ️",
                        "WARNING": "⚠️",
                        "ERROR": "❌",
                    }.get(level_str, "ℹ️")

                st.sidebar.markdown(
                    ui_loader.format_activity_entry(
                        timestamp, log.agent_name, f"{level_emoji} {activity_snippet}"
                    ),
                    unsafe_allow_html=True,
                )
    else:
        st.sidebar.info("No recent activity to display")


def display_workflow_progress(supervisor_agent: SupervisorAgent):
    """Display current workflow progress in sidebar."""
    try:
        workflow_status = supervisor_agent.get_workflow_status()
    except Exception:
        # Handle errors gracefully - supervisor might not be ready
        return
    
    if workflow_status and workflow_status.get("status") != "idle":
        st.sidebar.markdown("### 🔄 Workflow Progress")

        # Progress bar
        completed_stages = workflow_status.get("completed_stages", [])
        current_stage = workflow_status.get("current_stage", "")
        total_stages = len(completed_stages) + (1 if current_stage else 0)
        progress = len(completed_stages) / max(total_stages, 1)

        st.sidebar.progress(progress)
        if current_stage:
            st.sidebar.markdown(f"**Current Stage:** {current_stage.replace('_', ' ').title()}")

        # Completed stages
        if completed_stages:
            st.sidebar.markdown("**Completed:**")
            for stage in completed_stages:
                st.sidebar.markdown(f"✅ {stage.replace('_', ' ').title()}")

        # Issues found
        issues_found = workflow_status.get("issues_found", [])
        if issues_found:
            st.sidebar.markdown("**Issues:**")
            for issue in issues_found[-3:]:  # Show last 3 issues
                st.sidebar.markdown(f"⚠️ {issue}")


def display_metrics():
    """Display system metrics in sidebar."""
    st.sidebar.markdown("### 📈 System Metrics")

    # Mock metrics - in a real system, these would come from monitoring
    metrics = [
        ("API Calls", "142"),
        ("Success Rate", "98.5%"),
        ("Avg Response", "2.3s"),
        ("Active Sessions", "5"),
    ]

    for label, value in metrics:
        st.sidebar.markdown(
            ui_loader.format_metric_container(label, value),
            unsafe_allow_html=True,
        )


def display_cost_estimation(cost_data: Dict[str, Any]):
    """Display cost estimation in sidebar."""
    if not cost_data:
        return

    st.sidebar.markdown("### 💰 Cost Estimation")

    if "estimated_monthly_cost" in cost_data:
        monthly_cost = cost_data["estimated_monthly_cost"]
        st.sidebar.markdown(f"**Monthly Cost:** ${monthly_cost:.2f}")

    if "resource_breakdown" in cost_data:
        st.sidebar.markdown("**Resource Breakdown:**")
        for resource, cost in cost_data["resource_breakdown"].items():
            st.sidebar.markdown(f"• {resource}: ${cost:.2f}")

    if "cost_optimization_tips" in cost_data:
        with st.sidebar.expander("💡 Cost Optimization Tips"):
            for tip in cost_data["cost_optimization_tips"]:
                st.markdown(f"• {tip}")
