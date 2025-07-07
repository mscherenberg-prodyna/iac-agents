"""Compliance settings panel component for the Streamlit interface."""

from typing import Dict

import streamlit as st

# pylint: disable=E0402
from ...config.settings import config


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
            # Check if this framework should be pre-selected
            default_selected = framework in st.session_state.compliance_settings.get(
                "selected_frameworks", []
            )
            checkbox_key = f"compliance_{framework}"

            # Use the session state value if it exists, otherwise use the default
            checkbox_value = st.session_state.get(checkbox_key, default_selected)

            if st.checkbox(
                framework, help=description, key=checkbox_key, value=checkbox_value
            ):
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


def get_deployment_config() -> Dict[str, any]:
    """Get current deployment configuration from session state."""
    return st.session_state.get(
        "deployment_config",
        {
            "approval_required": True,
        },
    )
