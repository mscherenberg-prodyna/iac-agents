"""LangGraph state schema for Infrastructure as Code workflow."""

from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


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


class InfrastructureStateDict(TypedDict):
    """TypedDict version for LangGraph workflow compatibility."""

    # Input
    user_input: str
    conversation_history: Optional[List[str]]
    compliance_settings: Optional[Dict[str, Any]]
    deployment_config: Optional[Dict[str, Any]]

    # Workflow tracking
    current_stage: Optional[str]
    architect_target: Optional[str]

    # Agent IDs for Cloud Agents
    terraform_consultant_id: Optional[str]

    # Final output
    final_template: Optional[str]

    # Error handling
    errors: List[str]
    warnings: List[str]

    # Human interaction
    requires_approval: bool
    approval_received: bool

    # Additional workflow fields
    current_agent: Optional[str]
    subscription_info: Optional[Dict[str, Any]]
    needs_terraform_lookup: bool
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
