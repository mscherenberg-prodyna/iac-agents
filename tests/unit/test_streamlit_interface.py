"""Unit tests for Streamlit interface components."""

from unittest.mock import Mock, patch

import pytest

from src.iac_agents.agents import SupervisorAgent
from src.iac_agents.streamlit.components.sidebar import display_workflow_progress
from src.iac_agents.streamlit.main_interface import StreamlitInterface


def test_display_workflow_progress_with_langgraph_supervisor():
    """Test that display_workflow_progress works with LangGraph supervisor."""
    # Create a mock supervisor that behaves like LangGraphSupervisor
    mock_supervisor = Mock(spec=SupervisorAgent)
    mock_supervisor.get_workflow_status.return_value = {
        "status": "active",
        "current_stage": "template_generation",
        "completed_stages": ["requirements_analysis", "research_planning"],
        "issues_found": ["Warning: Template needs review"],
        "quality_gate_passed": True,
        "compliance_score": 85.0,
    }

    # Mock streamlit components
    with patch("src.iac_agents.streamlit.components.sidebar.st") as mock_st:
        mock_st.sidebar = Mock()

        # This should not raise an AttributeError
        display_workflow_progress(mock_supervisor)

        # Verify the supervisor method was called
        mock_supervisor.get_workflow_status.assert_called_once()

        # Verify streamlit components were called
        assert mock_st.sidebar.markdown.called
        assert mock_st.sidebar.progress.called


def test_display_workflow_progress_idle_state():
    """Test display_workflow_progress when workflow is idle."""
    mock_supervisor = Mock(spec=SupervisorAgent)
    mock_supervisor.get_workflow_status.return_value = {"status": "idle"}

    with patch("src.iac_agents.streamlit.components.sidebar.st") as mock_st:
        mock_st.sidebar = Mock()

        display_workflow_progress(mock_supervisor)

        # Should not display progress when idle
        mock_st.sidebar.markdown.assert_not_called()
        mock_st.sidebar.progress.assert_not_called()


def test_streamlit_interface_initialization():
    """Test that StreamlitInterface can be initialized with LangGraph supervisor."""
    # This should not raise any errors
    interface = StreamlitInterface()

    # Verify the supervisor is initialized
    assert hasattr(interface, "supervisor_agent")
    assert hasattr(interface.supervisor_agent, "get_workflow_status")


def test_streamlit_interface_workflow_status_compatibility():
    """Test that StreamlitInterface supervisor has compatible methods."""
    interface = StreamlitInterface()

    # Test that required methods exist
    assert hasattr(interface.supervisor_agent, "process_user_request")
    assert hasattr(interface.supervisor_agent, "get_workflow_status")
    assert hasattr(interface.supervisor_agent, "get_conversation_history")
    assert hasattr(interface.supervisor_agent, "clear_history")

    # Test workflow status returns expected structure
    status = interface.supervisor_agent.get_workflow_status()
    assert isinstance(status, dict)
    assert "status" in status


@patch("src.iac_agents.streamlit.components.sidebar.st")
def test_workflow_progress_display_formatting(mock_st):
    """Test that workflow progress displays stages with proper formatting."""
    mock_supervisor = Mock(spec=SupervisorAgent)
    mock_supervisor.get_workflow_status.return_value = {
        "status": "active",
        "current_stage": "template_generation",
        "completed_stages": ["requirements_analysis", "research_and_planning"],
        "issues_found": [],
    }

    mock_st.sidebar = Mock()

    display_workflow_progress(mock_supervisor)

    # Check that stage names are properly formatted (underscores to spaces, title case)
    calls = mock_st.sidebar.markdown.call_args_list
    stage_calls = [
        call
        for call in calls
        if "Template Generation" in str(call) or "Requirements Analysis" in str(call)
    ]

    assert len(stage_calls) > 0, "Stage names should be formatted and displayed"


def test_workflow_progress_error_handling():
    """Test that workflow progress handles errors gracefully."""
    mock_supervisor = Mock(spec=SupervisorAgent)
    mock_supervisor.get_workflow_status.side_effect = Exception("Test error")

    with patch("src.iac_agents.streamlit.components.sidebar.st") as mock_st:
        mock_st.sidebar = Mock()

        # Should not raise exception
        try:
            display_workflow_progress(mock_supervisor)
        except Exception as e:
            pytest.fail(
                f"display_workflow_progress should handle errors gracefully, but raised: {e}"
            )


def test_main_interface_with_langgraph():
    """Test that main interface initializes correctly with LangGraph supervisor."""
    # Test basic initialization without Streamlit session state complexity
    interface = StreamlitInterface()

    # Verify interface components are initialized
    assert interface.supervisor_agent is not None
    assert interface.approval_workflow is not None
    assert interface.deployment_manager is not None

    # Test supervisor has required methods
    assert hasattr(interface.supervisor_agent, "process_user_request")
    assert hasattr(interface.supervisor_agent, "get_workflow_status")
    assert hasattr(interface.supervisor_agent, "get_conversation_history")

    # Test method calls work
    status = interface.supervisor_agent.get_workflow_status()
    assert isinstance(status, dict)
    assert "status" in status

    history = interface.supervisor_agent.get_conversation_history()
    assert isinstance(history, list)
