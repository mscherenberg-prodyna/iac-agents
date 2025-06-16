"""Response compiler for LangGraph workflow."""

from ..logging_system import log_agent_complete, log_agent_start
from .state import InfrastructureStateDict


def compile_final_response(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Compile the final response to the user."""
    log_agent_start("Response Compiler", "Compiling final response")

    # Check if validation was performed and quality gates passed
    quality_gate_passed = state.get("quality_gate_passed", False)
    compliance_score = state.get("compliance_score", 0)

    response_parts = []

    # Add template with appropriate quality indicators
    template = state.get("final_template", "")
    if template:
        if quality_gate_passed:
            response_parts.append(
                f"## 🏗️ Production-Ready Infrastructure Template\n\n```hcl\n{template}\n```\n"
            )
        else:
            response_parts.append(
                f"## ⚠️ Infrastructure Template (Compliance Review Needed)\n\n```hcl\n{template}\n```\n"
            )

    # Add validation results with appropriate status
    compliance_validation = state.get("compliance_validation_result", {})
    if compliance_validation:
        violations_count = len(state.get("violations_found", []))

        if quality_gate_passed:
            response_parts.append("## ✅ Quality Validation Passed\n\n")
            response_parts.append(f"**Compliance Score:** {compliance_score:.1f}% ✅\n")
            response_parts.append(f"**Security Violations:** {violations_count} (within acceptable limits)\n")
            response_parts.append("**Quality Gate:** PASSED ✅\n\n")
        else:
            response_parts.append("## ⚠️ Compliance Review Required\n\n")
            response_parts.append(f"**Compliance Score:** {compliance_score:.1f}% ⚠️\n")
            response_parts.append(f"**Security Violations:** {violations_count} (requires attention)\n")
            response_parts.append("**Quality Gate:** REVIEW NEEDED ⚠️\n\n")

            # Add specific violation details for low-compliance templates
            violations = state.get("violations_found", [])
            if violations:
                response_parts.append("**Key Compliance Issues:**\n")
                for i, violation in enumerate(violations[:3]):  # Show top 3 violations
                    response_parts.append(f"{i + 1}. {violation}\n")
                if len(violations) > 3:
                    response_parts.append(f"   ... and {len(violations) - 3} more issues\n")
                response_parts.append("\n")

        # Add framework compliance details
        validation_frameworks = compliance_validation.get("validation_frameworks", [])
        if validation_frameworks:
            frameworks = ", ".join(validation_frameworks)
            response_parts.append(f"**Validated Frameworks:** {frameworks}\n\n")

    # Add cost estimation
    cost_estimation = state.get("cost_estimation_result", {})
    if cost_estimation and "error" not in cost_estimation:
        cost_data = cost_estimation.get("cost_estimate", {})
        if cost_data:
            cost_summary = cost_data.get("summary", "Cost analysis completed")
            response_parts.append(f"## 💰 Cost Estimate\n\n{cost_summary}\n")

    # Add approval information with appropriate status
    approval_preparation = state.get("approval_preparation_result", {})
    if approval_preparation and "error" not in approval_preparation:
        approval_summary = approval_preparation.get("approval_summary", "")
        if quality_gate_passed:
            response_parts.append("## ⚖️ Ready for Approval\n\n")
            response_parts.append(
                "✅ **Template Quality Verified** - Ready for production deployment consideration\n\n"
            )
        else:
            response_parts.append("## ⚖️ Approval Required (with Compliance Review)\n\n")
            response_parts.append(
                "⚠️ **Additional Review Needed** - Template requires compliance assessment before deployment\n\n"
            )
        response_parts.append(f"{approval_summary}\n")

    # Add workflow summary with appropriate quality metrics
    completed_stages = len(state.get("completed_stages", []))
    workflow_plan = state.get("workflow_plan", {})
    total_stages = len(workflow_plan.get("stages", [])) if workflow_plan else 0
    errors_count = len(state.get("errors", []))

    response_parts.append("## 📊 Workflow Summary\n\n")
    response_parts.append(f"- **Stages Completed:** {completed_stages}/{total_stages} ✅\n")

    if quality_gate_passed:
        response_parts.append("- **Quality Gate Status:** PASSED ✅\n")
        response_parts.append("- **Ready for Production:** ✅ YES\n")
    else:
        response_parts.append("- **Quality Gate Status:** REVIEW NEEDED ⚠️\n")
        response_parts.append("- **Ready for Production:** ⚠️ REQUIRES COMPLIANCE REVIEW\n")

    response_parts.append(f"- **Issues Found:** {errors_count}\n")

    if workflow_plan:
        complexity_score = workflow_plan.get("complexity_score", 0)
        response_parts.append(f"- **Estimated Complexity:** {complexity_score}/10\n")

    # Add appropriate next steps based on quality gate status
    response_parts.append("\n## 🚀 Next Steps\n\n")
    if quality_gate_passed:
        response_parts.append("1. ✅ **Template Quality Verified** - Meets enterprise security standards\n")
        response_parts.append("2. 🔍 **Review Deployment Plan** - Verify resources match requirements\n")
        response_parts.append("3. 🧪 **Test in Development** - Deploy to development environment first\n")
        response_parts.append("4. ⚖️ **Submit for Approval** - Ready for stakeholder review\n")
        response_parts.append("5. 🚀 **Deploy to Production** - Execute deployment after approval\n")
    else:
        response_parts.append("1. ⚠️ **Review Compliance Issues** - Address security violations listed above\n")
        response_parts.append("2. 🔍 **Security Assessment** - Have security team review template\n")
        response_parts.append("3. 🧪 **Test in Development** - Deploy to development environment first\n")
        response_parts.append("4. 🔧 **Template Enhancement** - Consider implementing recommended security measures\n")
        response_parts.append("5. ⚖️ **Submit for Review** - Requires additional approval due to compliance gaps\n")

    final_response = "\n".join(response_parts)

    log_agent_complete(
        "Response Compiler",
        "Final response compiled",
        {
            "quality_gate_passed": quality_gate_passed,
            "compliance_score": compliance_score,
        },
    )

    return {
        **state,
        "final_response": final_response,
    }