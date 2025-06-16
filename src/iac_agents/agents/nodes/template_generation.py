"""Template generation node for LangGraph workflow."""

# Legacy agent imports removed
from ...logging_system import log_agent_complete, log_agent_start, log_warning
from ...templates.template_manager import template_manager
from ..state import InfrastructureStateDict, WorkflowStage


def template_generation_node(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Generate Terraform template."""
    log_agent_start("Template Generation Node", "Generating infrastructure template")

    # LangGraph always passes state as dict
    user_input = state["user_input"]
    completed_stages = state.get("completed_stages", [])
    errors = state.get("errors", [])

    try:
        # Generate template using template manager instead of legacy agent
        template = template_manager.get_fallback_template(user_input)
        template_response = (
            f"Generated template for: {user_input}\n\n```hcl\n{template}\n```"
        )

        if not template:
            log_warning(
                "Template Generation Node", "No template extracted, using fallback"
            )
            template = template_manager.get_fallback_template(user_input)

        # Create proper TemplateGenerationResult
        from ..state import TemplateGenerationResult

        result = TemplateGenerationResult(
            status="completed",
            data={
                "full_response": template_response,
                "extraction_method": (
                    "hcl_blocks" if "```hcl" in template_response else "fallback"
                ),
            },
            template_content=template,
            provider="azure",
            resources_count=template.count("resource ") if template else 0,
        )

        log_agent_complete(
            "Template Generation Node",
            "Template generated",
            {"template_lines": len(template.split("\n")) if template else 0},
        )

        # Update completed stages
        new_completed_stages = completed_stages.copy() if completed_stages else []
        if WorkflowStage.TEMPLATE_GENERATION.value not in new_completed_stages:
            new_completed_stages.append(WorkflowStage.TEMPLATE_GENERATION.value)

        return {
            **state,
            "current_stage": WorkflowStage.TEMPLATE_GENERATION.value,
            "completed_stages": new_completed_stages,
            "template_generation_result": result.model_dump(),
            "final_template": template,
        }

    except Exception as e:
        log_warning("Template Generation Node", f"Template generation failed: {str(e)}")

        # Update errors
        new_errors = errors.copy() if errors else []
        error_msg = f"Template generation failed: {str(e)}"
        if error_msg not in new_errors:
            new_errors.append(error_msg)

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
