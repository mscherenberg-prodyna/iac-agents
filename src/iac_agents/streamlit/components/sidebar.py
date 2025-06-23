"""Sidebar components for the Streamlit interface."""

from typing import Any, Dict, List, Optional

import streamlit as st

from ...config.settings import config
from ...templates.ui_loader import ui_loader


def _display_recent_activity(recent_logs: List[Any]):
    """Display recent activity logs in sidebar."""
    st.sidebar.markdown("### 📊 Recent Activity")

    if recent_logs:
        with st.sidebar.container():
            for log in recent_logs[-config.ui.activity_log_entries :]:
                timestamp = log.timestamp.strftime("%H:%M:%S")
                activity_snippet = log.activity[:50] + (
                    "..." if len(log.activity) > 50 else ""
                )

                # Use emoji for different log levels
                level_emoji = "ℹ️"
                if hasattr(log, "level"):
                    level_str = (
                        str(log.level).rsplit(".", maxsplit=1)[-1]
                        if hasattr(log, "level")
                        else "INFO"
                    )
                    level_emoji = {
                        "AGENT_START": "🚀",
                        "AGENT_COMPLETE": "✅",
                        "USER_UPDATE": "💬",
                        "INFO": "ℹ️",
                        "WARNING": "⚠️",
                        "ERROR": "❌",
                    }.get(level_str, "ℹ️")

                st.sidebar.markdown(
                    ui_loader.format_activity_entry(
                        timestamp, log.agent_name, f"{level_emoji} {activity_snippet}"
                    ),
                    unsafe_allow_html=True,
                )
    else:
        st.sidebar.info("No recent activity to display")


def display_agent_monitoring(state: Dict[str, Any]):
    """Display real-time agent monitoring information."""
    st.sidebar.markdown("### 🤖 Agent Monitoring")
    
    # Current Agent Status
    current_agent = state.get("current_agent", "None")
    workflow_phase = state.get("workflow_phase", "idle")
    
    st.sidebar.markdown("**Current Status:**")
    st.sidebar.markdown(f"🔄 **Agent:** {current_agent}")
    st.sidebar.markdown(f"📋 **Phase:** {workflow_phase}")
    
    # Workflow Progress
    completed_stages = state.get("completed_stages", [])
    if completed_stages:
        st.sidebar.markdown("**Completed Stages:**")
        for stage in completed_stages:
            st.sidebar.markdown(f"✅ {stage}")
    
    # Error Status
    errors = state.get("errors", [])
    if errors:
        st.sidebar.markdown(f"⚠️ **Errors:** {len(errors)}")
        with st.sidebar.expander("View Errors"):
            for error in errors[-3:]:  # Show last 3 errors
                st.error(error)
    
    # Agent Flags
    flags = []
    if state.get("needs_terraform_lookup"):
        flags.append("🔍 Terraform consultation needed")
    if state.get("needs_pricing_lookup"):
        flags.append("💰 Pricing lookup needed")
    if state.get("requires_approval"):
        flags.append("👤 Human approval required")
    
    if flags:
        st.sidebar.markdown("**Active Flags:**")
        for flag in flags:
            st.sidebar.markdown(f"• {flag}")


def display_deployment_plan(state: Dict[str, Any]):
    """Display current resource deployment plan."""
    st.sidebar.markdown("### 📋 Deployment Plan")
    
    # Check for Terraform template in cloud engineer response
    terraform_template = state.get("final_template")
    cloud_engineer_response = state.get("cloud_engineer_response", "")
    
    # Extract resources from template or response
    resources = _extract_resource_list(terraform_template, cloud_engineer_response)
    
    if resources:
        st.sidebar.markdown("**Planned Resources:**")
        for resource in resources:
            st.sidebar.markdown(f"• {resource}")
    else:
        st.sidebar.info("No deployment plan available yet")
    
    # Show deployment status if available
    deployment_status = state.get("deployment_status")
    if deployment_status:
        status_emoji = {
            "planned": "📋",
            "in_progress": "⚙️", 
            "completed": "✅",
            "failed": "❌"
        }.get(deployment_status.lower(), "📋")
        st.sidebar.markdown(f"**Status:** {status_emoji} {deployment_status}")


