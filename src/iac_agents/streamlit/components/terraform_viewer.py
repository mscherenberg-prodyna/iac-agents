"""Terraform template download component for the UI."""

import streamlit as st

from iac_agents.logging_system import get_thread_id


def render_terraform_template_viewer():
    """Render the Terraform template download button in the sidebar."""
    # Check if there's a Terraform template in the workflow state
    workflow_result = st.session_state.get("workflow_result", {})
    terraform_template = workflow_result.get("final_template")

    if terraform_template:
        st.subheader("📋 Generated Terraform")

        thread_id = get_thread_id()
        # Display thread ID
        st.write(f"**Thread ID:** `{thread_id}`")

        st.download_button(
            label="📥 Download Terraform Template",
            data=terraform_template,
            file_name="main.tf",
            mime="text/plain",
            help="Download the generated Terraform template",
            use_container_width=True,
        )
