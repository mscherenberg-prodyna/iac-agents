"""Unit tests for state module."""

import pytest

from src.iac_agents.agents.state import (
    InfrastructureStateDict,
    StageResult,
    TemplateGenerationResult,
    WorkflowStage,
)


class TestWorkflowStage:
    """Test WorkflowStage enum."""

    def test_workflow_stages_exist(self):
        """Test that all expected workflow stages exist."""
        expected_stages = [
            "REQUIREMENTS_ANALYSIS",
            "RESEARCH_AND_PLANNING",
            "TEMPLATE_GENERATION",
            "VALIDATION_AND_COMPLIANCE",
            "COST_ESTIMATION",
            "APPROVAL_PREPARATION",
            "TEMPLATE_REFINEMENT",
            "COMPLETED",
        ]

        for stage in expected_stages:
            assert hasattr(WorkflowStage, stage)

    def test_workflow_stage_values(self):
        """Test workflow stage values."""
        assert WorkflowStage.REQUIREMENTS_ANALYSIS.value == "requirements_analysis"
        assert WorkflowStage.TEMPLATE_GENERATION.value == "template_generation"
        assert WorkflowStage.COMPLETED.value == "completed"


class TestStageResult:
    """Test StageResult model."""

    def test_stage_result_creation(self):
        """Test creating a StageResult."""
        result = StageResult(status="completed")
        assert result.status == "completed"
        assert result.data is None
        assert result.errors == []
        assert result.warnings == []
        assert result.timestamp is None

    def test_stage_result_with_all_fields(self):
        """Test creating a StageResult with all fields."""
        result = StageResult(
            status="in_progress",
            data={"key": "value"},
            errors=["error1", "error2"],
            warnings=["warning1"],
            timestamp="2023-01-01T00:00:00Z",
        )
        assert result.status == "in_progress"
        assert result.data == {"key": "value"}
        assert result.errors == ["error1", "error2"]
        assert result.warnings == ["warning1"]
        assert result.timestamp == "2023-01-01T00:00:00Z"

    def test_stage_result_defaults(self):
        """Test StageResult default values."""
        result = StageResult(status="test")
        assert result.errors == []
        assert result.warnings == []


class TestTemplateGenerationResult:
    """Test TemplateGenerationResult model."""

    def test_template_generation_result_creation(self):
        """Test creating a TemplateGenerationResult."""
        result = TemplateGenerationResult(
            status="completed",
            template_content='resource "azurerm_resource_group" {}',
            provider="azurerm",
            resources_count=5,
        )
        assert result.status == "completed"
        assert "azurerm_resource_group" in result.template_content
        assert result.provider == "azurerm"
        assert result.resources_count == 5

    def test_template_generation_result_defaults(self):
        """Test TemplateGenerationResult default values."""
        result = TemplateGenerationResult(status="test")
        assert result.template_content is None
        assert result.provider is None
        assert result.resources_count == 0


class TestInfrastructureStateDict:
    """Test InfrastructureStateDict TypedDict."""

    def test_infrastructure_state_dict_creation(self):
        """Test creating an InfrastructureStateDict."""
        state: InfrastructureStateDict = {
            "user_input": "Create a web app",
            "conversation_history": ["Hello", "Create web app"],
            "compliance_settings": {"enforce": True},
            "deployment_config": {"region": "eastus"},
            "current_stage": "template_generation",
            "completed_stages": ["requirements_analysis"],
            "phase_iterations": {"phase1": 1},
            "requirements_analysis_result": {"status": "completed"},
            "research_data_result": None,
            "template_generation_result": None,
            "compliance_validation_result": None,
            "template_validation_result": None,
            "cost_estimation_result": None,
            "approval_preparation_result": None,
            "final_template": None,
            "final_response": None,
            "errors": [],
            "warnings": [],
            "requires_approval": True,
            "approval_request_id": None,
            "current_agent": "cloud_architect",
            "workflow_phase": "analysis",
            "subscription_info": {"id": "123"},
            "needs_terraform_lookup": False,
            "needs_pricing_lookup": False,
            "approval_received": False,
            "cloud_architect_analysis": None,
            "cloud_engineer_response": None,
            "secops_finops_analysis": None,
            "terraform_guidance": None,
            "terraform_pricing_query": None,
            "devops_response": None,
            "deployment_status": None,
            "deployment_details": None,
            "resource_deployment_plan": None,
            "terraform_workspace": None,
            "terraform_consultant_caller": None,
        }

        assert state["user_input"] == "Create a web app"
        assert len(state["conversation_history"]) == 2
        assert state["current_stage"] == "template_generation"
        assert state["requires_approval"] is True

    def test_minimal_infrastructure_state_dict(self):
        """Test creating a minimal InfrastructureStateDict."""
        state: InfrastructureStateDict = {
            "user_input": "Test input",
            "conversation_history": None,
            "compliance_settings": None,
            "deployment_config": None,
            "current_stage": None,
            "completed_stages": [],
            "phase_iterations": None,
            "requirements_analysis_result": None,
            "research_data_result": None,
            "template_generation_result": None,
            "compliance_validation_result": None,
            "template_validation_result": None,
            "cost_estimation_result": None,
            "approval_preparation_result": None,
            "final_template": None,
            "final_response": None,
            "errors": [],
            "warnings": [],
            "requires_approval": False,
            "approval_request_id": None,
            "current_agent": None,
            "workflow_phase": None,
            "subscription_info": None,
            "needs_terraform_lookup": False,
            "needs_pricing_lookup": False,
            "approval_received": False,
            "cloud_architect_analysis": None,
            "cloud_engineer_response": None,
            "secops_finops_analysis": None,
            "terraform_guidance": None,
            "terraform_pricing_query": None,
            "devops_response": None,
            "deployment_status": None,
            "deployment_details": None,
            "resource_deployment_plan": None,
            "terraform_workspace": None,
            "terraform_consultant_caller": None,
        }

        assert state["user_input"] == "Test input"
        assert state["requires_approval"] is False
        assert state["errors"] == []
