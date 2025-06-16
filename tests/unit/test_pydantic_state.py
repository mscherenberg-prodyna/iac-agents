"""Unit tests for Pydantic state models."""

import pytest
from pydantic import ValidationError

from src.iac_agents.agents.state import (ComplianceSettings,
                                         ComplianceValidationResult,
                                         InfrastructureState,
                                         RequirementsAnalysisResult,
                                         StageResult, TemplateGenerationResult,
                                         WorkflowStage)


def test_compliance_settings_validation():
    """Test ComplianceSettings model validation."""
    # Valid settings
    settings = ComplianceSettings(
        enforce_compliance=True, selected_frameworks=["GDPR", "PCI DSS"]
    )
    assert settings.enforce_compliance is True
    assert "GDPR" in settings.selected_frameworks

    # Invalid framework
    with pytest.raises(ValidationError):
        ComplianceSettings(selected_frameworks=["INVALID_FRAMEWORK"])


def test_stage_result_validation():
    """Test StageResult model validation."""
    result = StageResult(
        status="completed", data={"key": "value"}, errors=[], warnings=[]
    )
    assert result.status == "completed"
    assert result.data["key"] == "value"


def test_requirements_analysis_result():
    """Test RequirementsAnalysisResult model."""
    result = RequirementsAnalysisResult(
        status="completed",
        requirements=["storage", "compute"],
        architecture_type="azure",
        estimated_complexity="medium",
    )
    assert len(result.requirements) == 2
    assert result.architecture_type == "azure"


def test_template_generation_result():
    """Test TemplateGenerationResult model."""
    result = TemplateGenerationResult(
        status="completed",
        template_content='resource "azurerm_storage_account" {}',
        provider="azure",
        resources_count=1,
    )
    assert "azurerm_storage_account" in result.template_content
    assert result.resources_count == 1


def test_compliance_validation_result():
    """Test ComplianceValidationResult model."""
    result = ComplianceValidationResult(
        status="completed",
        compliance_score=85.5,
        violations=["Warning: Missing encryption"],
        passed_checks=["Access control configured"],
    )
    assert result.compliance_score == 85.5
    assert len(result.violations) == 1
    assert len(result.passed_checks) == 1


def test_infrastructure_state_validation():
    """Test InfrastructureState model validation."""
    state = InfrastructureState(
        user_input="Create storage account",
        compliance_settings=ComplianceSettings(
            enforce_compliance=True, selected_frameworks=["GDPR"]
        ),
    )
    assert state.user_input == "Create storage account"
    assert state.compliance_settings.selected_frameworks == ["GDPR"]
    assert state.quality_gate_passed is False  # default
    assert state.compliance_score == 0.0  # default

    # Test validation methods
    state.add_error("Test error")
    assert "Test error" in state.errors

    state.add_warning("Test warning")
    assert "Test warning" in state.warnings

    state.complete_stage("requirements_analysis")
    assert state.is_stage_completed("requirements_analysis")
    assert not state.is_stage_completed("template_generation")


def test_infrastructure_state_stage_validation():
    """Test stage validation in InfrastructureState."""
    # Valid stages
    state = InfrastructureState(
        user_input="test",
        completed_stages=["requirements_analysis", "template_generation"],
        current_stage="validation_and_compliance",
    )
    assert len(state.completed_stages) == 2

    # Invalid current stage
    with pytest.raises(ValidationError):
        InfrastructureState(user_input="test", current_stage="invalid_stage")

    # Invalid completed stage
    with pytest.raises(ValidationError):
        InfrastructureState(user_input="test", completed_stages=["invalid_stage"])


def test_infrastructure_state_next_stage():
    """Test get_next_stage method."""
    state = InfrastructureState(
        user_input="test", completed_stages=["requirements_analysis"]
    )

    next_stage = state.get_next_stage()
    assert next_stage == "research_and_planning"

    # Complete all stages
    all_stages = [stage.value for stage in WorkflowStage]
    state = InfrastructureState(user_input="test", completed_stages=all_stages)

    next_stage = state.get_next_stage()
    assert next_stage is None


def test_infrastructure_state_required_fields():
    """Test required field validation."""
    # Missing user_input
    with pytest.raises(ValidationError):
        InfrastructureState()

    # Empty user_input
    with pytest.raises(ValidationError):
        InfrastructureState(user_input="")

    # Valid minimal state
    state = InfrastructureState(user_input="test")
    assert state.user_input == "test"
    assert state.completed_stages == []
    assert state.errors == []
    assert state.warnings == []


def test_compliance_score_bounds():
    """Test compliance score validation bounds."""
    # Valid scores
    state = InfrastructureState(user_input="test", compliance_score=0.0)
    assert state.compliance_score == 0.0

    state = InfrastructureState(user_input="test", compliance_score=100.0)
    assert state.compliance_score == 100.0

    # Invalid scores
    with pytest.raises(ValidationError):
        InfrastructureState(user_input="test", compliance_score=-1.0)

    with pytest.raises(ValidationError):
        InfrastructureState(user_input="test", compliance_score=101.0)


def test_pydantic_model_serialization():
    """Test Pydantic model serialization."""
    state = InfrastructureState(
        user_input="test request",
        compliance_settings=ComplianceSettings(
            enforce_compliance=True, selected_frameworks=["GDPR", "ISO 27001"]
        ),
        compliance_score=75.5,
        completed_stages=["requirements_analysis"],
        quality_gate_passed=True,
    )

    # Test model_dump
    data = state.model_dump()
    assert isinstance(data, dict)
    assert data["user_input"] == "test request"
    assert data["compliance_score"] == 75.5
    assert data["quality_gate_passed"] is True

    # Test nested model serialization
    compliance_data = data["compliance_settings"]
    assert compliance_data["enforce_compliance"] is True
    assert "GDPR" in compliance_data["selected_frameworks"]

    # Test round-trip serialization
    new_state = InfrastructureState(**data)
    assert new_state.user_input == state.user_input
    assert new_state.compliance_score == state.compliance_score
    assert (
        new_state.compliance_settings.selected_frameworks
        == state.compliance_settings.selected_frameworks
    )
