"""Cloud Engineer Agent node for LangGraph workflow."""

from ...logging_system import log_agent_complete, log_agent_start, log_warning, log_agent_response
from ...templates.template_manager import template_manager
from ..state import InfrastructureStateDict, TemplateGenerationResult, WorkflowStage
from ..utils import (
    add_error_to_state,
    extract_terraform_template,
    make_llm_call,
    mark_stage_completed,
)


def cloud_engineer_agent(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Generate infrastructure templates based on Cloud Architect requirements."""
    log_agent_start(
        "Cloud Engineer", "Processing requirements and generating templates"
    )

    # Get inputs from Cloud Architect analysis, not raw user input
    architect_analysis = state.get("cloud_architect_analysis", "")
    user_input = state["user_input"]  # For context only

    try:
        # Check if terraform research is enabled
        deployment_config = state.get("deployment_config", {})
        terraform_enabled = deployment_config.get("terraform_research_enabled", True)
        
        # Load the cloud engineer prompt with Cloud Architect's analysis
        system_prompt = template_manager.get_prompt(
            "cloud_engineer",
            user_request=user_input,
            architect_analysis=architect_analysis or "No architect analysis available",
            current_stage=state.get("current_stage", "template_generation"),
            terraform_consultant_available=terraform_enabled,
        )

        # Make LLM call with architect's analysis as primary input
        response = make_llm_call(system_prompt, architect_analysis or user_input)

        # Extract Terraform template (needed for deployment)
        template_content = extract_terraform_template(response)
        
        # Simple consultation detection - let LLM be explicit
        needs_terraform_consultation = "TERRAFORM_CONSULTATION_NEEDED" in response
        
        # Create result with extracted template
        result = TemplateGenerationResult(
            status="completed",
            data={
                "full_response": response,
                "has_template": bool(template_content),
                "needs_terraform_consultation": needs_terraform_consultation,
            },
            template_content=template_content,
            provider="azure" if template_content else None,
            resources_count=template_content.count("resource ") if template_content else 0,
        )

        # Mark stage as completed
        new_completed_stages = mark_stage_completed(
            state, WorkflowStage.TEMPLATE_GENERATION.value
        )

        # Log the response content for debugging
        log_agent_response("Cloud Engineer", response)
        
        log_agent_complete(
            "Cloud Engineer",
            f"Response generated {'with template' if template_content else 'without template'}, "
            f"consultation {'required' if needs_terraform_consultation else 'not required'}",
        )

        # Determine if we need Terraform consultation
        needs_terraform_lookup = needs_terraform_consultation

        # If consultation is needed, prepare specific query for Terraform Consultant
        terraform_query = ""
        if needs_terraform_lookup:
            terraform_query = f"""
Cloud Engineer needs Terraform guidance for the following request:

Original Request: {user_input}
Cloud Architect Analysis: {architect_analysis}

Specific areas where guidance is needed:
{response}

Please provide best practices, latest resource configurations, and any optimization recommendations.
"""

        result_state = {
            **state,
            "current_stage": WorkflowStage.TEMPLATE_GENERATION.value,
            "completed_stages": new_completed_stages,
            "template_generation_result": result.model_dump(),
            "final_template": template_content,
            "cloud_engineer_response": terraform_query if needs_terraform_lookup else response,
            "needs_terraform_lookup": needs_terraform_lookup,
        }
        
        # Set caller info if requesting Terraform consultation
        if needs_terraform_lookup:
            result_state["terraform_consultant_caller"] = "cloud_engineer"
            
        return result_state

    except Exception as e:
        log_warning("Cloud Engineer", f"Template generation failed: {str(e)}")

        # Update errors
        new_errors = add_error_to_state(state, f"Cloud Engineer failed: {str(e)}")

        return {
            **state,
            "current_stage": WorkflowStage.TEMPLATE_GENERATION.value,
            "errors": new_errors,
        }


def _extract_template_from_response(response: str) -> str:
    """Extract Terraform template from agent response."""
    if not response:
        return ""

    # Find all HCL code blocks and choose the best one
    all_code_blocks = []

    # Find all HCL code blocks
    hcl_start = 0
    while True:
        hcl_start = response.find("```hcl", hcl_start)
        if hcl_start == -1:
            break

        content_start = hcl_start + 6
        content_end = response.find("```", content_start)

        if content_end > content_start:
            content = response[content_start:content_end].strip()
            all_code_blocks.append(("hcl", content))

        hcl_start = content_end + 3 if content_end != -1 else len(response)

    # Find generic code blocks if no HCL blocks or HCL blocks are invalid
    if not all_code_blocks:
        generic_start = 0
        while True:
            generic_start = response.find("```", generic_start)
            if generic_start == -1:
                break

            # Skip if it's a specific language block
            if response[generic_start : generic_start + 10].startswith(
                ("```hcl", "```terraform", "```python", "```bash")
            ):
                generic_start += 3
                continue

            content_start = generic_start + 3
            content_end = response.find("```", content_start)

            if content_end > content_start:
                content = response[content_start:content_end].strip()
                all_code_blocks.append(("generic", content))

            generic_start = content_end + 3 if content_end != -1 else len(response)

    # Evaluate all code blocks and choose the best one
    best_template = None
    best_score = 0

    for _, content in all_code_blocks:
        if _is_valid_terraform_content(content):
            # Score based on content quality
            score = len(content)  # Longer templates generally better
            if "terraform" in content.lower():
                score += 100
            if "provider" in content.lower():
                score += 50
            if "resource" in content.lower():
                score += 50

            if score > best_score:
                best_score = score
                best_template = content

    if best_template:
        return best_template

    # Look for direct terraform resources
    if "resource " in response:
        lines = response.split("\n")
        template_lines = []
        in_template = False

        for line in lines:
            if any(
                keyword in line
                for keyword in [
                    "terraform {",
                    "provider ",
                    "resource ",
                    "variable ",
                    "output ",
                ]
            ):
                in_template = True

            if in_template:
                template_lines.append(line)

        if template_lines:
            return "\n".join(template_lines).strip()

    return ""


def _is_valid_terraform_content(content: str) -> bool:
    """Check if content looks like actual Terraform code."""
    content_lower = content.lower()

    terraform_keywords = ["terraform", "provider", "resource", "variable", "output"]
    has_terraform_keywords = any(
        keyword in content_lower for keyword in terraform_keywords
    )
    has_hcl_syntax = any(char in content for char in ["{", "}", "="])

    return has_terraform_keywords and has_hcl_syntax


