"""Unit tests for LangGraph workflow nodes."""

import pytest
from unittest.mock import Mock, patch

from src.iac_agents.agents.nodes.requirements_analysis import (
    requirements_analysis_node,
    _estimate_complexity,
    _extract_compliance_requirements,
    _extract_components,
    _determine_workflow_stages
)
from src.iac_agents.agents.nodes.template_generation import (
    template_generation_node,
    _extract_template_from_response,
    _is_valid_terraform_content
)
from src.iac_agents.agents.nodes.validation_compliance import (
    validation_compliance_node
)
from src.iac_agents.agents.nodes.cost_estimation import (
    cost_estimation_node
)
from src.iac_agents.agents.nodes.approval_preparation import (
    approval_preparation_node
)
from src.iac_agents.agents.state import WorkflowStage


def test_requirements_analysis_node():
    """Test requirements analysis node."""
    state = {
        "user_input": "I need a secure storage account for documents",
        "completed_stages": []
    }
    
    result = requirements_analysis_node(state)
    
    assert isinstance(result, dict)
    assert result["current_stage"] == WorkflowStage.REQUIREMENTS_ANALYSIS.value
    assert WorkflowStage.REQUIREMENTS_ANALYSIS.value in result["completed_stages"]
    assert "requirements_analysis_result" in result
    assert "workflow_plan" in result
    
    # Check analysis result structure
    analysis_result = result["requirements_analysis_result"]
    assert isinstance(analysis_result, dict)
    assert "status" in analysis_result


def test_estimate_complexity():
    """Test complexity estimation function."""
    simple_input = "Create a basic storage account"
    complex_input = "Create an enterprise scalable high availability multi-region solution"
    
    simple_score = _estimate_complexity(simple_input)
    complex_score = _estimate_complexity(complex_input)
    
    assert isinstance(simple_score, int)
    assert isinstance(complex_score, int)
    assert complex_score > simple_score
    assert 1 <= simple_score <= 10
    assert 1 <= complex_score <= 10


def test_extract_compliance_requirements():
    """Test compliance requirements extraction."""
    inputs = [
        "Create a legal document storage",
        "Need financial data compliance",
        "Healthcare patient data storage",
        "Simple storage account"
    ]
    
    for user_input in inputs:
        requirements = _extract_compliance_requirements(user_input)
        assert isinstance(requirements, list)
        assert len(requirements) > 0
        # Should return valid compliance frameworks
        valid_frameworks = ["GDPR", "PCI DSS", "HIPAA", "SOX", "ISO 27001", "SOC 2"]
        for req in requirements:
            assert req in valid_frameworks


def test_extract_components():
    """Test component extraction function."""
    test_cases = [
        ("Create a web application with database", ["web application", "database"]),
        ("Need storage for documents", ["storage"]),
        ("Virtual machine with networking", ["compute", "networking"]),
        ("Secure key vault and firewall", ["security"])
    ]
    
    for user_input, expected_components in test_cases:
        components = _extract_components(user_input)
        assert isinstance(components, list)
        for expected in expected_components:
            assert expected in components


def test_determine_workflow_stages():
    """Test workflow stage determination."""
    simple_analysis = {"estimated_complexity": 3, "compliance_requirements": ["GDPR"]}
    complex_analysis = {"estimated_complexity": 8, "compliance_requirements": ["GDPR", "PCI DSS", "HIPAA"]}
    
    simple_stages = _determine_workflow_stages(simple_analysis)
    complex_stages = _determine_workflow_stages(complex_analysis)
    
    assert isinstance(simple_stages, list)
    assert isinstance(complex_stages, list)
    assert len(complex_stages) >= len(simple_stages)
    
    # Both should include essential stages
    essential_stages = [
        WorkflowStage.REQUIREMENTS_ANALYSIS.value,
        WorkflowStage.TEMPLATE_GENERATION.value,
        WorkflowStage.VALIDATION_AND_COMPLIANCE.value
    ]
    for stage in essential_stages:
        assert stage in simple_stages
        assert stage in complex_stages


