"""Test supervisor agent request processing capabilities."""

from src.iac_agents.agents import SupervisorAgent
from src.iac_agents.logging_system import log_user_update


def test_basic_request_processing():
    """Test that supervisor agent can process simple infrastructure requests and return appropriate responses with rate limiting protection."""
    log_user_update("Testing simple infrastructure request")

    supervisor = SupervisorAgent()

    # Simple test request
    simple_request = "I need a basic storage account for documents in Azure."

    try:
        response = supervisor.process_user_request(simple_request)

        # Verify response
        assert response
        assert len(response) > 0

        # Check if response contains expected infrastructure content
        response_lower = response.lower()
        assert "azure" in response_lower or "storage" in response_lower

    except Exception as e:
        # If there's an error, fail the test
        assert False, f"Error processing request: {e}"


def test_workflow_status_progression():
    """Test that workflow status progresses correctly during request processing."""
    supervisor = SupervisorAgent()
    
    # Initial status should be idle
    initial_status = supervisor.get_workflow_status()
    assert initial_status["status"] == "idle"
    
    # Process a request
    request = "Create a simple web application infrastructure"
    response = supervisor.process_user_request(request)
    
    # Should have response
    assert response
    assert len(response) > 100
    
    # Final status should show completion
    final_status = supervisor.get_workflow_status()
    assert final_status["status"] in ["completed", "active"]
    
    # Should have completed stages
    completed_stages = final_status.get("completed_stages", [])
    assert len(completed_stages) > 0
    
    # Should contain essential stages
    expected_stages = ["requirements_analysis", "template_generation", "validation_and_compliance"]
    for stage in expected_stages:
        assert stage in completed_stages, f"Missing essential stage: {stage}"


def test_conversation_history_tracking():
    """Test that conversation history is properly maintained."""
    supervisor = SupervisorAgent()
    
    # Initial history should be empty
    history = supervisor.get_conversation_history()
    assert len(history) == 0
    
    # Process first request
    request1 = "Create a storage account"
    supervisor.process_user_request(request1)
    
    history = supervisor.get_conversation_history()
    assert len(history) == 2  # user + assistant
    assert history[0]["role"] == "user"
    assert history[0]["content"] == request1
    assert history[1]["role"] == "assistant"
    
    # Process second request
    request2 = "Add backup capabilities"
    supervisor.process_user_request(request2)
    
    history = supervisor.get_conversation_history()
    assert len(history) == 4  # 2 user + 2 assistant
    assert history[2]["content"] == request2


def test_error_handling_robustness():
    """Test that supervisor handles various error conditions gracefully."""
    supervisor = SupervisorAgent()
    
    # Test with empty input
    response = supervisor.process_user_request("")
    assert response  # Should get some response, not crash
    
    # Test with very long input
    long_input = "Create infrastructure " * 1000
    response = supervisor.process_user_request(long_input)
    assert response  # Should handle gracefully
    
    # Test with special characters
    special_input = "Create infrastructure with émojis 🚀 and symbols @#$%"
    response = supervisor.process_user_request(special_input)
    assert response


def test_compliance_settings_integration():
    """Test that compliance settings are properly integrated into workflow."""
    supervisor = SupervisorAgent()
    
    compliance_settings = {
        "enforce_compliance": True,
        "selected_frameworks": ["GDPR", "PCI DSS"]
    }
    
    request = "Create a database for storing customer information"
    response = supervisor.process_user_request(request, compliance_settings)
    
    assert response
    assert len(response) > 100
    
    # Should mention compliance when enforced
    response_lower = response.lower()
    assert "compliance" in response_lower or "validation" in response_lower
    
    # Verify workflow status includes compliance information
    status = supervisor.get_workflow_status()
    assert "compliance_score" in status or "quality_gate_passed" in status


if __name__ == "__main__":
    # Test basic request
    test_basic_request_processing()
    print("✅ Basic request processing test passed")
    
    # Test workflow progression
    test_workflow_status_progression()
    print("✅ Workflow status progression test passed")