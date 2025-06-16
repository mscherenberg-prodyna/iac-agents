"""Requirements analysis node for LangGraph workflow."""

from typing import Any, Dict, List

from ...logging_system import log_agent_complete, log_agent_start
from ..state import InfrastructureStateDict, WorkflowStage


def requirements_analysis_node(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Analyze user requirements and create workflow plan."""
    log_agent_start("Requirements Analysis Node", "Analyzing requirements")
    
    # LangGraph always passes state as dict
    user_input = state["user_input"]
    completed_stages = state.get("completed_stages", [])
    
    # Extract key information from requirements
    extracted_info = {
        "cloud_provider": "azure",
        "estimated_complexity": _estimate_complexity(user_input),
        "compliance_requirements": _extract_compliance_requirements(user_input),
        "key_components": _extract_components(user_input),
    }
    
    # Determine workflow stages based on complexity
    workflow_plan = {
        "stages": _determine_workflow_stages(extracted_info),
        "requirements": user_input,
        "complexity_score": extracted_info["estimated_complexity"],
    }
    
    # Create proper RequirementsAnalysisResult
    from ..state import RequirementsAnalysisResult
    analysis_result = RequirementsAnalysisResult(
        status="completed",
        data=extracted_info,
        requirements=extracted_info.get("key_components", []),
        architecture_type=extracted_info["cloud_provider"],
        estimated_complexity=str(extracted_info["estimated_complexity"])
    )
    
    log_agent_complete(
        "Requirements Analysis Node", 
        "Requirements analyzed", 
        extracted_info
    )
    
    # Update completed stages
    new_completed_stages = completed_stages.copy() if completed_stages else []
    if WorkflowStage.REQUIREMENTS_ANALYSIS.value not in new_completed_stages:
        new_completed_stages.append(WorkflowStage.REQUIREMENTS_ANALYSIS.value)
    
    return {
        **state,
        "current_stage": WorkflowStage.REQUIREMENTS_ANALYSIS.value,
        "completed_stages": new_completed_stages,
        "requirements_analysis_result": analysis_result.model_dump(),
        "workflow_plan": workflow_plan,
    }


def _estimate_complexity(user_input: str) -> int:
    """Estimate complexity score from user input."""
    complexity_keywords = {
        "simple": 1, "basic": 2, "standard": 3, "complex": 5,
        "enterprise": 7, "scalable": 6, "secure": 4, "compliant": 5,
        "high availability": 7, "disaster recovery": 8, "multi-region": 9
    }
    
    user_lower = user_input.lower()
    scores = [score for keyword, score in complexity_keywords.items() if keyword in user_lower]
    
    return max(scores) if scores else 3


def _extract_compliance_requirements(user_input: str) -> List[str]:
    """Extract compliance requirements from user input."""
    compliance_keywords = {
        "legal": ["ISO 27001", "GDPR"],
        "financial": ["SOX", "PCI DSS"],
        "healthcare": ["HIPAA"],
        "compliant": ["GDPR", "ISO 27001"],
        "secure": ["ISO 27001", "SOC 2"],
    }
    
    user_lower = user_input.lower()
    requirements = set()
    
    for keyword, frameworks in compliance_keywords.items():
        if keyword in user_lower:
            requirements.update(frameworks)
    
    return list(requirements) if requirements else ["GDPR"]


def _extract_components(user_input: str) -> List[str]:
    """Extract key infrastructure components from user input."""
    components = []
    
    component_keywords = {
        "web application": ["web app", "frontend", "website"],
        "database": ["database", "db", "sql", "cosmos"],
        "storage": ["storage", "blob", "file", "archive", "document"],
        "compute": ["vm", "virtual machine", "compute", "container"],
        "networking": ["network", "vpc", "subnet", "load balancer"],
        "security": ["firewall", "waf", "security", "key vault"],
    }
    
    user_input_lower = user_input.lower()
    
    for component, keywords in component_keywords.items():
        if any(keyword in user_input_lower for keyword in keywords):
            components.append(component)
    
    return components


def _determine_workflow_stages(analysis: Dict[str, Any]) -> List[str]:
    """Determine workflow stages based on analysis."""
    complexity = analysis.get("estimated_complexity", 5)
    compliance_frameworks = analysis.get("compliance_requirements", [])
    
    stages = [WorkflowStage.REQUIREMENTS_ANALYSIS.value]
    
    if complexity >= 7 or len(compliance_frameworks) > 2:
        stages.append(WorkflowStage.RESEARCH_AND_PLANNING.value)
    
    stages.extend([
        WorkflowStage.TEMPLATE_GENERATION.value,
        WorkflowStage.VALIDATION_AND_COMPLIANCE.value
    ])
    
    if complexity >= 5:
        stages.append(WorkflowStage.COST_ESTIMATION.value)
    
    stages.extend([
        WorkflowStage.APPROVAL_PREPARATION.value,
        WorkflowStage.COMPLETED.value
    ])
    
    return stages