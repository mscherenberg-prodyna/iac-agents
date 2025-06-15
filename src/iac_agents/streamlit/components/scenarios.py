"""Showcase scenarios component for the Streamlit interface."""

import streamlit as st

from ...templates.scenario_loader import scenario_loader


def display_showcase_scenarios():
    """Display demo scenarios in sidebar."""
    st.sidebar.markdown("### 🎬 Demo Scenarios")

    scenario_titles = scenario_loader.get_all_scenario_titles()
    selected_scenario = st.sidebar.selectbox(
        "Choose a business scenario:",
        ["Custom Request"] + scenario_titles,
        key="scenario_selector",
    )

    if selected_scenario != "Custom Request":
        scenarios = scenario_loader.get_all_scenarios()
        for scenario_key, scenario in scenarios.items():
            if scenario["title"] == selected_scenario:
                with st.sidebar.expander("📋 Scenario Details", expanded=False):
                    st.markdown(f"**Context:** {scenario['business_context']}")
                    st.markdown(f"**Estimated Cost:** {scenario['estimated_cost']}")
                    st.markdown(
                        f"**Compliance:** {', '.join(scenario['compliance_requirements'])}"
                    )

                if st.sidebar.button(
                    "🚀 Load This Scenario", key=f"load_{scenario_key}"
                ):
                    return scenario["user_request"]

    return None


def get_scenario_by_title(title: str):
    """Get a scenario by its title."""
    scenarios = scenario_loader.get_all_scenarios()
    for scenario_key, scenario in scenarios.items():
        if scenario["title"] == title:
            return scenario
    return None


def get_all_scenario_titles():
    """Get all available scenario titles."""
    return scenario_loader.get_all_scenario_titles()


def display_scenario_quick_actions():
    """Display quick action buttons for common scenarios."""
    st.sidebar.markdown("### ⚡ Quick Start")

    quick_scenarios = [
        ("Simple Web App", "web_app"),
        ("E-commerce Platform", "ecommerce"),
        ("Document Storage", "document_storage"),
        ("AI/ML Platform", "ai_ml_platform"),
    ]

    cols = st.sidebar.columns(2)
    for i, (title, key) in enumerate(quick_scenarios):
        with cols[i % 2]:
            if st.button(title, key=f"quick_{key}", use_container_width=True):
                scenario = get_scenario_by_title(title)
                if scenario:
                    return scenario["user_request"]

    return None
