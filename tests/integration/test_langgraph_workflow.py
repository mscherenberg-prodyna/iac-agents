"""Integration tests for LangGraph workflow implementation."""

import pytest

from src.iac_agents.agents.supervisor import LangGraphSupervisor


@pytest.mark.integration
def test_langgraph_document_storage_request():
    """Test document storage infrastructure request processing with LangGraph."""
    supervisor = LangGraphSupervisor()

    request = (
        "I need an Azure storage solution where I can store my archive documents "
        "in a cheap and compliant manner."
    )

    response = supervisor.process_user_request(request)

    # Verify response is generated
    assert response, "Response should not be empty"
    assert len(response) > 100, "Response should be substantial"

    # Verify workflow status
    status = supervisor.get_workflow_status()
    assert status["status"] in [
        "completed",
        "active",
    ], "Workflow should have valid status"
    assert len(status["completed_stages"]) > 0, "Should have completed some stages"

    # Verify HCL template is present
    assert "```hcl" in response, "Response should contain HCL code block"

    # Extract and validate template
    start = response.find("```hcl") + 6
    end = response.find("```", start)
    template = response[start:end].strip()

    assert template, "Template should not be empty"
    assert len(template) > 50, "Template should be substantial"
    assert (
        "terraform" in template.lower()
    ), "Template should contain terraform configuration"
    assert "azurerm" in template.lower(), "Template should use Azure provider"


@pytest.mark.integration
def test_langgraph_compliance_validation():
    """Test that LangGraph compliance validation works correctly."""
    supervisor = LangGraphSupervisor()

    # Test with compliance enforcement
    compliance_settings = {
        "enforce_compliance": True,
        "selected_frameworks": ["PCI DSS", "GDPR"],
    }

    request = "Create a database for storing customer payment information."

    response = supervisor.process_user_request(request, compliance_settings)

    assert response, "Response should not be empty"
    assert (
        "compliance" in response.lower() or "validation" in response.lower()
    ), "Response should mention compliance when enforced"

    # Check workflow status
    status = supervisor.get_workflow_status()
    assert "compliance_score" in status, "Should have compliance score"
    assert isinstance(
        status["compliance_score"], (int, float)
    ), "Compliance score should be numeric"


@pytest.mark.integration
def test_langgraph_workflow_stages():
    """Test that LangGraph workflow executes expected stages."""
    supervisor = LangGraphSupervisor()

    request = "I need a simple storage account for documents."

    supervisor.process_user_request(request)
    status = supervisor.get_workflow_status()

    # Check that essential stages were completed
    completed_stages = status.get("completed_stages", [])
    expected_stages = [
        "requirements_analysis",
        "template_generation",
        "validation_and_compliance",
        "approval_preparation",
    ]

    for stage in expected_stages:
        assert stage in completed_stages, f"Stage {stage} should be completed"

    # Check that workflow status includes key information
    assert "quality_gate_passed" in status, "Should have quality gate status"
    assert isinstance(
        status["quality_gate_passed"], bool
    ), "Quality gate should be boolean"


def test_langgraph_error_handling():
    """Test LangGraph error handling with invalid input."""
    supervisor = LangGraphSupervisor()

    # Test with empty input
    response = supervisor.process_user_request("")
    assert response, "Should get some response even with empty input"
    assert (
        "error" in response.lower() or len(response) > 10
    ), "Should handle empty input gracefully"

    # Test workflow status after error
    status = supervisor.get_workflow_status()
    assert status["status"] in [
        "idle",
        "completed",
        "active",
    ], "Should have valid status after error"


def test_langgraph_conversation_history():
    """Test that LangGraph supervisor maintains conversation history."""
    supervisor = LangGraphSupervisor()

    request1 = "Create a storage account."
    request2 = "Add backup capabilities."

    supervisor.process_user_request(request1)
    supervisor.process_user_request(request2)

    history = supervisor.get_conversation_history()

    assert len(history) == 4, "Should have 4 entries (2 user + 2 assistant)"
    assert history[0]["role"] == "user", "First entry should be user"
    assert history[0]["content"] == request1, "First entry should match first request"
    assert history[2]["role"] == "user", "Third entry should be user"
    assert history[2]["content"] == request2, "Third entry should match second request"

    # Test clearing history
    supervisor.clear_history()
    history = supervisor.get_conversation_history()
    assert len(history) == 0, "History should be empty after clearing"