@patch('src.iac_agents.agents.nodes.template_generation.TerraformAgent')
def test_template_generation_node(mock_terraform_agent):
    """Test template generation node."""
    mock_agent = Mock()
    mock_agent.generate_response.return_value = """
    Here's your template:
    
    ```hcl
    resource "azurerm_storage_account" "test" {
      name = "mystorageaccount"
    }
    ```
    """
    mock_terraform_agent.return_value = mock_agent
    
    state = {
        "user_input": "Create storage account",
        "completed_stages": ["requirements_analysis"]
    }
    
    result = template_generation_node(state)
    
    assert isinstance(result, dict)
    assert result["current_stage"] == WorkflowStage.TEMPLATE_GENERATION.value
    assert WorkflowStage.TEMPLATE_GENERATION.value in result["completed_stages"]
    assert "template_generation_result" in result
    assert "final_template" in result
    
    mock_agent.generate_response.assert_called_once()


def test_extract_template_from_response():
    """Test template extraction from agent response."""
    response_with_hcl = """
    Here's your infrastructure template:
    
    ```hcl
    resource "azurerm_storage_account" "test" {
      name                     = "mystorageaccount"
      resource_group_name      = azurerm_resource_group.main.name
      location                 = azurerm_resource_group.main.location
      account_tier             = "Standard"
      account_replication_type = "LRS"
    }
    ```
    
    This template creates a basic storage account.
    """
    
    template = _extract_template_from_response(response_with_hcl)
    assert template
    assert "azurerm_storage_account" in template
    assert "resource" in template
    
    # Test with no code blocks
    response_no_code = "This is just text without any code blocks."
    template = _extract_template_from_response(response_no_code)
    assert template == ""
    
    # Test with generic code block
    response_generic = """
    Here's the template:
    
    ```
    resource "azurerm_storage_account" "test" {
      name = "test"
    }
    ```
    """
    
    template = _extract_template_from_response(response_generic)
    assert template
    assert "azurerm_storage_account" in template


def test_is_valid_terraform_content():
    """Test Terraform content validation."""
    valid_terraform = """
    resource "azurerm_storage_account" "test" {
      name = "test"
    }
    """
    
    invalid_content = "This is just text"
    partial_content = "resource {"
    
    assert _is_valid_terraform_content(valid_terraform) is True
    assert _is_valid_terraform_content(invalid_content) is False
    assert _is_valid_terraform_content(partial_content) is True  # Has keywords and syntax


@patch('src.iac_agents.agents.nodes.validation_compliance.ComplianceFramework')
@patch('src.iac_agents.agents.nodes.validation_compliance.TerraformAgent')
def test_validation_compliance_node(mock_terraform_agent, mock_compliance_framework):
    """Test validation compliance node."""
    # Mock compliance framework
    mock_framework = Mock()
    mock_framework.validate_template.return_value = {
        "compliance_score": 85.0,
        "violations": ["Warning: Missing encryption"]
    }
    mock_compliance_framework.return_value = mock_framework
    
    # Mock terraform agent
    mock_agent = Mock()
    mock_agent._validate_template.return_value = {
        "passed_checks": ["Syntax valid"],
        "issues": []
    }
    mock_terraform_agent.return_value = mock_agent
    
    state = {
        "final_template": "resource \"azurerm_storage_account\" \"test\" {}",
        "compliance_settings": {"enforce_compliance": True, "selected_frameworks": ["GDPR"]},
        "completed_stages": ["requirements_analysis", "template_generation"]
    }
    
    result = validation_compliance_node(state)
    
    assert isinstance(result, dict)
    assert result["current_stage"] == WorkflowStage.VALIDATION_AND_COMPLIANCE.value
    assert WorkflowStage.VALIDATION_AND_COMPLIANCE.value in result["completed_stages"]
    assert "compliance_validation_result" in result
    assert "compliance_score" in result
    assert "quality_gate_passed" in result
    
    mock_framework.validate_template.assert_called_once()
    mock_agent._validate_template.assert_called_once()


