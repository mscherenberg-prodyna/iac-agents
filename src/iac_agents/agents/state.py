"""LangGraph state schema for Infrastructure as Code workflow."""

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field


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


class StageResult(BaseModel):
    """Base model for stage results."""

    status: str = Field(..., description="Status of the stage")
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    timestamp: Optional[str] = None


class TemplateGenerationResult(StageResult):
    """Template generation stage result."""

    template_content: Optional[str] = None
    provider: Optional[str] = None
    resources_count: int = 0


class InfrastructureStateDict(TypedDict):
    """TypedDict version for LangGraph workflow compatibility."""

    # Input
    user_input: str
    conversation_history: Optional[List[str]]
    compliance_settings: Optional[Dict[str, Any]]
    deployment_config: Optional[Dict[str, Any]]

    # Workflow tracking
    current_stage: Optional[str]
    completed_stages: List[str]
    phase_iterations: Optional[Dict[str, int]]

    # Stage results (as dicts for LangGraph compatibility)
    requirements_analysis_result: Optional[Dict[str, Any]]
    research_data_result: Optional[Dict[str, Any]]
    template_generation_result: Optional[Dict[str, Any]]
    compliance_validation_result: Optional[Dict[str, Any]]
    cost_estimation_result: Optional[Dict[str, Any]]
    approval_preparation_result: Optional[Dict[str, Any]]

    # Final output
    final_template: Optional[str]
    final_response: Optional[str]

    # Error handling
    errors: List[str]
    warnings: List[str]

    # Human interaction
    requires_approval: bool
    approval_request_id: Optional[str]

    # Additional workflow fields
    current_agent: Optional[str]
    workflow_phase: Optional[str]
    subscription_info: Optional[Dict[str, Any]]
    needs_terraform_lookup: bool
    needs_pricing_lookup: bool
    approval_received: bool
    cloud_architect_analysis: Optional[str]
    cloud_engineer_response: Optional[str]
    secops_finops_analysis: Optional[str]
    terraform_guidance: Optional[str]
    terraform_pricing_query: Optional[str]
    devops_response: Optional[str]
    deployment_status: Optional[str]
    deployment_details: Optional[Dict[str, Any]]
    resource_deployment_plan: Optional[List[str]]
    terraform_workspace: Optional[str]
    terraform_consultant_caller: Optional[str]
