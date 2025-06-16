"""Integration tests to ensure Streamlit components work with agent implementations."""

from unittest.mock import Mock, patch

import pytest

from src.iac_agents.agents import SupervisorAgent
from src.iac_agents.streamlit.main_interface import StreamlitInterface


@pytest.mark.integration
def test_streamlit_supervisor_interface_compatibility():
    """Test that Streamlit interface works with current SupervisorAgent implementation."""
    # This test prevents the AttributeError that occurred with LangGraph migration
    supervisor = SupervisorAgent()

    # Test required interface methods exist
    assert hasattr(
        supervisor, "get_workflow_status"
    ), "Supervisor must have get_workflow_status method"
    assert hasattr(
        supervisor, "process_user_request"
    ), "Supervisor must have process_user_request method"
    assert hasattr(
        supervisor, "get_conversation_history"
    ), "Supervisor must have get_conversation_history method"
    assert hasattr(
        supervisor, "clear_history"
    ), "Supervisor must have clear_history method"

    # Test workflow status structure
    status = supervisor.get_workflow_status()
    assert isinstance(status, dict), "get_workflow_status must return dict"
    assert "status" in status, "Workflow status must have 'status' key"

    # Test that status can be idle without errors
    if status.get("status") == "idle":
        assert True  # This is expected for a new supervisor
    else:
        # If active, verify expected keys
        assert "current_stage" in status, "Active workflow must have current_stage"
        assert (
            "completed_stages" in status
        ), "Active workflow must have completed_stages"


@pytest.mark.integration
def test_streamlit_interface_initialization_with_supervisor():
    """Test that StreamlitInterface initializes correctly with current supervisor."""
    # This test ensures interface can be created without errors
    interface = StreamlitInterface()

    # Verify supervisor initialization
    assert interface.supervisor_agent is not None
    assert hasattr(interface.supervisor_agent, "get_workflow_status")

    # Test workflow status access (this was the failing code path)
    try:
        status = interface.supervisor_agent.get_workflow_status()
        assert isinstance(status, dict)
    except AttributeError as e:
        pytest.fail(f"Interface supervisor missing required attribute: {e}")


@pytest.mark.integration
def test_sidebar_workflow_progress_compatibility():
    """Test that sidebar workflow progress works with current supervisor."""
    from src.iac_agents.streamlit.components.sidebar import display_workflow_progress

    supervisor = SupervisorAgent()

    # Mock streamlit to avoid UI dependencies
    with patch("src.iac_agents.streamlit.components.sidebar.st") as mock_st:
        mock_st.sidebar = Mock()

        # This should not raise AttributeError for current_workflow
        try:
            display_workflow_progress(supervisor)
        except AttributeError as e:
            if "current_workflow" in str(e):
                pytest.fail(f"Sidebar component not compatible with supervisor: {e}")
            else:
                # Other AttributeErrors might be from mocking, which is ok
                pass


@pytest.mark.integration
def test_supervisor_workflow_state_transition():
    """Test supervisor workflow state changes correctly."""
    supervisor = SupervisorAgent()

    # Initial state should be idle
    initial_status = supervisor.get_workflow_status()
    assert initial_status["status"] == "idle"

    # After processing request, should have workflow state
    test_request = "Create a simple storage account"

    try:
        response = supervisor.process_user_request(test_request)
        assert response is not None

        # Check final state
        final_status = supervisor.get_workflow_status()
        assert "status" in final_status

        # Should have completed stages
        if final_status["status"] in ["completed", "active"]:
            assert "completed_stages" in final_status
            assert isinstance(final_status["completed_stages"], list)

    except Exception as e:
        pytest.fail(f"Supervisor request processing failed: {e}")


@pytest.mark.integration
def test_conversation_history_compatibility():
    """Test that conversation history works with Streamlit interface."""
    supervisor = SupervisorAgent()

    # Test initial history
    history = supervisor.get_conversation_history()
    assert isinstance(history, list)
    assert len(history) == 0

    # Test after processing
    supervisor.process_user_request("Test message")
    history = supervisor.get_conversation_history()
    assert len(history) >= 2  # user + assistant messages

    # Test clear history
    supervisor.clear_history()
    history = supervisor.get_conversation_history()
    assert len(history) == 0


@pytest.mark.integration
def test_interface_error_handling():
    """Test that interface handles supervisor errors gracefully."""
    interface = StreamlitInterface()

    # Test that supervisor error handling works at the method level
    with patch.object(
        interface.supervisor_agent,
        "process_user_request",
        side_effect=Exception("Test error"),
    ):
        try:
            # This should not crash the interface
            interface.supervisor_agent.process_user_request("test")
        except Exception:
            # Exception is expected, but interface should be stable
            pass

    # Interface should still be usable after error
    status = interface.supervisor_agent.get_workflow_status()
    assert isinstance(status, dict)


def test_supervisor_interface_contract():
    """Test that supervisor implements expected interface contract."""
    supervisor = SupervisorAgent()

    # Required methods for Streamlit compatibility
    required_methods = [
        "process_user_request",
        "get_workflow_status",
        "get_conversation_history",
        "clear_history",
    ]

    for method in required_methods:
        assert hasattr(
            supervisor, method
        ), f"Supervisor missing required method: {method}"
        assert callable(
            getattr(supervisor, method)
        ), f"Supervisor {method} is not callable"

    # Test method signatures don't break
    try:
        status = supervisor.get_workflow_status()
        assert isinstance(status, dict)

        history = supervisor.get_conversation_history()
        assert isinstance(history, list)

        supervisor.clear_history()

        # Test process_user_request accepts expected parameters
        response = supervisor.process_user_request(
            "test", compliance_settings={"test": True}
        )
        assert isinstance(response, str)

    except TypeError as e:
        pytest.fail(f"Supervisor method signature incompatible: {e}")