def test_validation_compliance_node_no_template():
    """Test validation compliance node without template."""
    state = {
        "final_template": "",
        "completed_stages": ["requirements_analysis"]
    }
    
    result = validation_compliance_node(state)
    
    assert isinstance(result, dict)
    assert result["current_stage"] == WorkflowStage.VALIDATION_AND_COMPLIANCE.value
    assert "errors" in result
    assert any("No template available" in error for error in result["errors"])


def test_cost_estimation_node():
    """Test cost estimation node."""
    state = {
        "final_template": """
        resource "azurerm_storage_account" "test" {
          name = "test"
        }
        resource "azurerm_virtual_machine" "vm" {
          name = "testvm"
        }
        """,
        "completed_stages": ["requirements_analysis", "template_generation", "validation_and_compliance"]
    }
    
    result = cost_estimation_node(state)
    
    assert isinstance(result, dict)
    assert result["current_stage"] == WorkflowStage.COST_ESTIMATION.value
    assert WorkflowStage.COST_ESTIMATION.value in result["completed_stages"]
    assert "cost_estimation_result" in result
    
    # Check cost estimation result structure
    cost_result = result["cost_estimation_result"]
    assert isinstance(cost_result, dict)
    assert "status" in cost_result


def test_cost_estimation_node_no_template():
    """Test cost estimation node without template."""
    state = {
        "final_template": "",
        "completed_stages": ["requirements_analysis"]
    }
    
    result = cost_estimation_node(state)
    
    assert isinstance(result, dict)
    assert result["current_stage"] == WorkflowStage.COST_ESTIMATION.value
    assert "cost_estimation_result" in result
    cost_result = result["cost_estimation_result"]
    assert "error" in cost_result


def test_approval_preparation_node():
    """Test approval preparation node."""
    state = {
        "final_template": "resource \"azurerm_storage_account\" \"test\" {}",
        "user_input": "Create storage account",
        "compliance_validation_result": {
            "data": {
                "compliance_validation": {"score": 85},
                "validation_frameworks": ["GDPR"]
            }
        },
        "cost_estimation_result": {
            "data": {
                "cost_estimate": {"total_monthly_usd": 25.0}
            }
        },
        "compliance_score": 85.0,
        "completed_stages": ["requirements_analysis", "template_generation", "validation_and_compliance", "cost_estimation"]
    }
    
    result = approval_preparation_node(state)
    
    assert isinstance(result, dict)
    assert result["current_stage"] == WorkflowStage.APPROVAL_PREPARATION.value
    assert WorkflowStage.APPROVAL_PREPARATION.value in result["completed_stages"]
    assert "approval_preparation_result" in result
    assert "requires_approval" in result
    assert result["requires_approval"] is True
    assert "approval_request_id" in result
    
    # Check approval preparation result structure
    approval_result = result["approval_preparation_result"]
    assert isinstance(approval_result, dict)
    assert "status" in approval_result


def test_node_error_handling():
    """Test error handling in nodes."""
    invalid_state = None
    
    # Test that nodes handle invalid state gracefully
    with pytest.raises((TypeError, KeyError)):
        requirements_analysis_node(invalid_state)
    
    # Test with missing required fields
    incomplete_state = {"user_input": "test"}
    
    result = requirements_analysis_node(incomplete_state)
    assert isinstance(result, dict)
    assert "completed_stages" in result


def test_workflow_stage_progression():
    """Test that stages are added correctly to completed_stages."""
    state = {
        "user_input": "Create storage account",
        "completed_stages": []
    }
    
    # Requirements analysis
    result1 = requirements_analysis_node(state)
    assert len(result1["completed_stages"]) == 1
    assert WorkflowStage.REQUIREMENTS_ANALYSIS.value in result1["completed_stages"]
    
    # Template generation (simulate)
    state_with_analysis = {
        **result1,
        "completed_stages": result1["completed_stages"]
    }
    
    # Should not duplicate stages
    result2 = requirements_analysis_node(state_with_analysis)
    # Count should be same since stage already completed
    completed_count = result2["completed_stages"].count(WorkflowStage.REQUIREMENTS_ANALYSIS.value)
    assert completed_count == 1