"""Terraform template viewer component for the UI."""

from typing import Optional

import streamlit as st


def render_terraform_template_viewer():
    """Render the Terraform template viewer in the sidebar."""
    # Check if there's a Terraform template in the workflow state
    workflow_result = st.session_state.get("workflow_result", {})
    terraform_template = workflow_result.get("final_template")

    if terraform_template:
        if st.button(
            "📄 View Terraform Template",
            help="View the generated Terraform template",
            use_container_width=True,
        ):
            st.session_state.show_terraform_modal = True

    # Show modal if requested
    if st.session_state.get("show_terraform_modal", False):
        show_terraform_template_modal(terraform_template)


def show_terraform_template_modal(template_content: Optional[str]):
    """Display Terraform template in a modal dialog."""
    if not template_content:
        st.error("No Terraform template available")
        return

    # Create modal using expander (Streamlit doesn't have true modals)
    with st.expander("🏗️ Generated Terraform Template", expanded=True):
        col1, col2 = st.columns([6, 1])

        with col1:
            st.subheader("Infrastructure as Code Template")

        with col2:
            if st.button("❌", help="Close", key="close_terraform_modal"):
                st.session_state.show_terraform_modal = False
                st.rerun()

        # Display template with syntax highlighting
        st.code(template_content, language="hcl", line_numbers=True)

        # Add template analysis
        st.subheader("Template Analysis")
        analyze_terraform_template(template_content)

        # Download button
        st.download_button(
            label="💾 Download Template",
            data=template_content,
            file_name="main.tf",
            mime="text/plain",
            use_container_width=True,
        )


def analyze_terraform_template(template_content: str):
    """Analyze and display information about the Terraform template."""
    from iac_agents.agents.terraform_utils import TerraformVariableManager

    try:
        # Extract and display variables
        variables = TerraformVariableManager.extract_variables_from_template(
            template_content
        )

        if variables:
            st.write("**Variables:**")
            for var_name, var_info in variables.items():
                status = "✅ Has default" if var_info["has_default"] else "⚠️ Required"
                validation = " (validated)" if var_info["has_validation"] else ""

                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 3])
                    with col1:
                        st.write(f"`{var_name}`")
                    with col2:
                        st.write(status)
                    with col3:
                        description = var_info.get("description", "No description")
                        st.write(f"{description}{validation}")

        # Validate template
        is_valid, issues = TerraformVariableManager.validate_template_variables(
            template_content
        )

        st.write("**Validation:**")
        if is_valid:
            st.success("✅ Template is valid and ready for deployment")
        else:
            st.warning("⚠️ Template has issues:")
            for issue in issues:
                st.write(f"- {issue}")

        # Count resources
        resource_count = len(
            [
                line
                for line in template_content.split("\n")
                if line.strip().startswith("resource ")
            ]
        )
        data_count = len(
            [
                line
                for line in template_content.split("\n")
                if line.strip().startswith("data ")
            ]
        )

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Resources", resource_count)
        with col2:
            st.metric("Data Sources", data_count)

    except Exception as e:
        st.error(f"Error analyzing template: {e}")
