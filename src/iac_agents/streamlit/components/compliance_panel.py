"""Compliance settings panel component for the Streamlit interface."""

import os
import time
from typing import Dict

import streamlit as st

from ...config.settings import config
from ...logging_system import agent_logger


def render_compliance_settings():
    """Render compliance settings panel."""
    st.markdown("### ⚖️ Compliance Settings")

    # Initialize compliance settings in session state
    if "compliance_settings" not in st.session_state:
        st.session_state.compliance_settings = {
            "enforce_compliance": False,
            "selected_frameworks": [],
        }

    # Compliance enforcement toggle
    enforce_compliance = st.checkbox(
        "🔒 Enforce Compliance Validation",
        value=st.session_state.compliance_settings["enforce_compliance"],
        help="When enabled, templates must meet selected compliance frameworks before deployment recommendation",
    )
    st.session_state.compliance_settings["enforce_compliance"] = enforce_compliance

    # Framework selection (only shown when compliance is enforced)
    if enforce_compliance:
        st.markdown("**Select Compliance Frameworks:**")

        frameworks = config.compliance.available_frameworks
        selected_frameworks = []

        for framework, description in frameworks.items():
            if st.checkbox(framework, help=description, key=f"compliance_{framework}"):
                selected_frameworks.append(framework)

        st.session_state.compliance_settings["selected_frameworks"] = (
            selected_frameworks
        )

        if selected_frameworks:
            st.success(f"✅ {len(selected_frameworks)} frameworks selected")
        else:
            st.warning("⚠️ Select at least one framework")
    else:
        st.info(
            "💡 Compliance validation disabled - templates will be generated with basic security practices"
        )
        st.session_state.compliance_settings["selected_frameworks"] = []


def render_system_metrics():
    """Render system metrics panel."""
    st.markdown("### 📈 System Metrics")

    try:
        total_messages = (
            len(st.session_state.messages) - 1 if "messages" in st.session_state else 0
        )

        active_agents_count = 0
        try:
            active_agents_count = len(agent_logger.get_active_agents())
        except Exception:
            pass

        # Display metrics
        st.markdown(f"**Total Messages:** {total_messages}")
        st.markdown(f"**Active Agents:** {active_agents_count}")
        st.markdown(f"**Session Duration:** {_get_session_duration()}")

        # Additional metrics
        if "compliance_settings" in st.session_state:
            compliance_enabled = st.session_state.compliance_settings[
                "enforce_compliance"
            ]
            frameworks_count = len(
                st.session_state.compliance_settings["selected_frameworks"]
            )
            st.markdown(
                f"**Compliance Enabled:** {'Yes' if compliance_enabled else 'No'}"
            )
            if compliance_enabled:
                st.markdown(f"**Selected Frameworks:** {frameworks_count}")

    except Exception as e:
        st.error(f"Error loading metrics: {e}")


def _get_session_duration():
    """Get session duration for metrics."""
    if "session_start_time" not in st.session_state:
        st.session_state.session_start_time = time.time()

    duration = time.time() - st.session_state.session_start_time
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    return f"{minutes}m {seconds}s"


def get_compliance_settings() -> Dict[str, any]:
    """Get current compliance settings from session state."""
    return st.session_state.get(
        "compliance_settings",
        {
            "enforce_compliance": False,
            "selected_frameworks": [],
        },
    )


def set_compliance_settings(settings: Dict[str, any]):
    """Set compliance settings in session state."""
    st.session_state.compliance_settings = settings


def render_deployment_config():
    """Render deployment configuration panel."""
    st.markdown("### 🚀 Deployment Configuration")

    # Initialize deployment settings in session state
    if "deployment_config" not in st.session_state:
        st.session_state.deployment_config = {
            "approval_required": True,
        }

    # Approval requirement
    approval_required = st.checkbox(
        "Require Manual Approval",
        value=st.session_state.deployment_config["approval_required"],
        help="When enabled, all deployments require manual approval before execution",
    )
    st.session_state.deployment_config["approval_required"] = approval_required

    # Status indicators
    if not approval_required:
        st.warning("⚠️ Auto-deployment without approval enabled")
    else:
        st.success("🛡️ Manual deployment mode (recommended)")


def _check_terraform_credentials() -> bool:
    """Check if required environment variables for Terraform Consultant are available."""
    required_vars = ["AZURE_PROJECT_ENDPOINT", "BING_CONNECTION"]

    return all(os.getenv(var) for var in required_vars)


def get_deployment_config() -> Dict[str, any]:
    """Get current deployment configuration from session state."""
    return st.session_state.get(
        "deployment_config",
        {
            "approval_required": True,
        },
    )
