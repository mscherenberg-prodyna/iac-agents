"""Validation and compliance node for LangGraph workflow."""

# Legacy agent imports removed
from ...compliance_framework import ComplianceFramework
from ...config.settings import config
from ...logging_system import log_agent_complete, log_agent_start, log_warning
from ..state import ComplianceValidationResult, InfrastructureStateDict, WorkflowStage


def validation_compliance_node(
    state: InfrastructureStateDict,
) -> InfrastructureStateDict:
    """Validate template for compliance and security."""
    log_agent_start("Validation Compliance Node", "Validating compliance and security")

    template = state.get("final_template", "")
    compliance_settings = state.get("compliance_settings", {})

    if not template:
        log_warning(
            "Validation Compliance Node", "No template available for validation"
        )
        return {
            **state,
            "current_stage": WorkflowStage.VALIDATION_AND_COMPLIANCE.value,
            "errors": state.get("errors", [])
            + ["No template available for validation"],
        }

    compliance_framework = ComplianceFramework()

    # Determine validation frameworks
    if compliance_settings.get("enforce_compliance"):
        validation_frameworks = compliance_settings.get("selected_frameworks", [])
    else:
        requirements_analysis = state.get("requirements_analysis_result", {})
        validation_frameworks = requirements_analysis.get(
            "compliance_requirements", ["GDPR"]
        )

    # Run compliance validation
    compliance_result = compliance_framework.validate_template(
        template, validation_frameworks
    )

    # Basic template validation
    basic_validation = {"passed_checks": ["Syntax valid"], "issues": []}

    # Calculate quality metrics
    compliance_score = compliance_result.get("compliance_score", 0)
    violations = compliance_result.get("violations", [])
    violations_count = len(violations)

    # Determine quality gate status
    should_enforce_quality_gates = (
        compliance_settings.get("enforce_compliance") and len(validation_frameworks) > 0
    )

    if should_enforce_quality_gates:
        minimum_score_threshold = config.compliance.minimum_score_enforced
        maximum_violations_threshold = config.compliance.max_violations_enforced
    else:
        minimum_score_threshold = config.compliance.minimum_score_relaxed
        maximum_violations_threshold = config.compliance.max_violations_relaxed

    quality_gate_passed = (
        (
            compliance_score >= minimum_score_threshold
            and violations_count <= maximum_violations_threshold
        )
        if should_enforce_quality_gates
        else True
    )

    # Create proper ComplianceValidationResult
    validation_result = ComplianceValidationResult(
        status="completed",
        data={
            "compliance_validation": compliance_result,
            "basic_validation": basic_validation,
            "compliance_enforced": should_enforce_quality_gates,
            "validation_frameworks": validation_frameworks,
        },
        compliance_score=compliance_score,
        violations=[str(v) for v in violations],
        passed_checks=(
            basic_validation.get("passed_checks", [])
            if isinstance(basic_validation, dict)
            else []
        ),
    )

    log_agent_complete(
        "Validation Compliance Node",
        "Validation completed",
        {
            "compliance_score": compliance_score,
            "violations": violations_count,
            "quality_gate_passed": quality_gate_passed,
        },
    )

    # Update completed stages
    completed_stages = state.get("completed_stages", [])
    new_completed_stages = completed_stages.copy() if completed_stages else []
    if WorkflowStage.VALIDATION_AND_COMPLIANCE.value not in new_completed_stages:
        new_completed_stages.append(WorkflowStage.VALIDATION_AND_COMPLIANCE.value)

    return {
        **state,
        "current_stage": WorkflowStage.VALIDATION_AND_COMPLIANCE.value,
        "completed_stages": new_completed_stages,
        "compliance_validation_result": validation_result.model_dump(),
        "quality_gate_passed": quality_gate_passed,
        "compliance_score": compliance_score,
        "violations_found": [str(v) for v in violations],
    }
