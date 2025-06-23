"""Sidebar components for the Streamlit interface."""

from typing import Any, Dict, List

import streamlit as st

from ...config.settings import config
from ...templates.ui_loader import ui_loader


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


def display_metrics():
    """Display system metrics in sidebar."""
    st.markdown("### 📈 System Metrics")

    # Mock metrics - in a real system, these would come from monitoring
    metrics = [
        ("API Calls", "142"),
        ("Success Rate", "98.5%"),
        ("Avg Response", "2.3s"),
        ("Active Sessions", "5"),
    ]

    for label, value in metrics:
        st.markdown(
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