def display_cost_estimation(state: Dict[str, Any]):
    """Extract and display cost estimation from SecOps/FinOps analysis."""
    secops_analysis = state.get("secops_finops_analysis", "")
    cost_result = state.get("cost_estimation_result")
    
    if not secops_analysis and not cost_result:
        return
        
    st.sidebar.markdown("### 💰 Cost Estimation")
    
    # Extract cost information from SecOps/FinOps analysis
    monthly_cost = _extract_monthly_cost(secops_analysis, cost_result)
    if monthly_cost:
        st.sidebar.markdown(f"**Estimated Monthly Cost:** ${monthly_cost}")
    
    # Extract resource costs
    resource_costs = _extract_resource_costs(secops_analysis, cost_result)
    if resource_costs:
        st.sidebar.markdown("**Cost Breakdown:**")
        for resource, cost in resource_costs.items():
            st.sidebar.markdown(f"• {resource}: ${cost}")
    
    # Extract optimization tips
    optimization_tips = _extract_optimization_tips(secops_analysis)
    if optimization_tips:
        with st.sidebar.expander("💡 Cost Optimization"):
            for tip in optimization_tips:
                st.markdown(f"• {tip}")


def _extract_resource_list(terraform_template: str, cloud_engineer_response: str) -> List[str]:
    """Extract list of resources from template or response."""
    resources = []
    
    # Try to extract from Terraform template first
    if terraform_template:
        import re
        # Look for resource blocks in Terraform
        resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"'
        matches = re.findall(resource_pattern, terraform_template)
        for resource_type, resource_name in matches:
            resources.append(f"{resource_type}.{resource_name}")
    
    # If no template, try to extract from cloud engineer response
    elif cloud_engineer_response:
        # Look for common Azure resources mentioned
        azure_resources = [
            "Virtual Network", "Subnet", "Virtual Machine", "Storage Account",
            "Key Vault", "Application Gateway", "Load Balancer", "SQL Database",
            "App Service", "Function App", "Container Instance", "AKS Cluster"
        ]
        
        for resource in azure_resources:
            if resource.lower() in cloud_engineer_response.lower():
                resources.append(resource)
    
    return resources


def _extract_monthly_cost(secops_analysis: str, cost_result: Dict[str, Any]) -> Optional[str]:
    """Extract monthly cost estimate from analysis."""
    if cost_result and isinstance(cost_result, dict):
        if "estimated_monthly_cost" in cost_result:
            return f"{cost_result['estimated_monthly_cost']:.2f}"
    
    if secops_analysis:
        import re
        # Look for cost patterns in the analysis
        cost_patterns = [
            r"\$([\d,]+(?:\.\d{2})?)\s*(?:per\s+month|monthly|/month)",
            r"([\d,]+(?:\.\d{2})?)\s*USD\s*(?:per\s+month|monthly|/month)",
            r"monthly\s+cost.*?\$([\d,]+(?:\.\d{2})?)"
        ]
        
        for pattern in cost_patterns:
            match = re.search(pattern, secops_analysis, re.IGNORECASE)
            if match:
                return match.group(1).replace(",", "")
    
    return None


def _extract_resource_costs(secops_analysis: str, cost_result: Dict[str, Any]) -> Dict[str, str]:
    """Extract per-resource cost breakdown."""
    resource_costs = {}
    
    if cost_result and isinstance(cost_result, dict):
        if "resource_breakdown" in cost_result:
            return {k: f"{v:.2f}" for k, v in cost_result["resource_breakdown"].items()}
    
    if secops_analysis:
        import re
        # Look for resource-specific cost mentions
        lines = secops_analysis.split("\n")
        for line in lines:
            # Pattern: "Resource Name: $XX.XX"
            match = re.search(r"([A-Za-z\s]+):\s*\$([\d,]+(?:\.\d{2})?)", line)
            if match:
                resource_name = match.group(1).strip()
                cost = match.group(2).replace(",", "")
                resource_costs[resource_name] = cost
    
    return resource_costs


def _extract_optimization_tips(secops_analysis: str) -> List[str]:
    """Extract cost optimization recommendations."""
    tips = []
    
    if secops_analysis:
        # Look for optimization-related content
        optimization_keywords = [
            "optimization", "optimize", "reduce cost", "save money", 
            "recommendation", "suggest", "consider", "alternative"
        ]
        
        lines = secops_analysis.split("\n")
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in optimization_keywords):
                # Clean up the line and add as tip
                tip = line.strip("- •*")
                if len(tip) > 10:  # Ignore very short lines
                    tips.append(tip)
    
    return tips[:5]  # Limit to 5 tips
