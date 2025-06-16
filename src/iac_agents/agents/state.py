"""LangGraph state schema for Infrastructure as Code workflow."""

from typing import Any, Dict, List, Optional, TypedDict
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class WorkflowStage(Enum):
    """Stages of the infrastructure deployment workflow."""
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    RESEARCH_AND_PLANNING = "research_and_planning"
    TEMPLATE_GENERATION = "template_generation"
    VALIDATION_AND_COMPLIANCE = "validation_and_compliance"
    COST_ESTIMATION = "cost_estimation"
    APPROVAL_PREPARATION = "approval_preparation"
    TEMPLATE_REFINEMENT = "template_refinement"
    COMPLETED = "completed"


class ComplianceSettings(BaseModel):
    """Compliance settings validation model."""
    enforce_compliance: bool = True
    selected_frameworks: List[str] = Field(default_factory=list)
    custom_rules: Optional[Dict[str, Any]] = None
    
    @field_validator('selected_frameworks')
    @classmethod
    def validate_frameworks(cls, v):
        valid_frameworks = ['GDPR', 'PCI DSS', 'HIPAA', 'SOX', 'ISO 27001']
        invalid = [f for f in v if f not in valid_frameworks]
        if invalid:
            raise ValueError(f"Invalid compliance frameworks: {invalid}")
        return v


class StageResult(BaseModel):
    """Base model for stage results."""
    status: str = Field(..., description="Status of the stage")
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    timestamp: Optional[str] = None


class RequirementsAnalysisResult(StageResult):
    """Requirements analysis stage result."""
    requirements: List[str] = Field(default_factory=list)
    architecture_type: Optional[str] = None
    estimated_complexity: Optional[str] = None


class TemplateGenerationResult(StageResult):
    """Template generation stage result."""
    template_content: Optional[str] = None
    provider: Optional[str] = None
    resources_count: int = 0


class ComplianceValidationResult(StageResult):
    """Compliance validation stage result."""
    compliance_score: float = Field(ge=0.0, le=100.0, default=0.0)
    violations: List[str] = Field(default_factory=list)
    passed_checks: List[str] = Field(default_factory=list)


class InfrastructureState(BaseModel):
    """State schema for the infrastructure deployment workflow with Pydantic validation."""
    
    # Input
    user_input: str = Field(..., min_length=1, description="User's infrastructure request")
    compliance_settings: Optional[ComplianceSettings] = None
    
    # Workflow tracking
    current_stage: Optional[str] = None
    completed_stages: List[str] = Field(default_factory=list)
    workflow_plan: Optional[Dict[str, Any]] = None
    
    # Stage results with proper typing
    requirements_analysis_result: Optional[RequirementsAnalysisResult] = None
    research_data_result: Optional[StageResult] = None
    template_generation_result: Optional[TemplateGenerationResult] = None
    compliance_validation_result: Optional[ComplianceValidationResult] = None
    cost_estimation_result: Optional[StageResult] = None
    approval_preparation_result: Optional[StageResult] = None
    
    # Quality control
    quality_gate_passed: bool = False
    compliance_score: float = Field(ge=0.0, le=100.0, default=0.0)
    violations_found: List[str] = Field(default_factory=list)
    
    # Final output
    final_template: Optional[str] = None
    final_response: Optional[str] = None
    
    # Error handling
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Human interaction
    requires_approval: bool = False
    approval_request_id: Optional[str] = None
    human_feedback: Optional[str] = None
    
    @field_validator('completed_stages')
    @classmethod
    def validate_completed_stages(cls, v):
        """Ensure completed stages are valid workflow stages."""
        valid_stages = [stage.value for stage in WorkflowStage]
        invalid = [stage for stage in v if stage not in valid_stages]
        if invalid:
            raise ValueError(f"Invalid workflow stages: {invalid}")
        return v
    
    @field_validator('current_stage')
    @classmethod
    def validate_current_stage(cls, v):
        """Ensure current stage is a valid workflow stage."""
        if v is not None:
            valid_stages = [stage.value for stage in WorkflowStage]
            if v not in valid_stages:
                raise ValueError(f"Invalid current stage: {v}")
        return v
    
    def add_error(self, error: str) -> None:
        """Add an error to the state."""
        if error not in self.errors:
            self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the state."""
        if warning not in self.warnings:
            self.warnings.append(warning)
    
    def complete_stage(self, stage: str) -> None:
        """Mark a stage as completed."""
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
    
    def is_stage_completed(self, stage: str) -> bool:
        """Check if a stage has been completed."""
        return stage in self.completed_stages
    
    def get_next_stage(self) -> Optional[str]:
        """Get the next stage to execute based on current progress."""
        all_stages = [stage.value for stage in WorkflowStage]
        for stage in all_stages:
            if not self.is_stage_completed(stage):
                return stage
        return None
    
    model_config = {
        "use_enum_values": True,
        "validate_assignment": True,
        "extra": "forbid"
    }


class InfrastructureStateDict(TypedDict):
    """TypedDict version for LangGraph workflow compatibility."""
    
    # Input
    user_input: str
    compliance_settings: Optional[Dict[str, Any]]
    
    # Workflow tracking
    current_stage: Optional[str]
    completed_stages: List[str]
    workflow_plan: Optional[Dict[str, Any]]
    
    # Stage results (as dicts for LangGraph compatibility)
    requirements_analysis_result: Optional[Dict[str, Any]]
    research_data_result: Optional[Dict[str, Any]]
    template_generation_result: Optional[Dict[str, Any]]
    compliance_validation_result: Optional[Dict[str, Any]]
    cost_estimation_result: Optional[Dict[str, Any]]
    approval_preparation_result: Optional[Dict[str, Any]]
    
    # Quality control
    quality_gate_passed: bool
    compliance_score: float
    violations_found: List[str]
    
    # Final output
    final_template: Optional[str]
    final_response: Optional[str]
    
    # Error handling
    errors: List[str]
    warnings: List[str]
    
    # Human interaction
    requires_approval: bool
    approval_request_id: Optional[str]
    human_feedback: Optional[str]