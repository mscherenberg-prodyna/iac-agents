"""Showcase scenarios component for conference demonstrations."""

import json
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from .chat import add_message
from .compliance_panel import set_compliance_settings


def load_showcase_scenarios() -> Dict[str, Any]:
    """Load showcase scenarios from JSON file."""
    try:
        scenarios_path = (
            Path(__file__).parent.parent.parent
            / "templates"
            / "data"
            / "showcase_scenarios.json"
        )
        with open(scenarios_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load showcase scenarios: {e}")
        return {}


def render_showcase_scenarios():
    """Render showcase scenarios section in sidebar."""
    st.markdown("### 🎯 Demo Scenarios")

    scenarios = load_showcase_scenarios()

    if not scenarios:
        st.warning("No showcase scenarios available")
        return

    # Create a selectbox for choosing scenarios
    scenario_options = ["Select a demo scenario..."] + [
        f"{scenarios[key]['title']}" for key in scenarios.keys()
    ]

    selected_scenario = st.selectbox(
        "Choose Demo Scenario", scenario_options, key="showcase_scenario_select"
    )

    if selected_scenario != "Select a demo scenario...":
        # Find the scenario key
        scenario_key = None
        for key, scenario in scenarios.items():
            if scenario["title"] == selected_scenario:
                scenario_key = key
                break

        if scenario_key:
            scenario_data = scenarios[scenario_key]

            # Show scenario details
            with st.expander("📋 Scenario Details", expanded=False):
                st.markdown(f"**Context:** {scenario_data['business_context']}")
                st.markdown(
                    f"**Expected Cost:** {scenario_data.get('estimated_cost', 'N/A')}"
                )

                if "expected_resources" in scenario_data:
                    st.markdown("**Expected Resources:**")
                    for resource in scenario_data["expected_resources"]:
                        st.markdown(f"• {resource}")

            # Load scenario button
            if st.button(
                f"🚀 Load Demo: {scenario_data['title']}",
                key=f"load_scenario_{scenario_key}",
                help="Load this scenario and auto-configure compliance settings",
                use_container_width=True,
            ):
                load_showcase_scenario(scenario_key, scenario_data)
                st.success(f"✅ Loaded: {scenario_data['title']}")
                st.rerun()


def load_showcase_scenario(scenario_key: str, scenario_data: Dict[str, Any]):
    """Load a showcase scenario into the session."""

    # Set compliance settings if specified
    if "compliance_requirements" in scenario_data:
        compliance_settings = {
            "enforce_compliance": True,
            "selected_frameworks": scenario_data["compliance_requirements"],
        }
        set_compliance_settings(compliance_settings)

        # Also set the checkbox states in session state for proper UI update
        for framework in scenario_data["compliance_requirements"]:
            st.session_state[f"compliance_{framework}"] = True

    # Add the initial user message to chat
    add_message("user", scenario_data["user_request"].strip())

    # Store scenario info in session state for handling clarifying questions
    st.session_state.active_showcase_scenario = {
        "key": scenario_key,
        "data": scenario_data,
        "questions_asked": False,
    }

    # Set up workflow to start
    st.session_state.workflow_active = True
    st.session_state.workflow_status = "Starting showcase scenario..."
    st.session_state.current_agent_status = "Cloud Architect"
    st.session_state.current_workflow_phase = "Planning"
    st.session_state.workflow_result = {}
    st.session_state.workflow_error = None
    st.session_state.workflow_interrupted = False
    st.session_state.pending_workflow_input = scenario_data["user_request"].strip()


def handle_showcase_clarifying_questions(user_input: str) -> bool:
    """Handle clarifying questions for showcase scenarios.

    Returns True if the input was handled as a showcase scenario response.
    """
    # This function is kept for compatibility but actual handling is done
    # through the auto-answer button in the chat interface
    del user_input  # Parameter kept for API compatibility
    return False


def should_show_auto_answer_button() -> bool:
    """Check if we should show the auto-answer button for showcase scenarios."""

    # Check if we have an active showcase scenario
    if "active_showcase_scenario" not in st.session_state:
        return False

    scenario_info = st.session_state.active_showcase_scenario
    scenario_data = scenario_info["data"]

    # Check if we have clarifying questions and answers
    if (
        "clarifying_questions" not in scenario_data
        or "suggested_answers" not in scenario_data
    ):
        return False

    # Check if the last assistant message contains clarifying questions
    messages = st.session_state.get("messages", [])
    if not messages:
        return False

    last_message = messages[-1]
    if last_message.get("role") != "assistant":
        return False

    # Check if this is a clarification request from the agent
    message_content = last_message.get("content", "").upper()
    is_likely_clarifying = "CLARIFICATION_REQUIRED" in message_content

    # Only show if we haven't answered yet
    return is_likely_clarifying and not scenario_info.get("questions_answered", False)


def render_auto_answer_button():
    """Render the auto-answer button if appropriate."""

    if not should_show_auto_answer_button():
        return

    scenario_info = st.session_state.active_showcase_scenario
    scenario_data = scenario_info["data"]

    st.markdown("---")
    st.markdown("**🎯 Demo Mode Active**")
    st.markdown("*Click below to auto-answer with realistic responses*")

    if st.button(
        "🎯 Auto-Answer Demo Questions",
        key="auto_answer_demo",
        use_container_width=True,
    ):
        # Combine all suggested answers
        suggested_answers = scenario_data["suggested_answers"]
        combined_answer = "\n".join(suggested_answers)

        # Add the combined answer as a user message
        add_message("user", combined_answer)

        # Mark questions as answered
        st.session_state.active_showcase_scenario["questions_answered"] = True

        # Trigger workflow continuation
        st.session_state.pending_workflow_input = combined_answer
        st.session_state.workflow_active = True
        st.session_state.workflow_status = "Processing demo responses..."

        st.rerun()
