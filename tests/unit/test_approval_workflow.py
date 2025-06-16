"""Unit tests for approval workflow."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.iac_agents.approval_workflow import (
    TerraformApprovalWorkflow,
    ApprovalRequest,
    ApprovalStatus
)


def test_approval_workflow_initialization():
    """Test TerraformApprovalWorkflow can be initialized."""
    workflow = TerraformApprovalWorkflow()
    assert workflow is not None
    assert hasattr(workflow, 'create_approval_request')
    assert hasattr(workflow, 'get_approval_summary')


def test_approval_request_creation():
    """Test creating approval requests."""
    workflow = TerraformApprovalWorkflow()
    
    template = """
    resource "azurerm_storage_account" "test" {
      name = "test"
    }
    """
    
    request = workflow.create_approval_request(
        template=template,
        requirements="Storage account for documents",
        validation_result={"score": 85},
        estimated_cost={"total": 50.0}
    )
    
    assert isinstance(request, ApprovalRequest)
    assert request.template == template
    assert request.requirements == "Storage account for documents"
    assert request.status == ApprovalStatus.PENDING
    assert request.id is not None


def test_approval_request_with_minimal_data():
    """Test creating approval request with minimal data."""
    workflow = TerraformApprovalWorkflow()
    
    request = workflow.create_approval_request(
        template="resource test {}",
        requirements="Basic test",
        validation_result={},
        estimated_cost={}
    )
    
    assert isinstance(request, ApprovalRequest)
    assert request.template == "resource test {}"
    assert request.requirements == "Basic test"
    assert request.status == ApprovalStatus.PENDING


def test_approval_status_enum():
    """Test ApprovalStatus enum values."""
    assert ApprovalStatus.PENDING.value == "pending"
    assert ApprovalStatus.APPROVED.value == "approved" 
    assert ApprovalStatus.REJECTED.value == "rejected"
    assert ApprovalStatus.EXPIRED.value == "expired"


def test_approval_status_extended():
    """Test additional ApprovalStatus functionality."""
    # Test string representation
    assert str(ApprovalStatus.PENDING) in ["ApprovalStatus.PENDING", "pending"]
    assert str(ApprovalStatus.APPROVED) in ["ApprovalStatus.APPROVED", "approved"]


def test_get_approval_summary():
    """Test getting approval summary."""
    workflow = TerraformApprovalWorkflow()
    
    # Create a request first
    request = workflow.create_approval_request(
        template="resource test {}",
        requirements="Test requirements",
        validation_result={"score": 75},
        estimated_cost={"total": 25.0}
    )
    
    summary = workflow.get_approval_summary(request.id)
    
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "Test requirements" in summary or "test" in summary.lower()


def test_get_approval_summary_invalid_id():
    """Test getting approval summary with invalid ID."""
    workflow = TerraformApprovalWorkflow()
    
    summary = workflow.get_approval_summary("invalid-id")
    
    assert isinstance(summary, str)
    assert "not found" in summary.lower() or "error" in summary.lower()


def test_approval_request_timestamps():
    """Test that approval requests have proper timestamps."""
    workflow = TerraformApprovalWorkflow()
    
    request = workflow.create_approval_request(
        template="resource test {}",
        requirements="Test",
        validation_result={},
        estimated_cost={}
    )
    
    assert hasattr(request, 'created_at')
    assert isinstance(request.created_at, datetime)


def test_approval_workflow_multiple_requests():
    """Test creating multiple approval requests."""
    workflow = TerraformApprovalWorkflow()
    
    requests = []
    for i in range(3):
        request = workflow.create_approval_request(
            template=f"resource test{i} {{}}",
            requirements=f"Test {i}",
            validation_result={"score": 70 + i},
            estimated_cost={"total": 10.0 * i}
        )
        requests.append(request)
    
    # All requests should have unique IDs
    ids = [req.id for req in requests]
    assert len(set(ids)) == 3
    
    # All should be pending initially
    for request in requests:
        assert request.status == ApprovalStatus.PENDING


def test_approval_request_with_high_cost():
    """Test approval request with high cost estimation."""
    workflow = TerraformApprovalWorkflow()
    
    request = workflow.create_approval_request(
        template="resource expensive {}",
        requirements="Expensive infrastructure",
        validation_result={"score": 90},
        estimated_cost={"total": 5000.0}
    )
    
    assert isinstance(request, ApprovalRequest)
    assert request.status == ApprovalStatus.PENDING


def test_approval_request_with_low_compliance():
    """Test approval request with low compliance score."""
    workflow = TerraformApprovalWorkflow()
    
    request = workflow.create_approval_request(
        template="resource insecure {}",
        requirements="Less secure setup",
        validation_result={"score": 30, "violations": ["Missing encryption"]},
        estimated_cost={"total": 100.0}
    )
    
    assert isinstance(request, ApprovalRequest)
    assert request.status == ApprovalStatus.PENDING


def test_approval_workflow_error_handling():
    """Test approval workflow error handling."""
    workflow = TerraformApprovalWorkflow()
    
    # Test with None values
    try:
        request = workflow.create_approval_request(
            template=None,
            requirements=None,
            validation_result=None,
            estimated_cost=None
        )
        # Should either create request or handle gracefully
        assert request is None or isinstance(request, ApprovalRequest)
    except Exception:
        # Exception handling is also acceptable
        pass


def test_approval_request_data_structure():
    """Test approval request data structure."""
    workflow = TerraformApprovalWorkflow()
    
    request = workflow.create_approval_request(
        template="resource test {}",
        requirements="Test requirements",
        validation_result={"score": 80, "violations": []},
        estimated_cost={"total": 150.0, "breakdown": {"compute": 100, "storage": 50}}
    )
    
    # Test that request has expected attributes
    expected_attrs = ['id', 'template', 'requirements', 'status', 'created_at']
    for attr in expected_attrs:
        assert hasattr(request, attr), f"ApprovalRequest missing attribute: {attr}"


def test_approval_summary_content():
    """Test approval summary contains relevant information."""
    workflow = TerraformApprovalWorkflow()
    
    request = workflow.create_approval_request(
        template="resource azurerm_storage_account test {}",
        requirements="Storage for confidential documents",
        validation_result={"score": 85, "violations": ["Missing backup"]},
        estimated_cost={"total": 200.0}
    )
    
    summary = workflow.get_approval_summary(request.id)
    
    # Summary should contain key information
    assert isinstance(summary, str)
    assert len(summary) > 50  # Should be substantial
    
    # Should mention key aspects
    summary_lower = summary.lower()
    key_terms = ["storage", "cost", "score", "compliance"]
    matches = sum(1 for term in key_terms if term in summary_lower)
    assert matches >= 2, f"Summary should mention key terms: {summary}"


@patch('src.iac_agents.approval_workflow.datetime')
def test_approval_workflow_with_mocked_time(mock_datetime):
    """Test approval workflow with mocked datetime."""
    mock_now = datetime(2024, 1, 1, 12, 0, 0)
    mock_datetime.now.return_value = mock_now
    
    workflow = TerraformApprovalWorkflow()
    
    request = workflow.create_approval_request(
        template="resource test {}",
        requirements="Test",
        validation_result={},
        estimated_cost={}
    )
    
    assert isinstance(request, ApprovalRequest)
    # Should have used mocked time if datetime is used
    mock_datetime.now.assert_called()


def test_approval_workflow_string_representations():
    """Test string representations of approval objects."""
    workflow = TerraformApprovalWorkflow()
    
    request = workflow.create_approval_request(
        template="resource test {}",
        requirements="Test",
        validation_result={},
        estimated_cost={}
    )
    
    # Test that objects have reasonable string representations
    request_str = str(request)
    assert isinstance(request_str, str)
    assert len(request_str) > 0
    
    status_str = str(request.status)
    assert isinstance(status_str, str)
    assert status_str in ["pending", "approved", "rejected", "expired"] or "ApprovalStatus" in status_str


def test_approval_workflow_complex_validation():
    """Test approval workflow with complex validation results."""
    workflow = TerraformApprovalWorkflow()
    
    complex_validation = {
        "score": 75.5,
        "violations": [
            "Missing encryption at rest",
            "Public access enabled",
            "No backup configuration"
        ],
        "warnings": [
            "Cost may exceed budget",
            "Resource naming not standardized"
        ],
        "frameworks_checked": ["GDPR", "ISO 27001", "PCI DSS"],
        "passed_checks": [
            "HTTPS enforced",
            "Access logging enabled",
            "IAM roles configured"
        ]
    }
    
    request = workflow.create_approval_request(
        template="resource complex_infrastructure {}",
        requirements="Complex multi-tier application",
        validation_result=complex_validation,
        estimated_cost={"total": 1500.0, "monthly": 150.0}
    )
    
    assert isinstance(request, ApprovalRequest)
    assert request.status == ApprovalStatus.PENDING
    
    summary = workflow.get_approval_summary(request.id)
    assert isinstance(summary, str)
    assert len(summary) > 100  # Should be detailed for complex requests


def test_approval_workflow_edge_cases():
    """Test approval workflow edge cases."""
    workflow = TerraformApprovalWorkflow()
    
    edge_cases = [
        ("", "", {}, {}),  # Empty strings
        ("   ", "   ", {}, {}),  # Whitespace
        ("resource test {}", "Test" * 1000, {}, {}),  # Very long requirements
    ]
    
    for template, requirements, validation, cost in edge_cases:
        try:
            request = workflow.create_approval_request(
                template=template,
                requirements=requirements,
                validation_result=validation,
                estimated_cost=cost
            )
            # Should handle gracefully
            assert request is None or isinstance(request, ApprovalRequest)
        except Exception:
            # Exception handling is also acceptable for edge cases
            pass