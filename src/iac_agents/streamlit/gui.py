"""GUI for the IaC Agents application."""

import streamlit as st

from iac_agents.agents import TerraformAgent
from iac_agents.approval_workflow import TerraformApprovalWorkflow
from iac_agents.deployment_automation import TerraformDeploymentManager
from iac_agents.showcase_scenarios import SHOWCASE_SCENARIOS, get_all_scenario_titles

st.set_page_config(
    page_title="Infrastructure as Code AI Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Infrastructure as Code AI Agent")
st.markdown("""
**Transform cloud infrastructure deployment from complex command-line operations to simple conversational requests.**

This showcase demonstrates how AI agents interpret natural language requirements and automatically provision Azure resources through an intelligent multi-agent system with built-in compliance validation.
""")

# Initialize agents and managers
if "terraform_agent" not in st.session_state:
    st.session_state.terraform_agent = TerraformAgent()

if "approval_workflow" not in st.session_state:
    st.session_state.approval_workflow = TerraformApprovalWorkflow()

if "deployment_manager" not in st.session_state:
    st.session_state.deployment_manager = TerraformDeploymentManager()

agent = st.session_state.terraform_agent
approval_workflow = st.session_state.approval_workflow
deployment_manager = st.session_state.deployment_manager

# Showcase mode toggle
showcase_mode = st.sidebar.toggle("🎯 Showcase Mode", value=True)

if showcase_mode:
    st.sidebar.header("🎬 Demo Scenarios")
    scenario_titles = get_all_scenario_titles()
    selected_scenario = st.sidebar.selectbox(
        "Choose a business scenario:",
        ["Custom Request"] + scenario_titles
    )
    
    # Show scenario details
    if selected_scenario != "Custom Request":
        for scenario_key, scenario in SHOWCASE_SCENARIOS.items():
            if scenario["title"] == selected_scenario:
                with st.sidebar.expander("📋 Scenario Details"):
                    st.write(f"**Context:** {scenario['business_context']}")
                    st.write(f"**Estimated Cost:** {scenario['estimated_cost']}")
                    st.write(f"**Compliance:** {', '.join(scenario['compliance_requirements'])}")
                
                if st.sidebar.button("🚀 Load This Scenario"):
                    st.session_state.scenario_request = scenario["user_request"]
                    st.rerun()

# Deployment tracking
st.sidebar.header("📊 Deployments")
deployments = deployment_manager.list_deployments()
if deployments:
    for deployment in deployments[-3:]:  # Show last 3
        status_emoji = {
            "planning": "🔄", "planned": "✅", "applying": "⚡", 
            "completed": "🎉", "failed": "❌", "destroying": "🗑️"
        }.get(deployment.status, "❓")
        
        st.sidebar.write(f"{status_emoji} {deployment.deployment_id[:8]}... ({deployment.status})")
else:
    st.sidebar.info("No deployments yet")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Create columns for main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Chat with Infrastructure AI")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

with col2:
    st.header("🔧 Agent Orchestration")
    
    # Show active agents
    with st.expander("🤖 Active Agents", expanded=True):
        st.write("✅ **Terraform Agent** - Template Generation")
        st.write("✅ **Research Agent** - Documentation Lookup") 
        st.write("✅ **Validation Agent** - Security & Compliance")
        st.write("✅ **Deployment Agent** - Azure Provisioning")
    
    # Show recent activity
    with st.expander("📈 Recent Activity"):
        if st.session_state.messages:
            last_msg = st.session_state.messages[-1]
            if last_msg["role"] == "assistant":
                st.write(f"🕐 Last: Template generated")
                st.write(f"📊 Validation passed: ✅")
        else:
            st.write("No recent activity")

# Main chat input
with col1:
    # Handle pre-loaded scenario
    default_prompt = ""
    if hasattr(st.session_state, 'scenario_request'):
        default_prompt = st.session_state.scenario_request
        del st.session_state.scenario_request
    
    prompt = st.chat_input(
        "Describe your infrastructure requirements...",
        key="main_chat_input"
    ) or default_prompt

# Process user input
if prompt:
    
    # Handle approval responses
    if prompt.upper().startswith(('APPROVE', 'REJECT', 'CHANGES')):
        response = approval_workflow.process_approval_response(prompt)
        st.session_state.messages.append({"role": "system", "content": response})
        
        with st.chat_message("assistant"):
            st.markdown(response)
    else:
        # Handle infrastructure requests
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Terraform template
        with st.chat_message("assistant"):
            with st.spinner("Generating Terraform template..."):
                response = agent.generate_response(prompt)
                st.markdown(response)
                
                # Create approval request
                # Extract template from response (this is simplified)
                if "```hcl" in response:
                    template_start = response.find("```hcl") + 6
                    template_end = response.find("```", template_start)
                    template = response[template_start:template_end].strip()
                    
                    if template:
                        validation_result = agent._validate_template(template)
                        approval_request = approval_workflow.create_approval_request(
                            template=template,
                            requirements=prompt,
                            validation_result=validation_result
                        )
                        
                        approval_summary = approval_workflow.get_approval_summary(approval_request.id)
                        st.markdown("---")
                        st.markdown(approval_summary)

        st.session_state.messages.append({"role": "assistant", "content": response})

# Approval workflow section
st.header("⚖️ Governance & Approval Workflow")

col_approval1, col_approval2 = st.columns(2)

with col_approval1:
    st.subheader("📋 Pending Approvals")
    pending_requests = approval_workflow.get_pending_requests()
    
    if pending_requests:
        for request in pending_requests:
            with st.expander(f"🔍 {request.id[:12]}... ({request.created_at.strftime('%H:%M')})"):
                st.write(f"**Requirements:** {request.requirements[:200]}...")
                
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button(f"✅ Approve", key=f"approve_{request.id}"):
                        result = approval_workflow.process_approval_response(f"APPROVE {request.id}")
                        st.success("Approved!")
                        st.rerun()
                
                with col_btn2:
                    if st.button(f"❌ Reject", key=f"reject_{request.id}"):
                        result = approval_workflow.process_approval_response(f"REJECT {request.id} Requires review")
                        st.error("Rejected!")
                        st.rerun()
                
                with col_btn3:
                    if st.button(f"🔧 Changes", key=f"changes_{request.id}"):
                        result = approval_workflow.process_approval_response(f"CHANGES {request.id} Needs modification")
                        st.warning("Changes requested!")
                        st.rerun()
    else:
        st.info("No pending approvals")

with col_approval2:
    st.subheader("📊 Deployment Pipeline")
    
    # Show deployment progress
    if deployments:
        latest_deployment = deployments[-1]
        
        progress_stages = ["Planning", "Validation", "Approval", "Deployment", "Monitoring"]
        current_stage = {
            "planning": 0, "planned": 1, "applying": 3, 
            "completed": 4, "failed": 3
        }.get(latest_deployment.status, 0)
        
        for i, stage in enumerate(progress_stages):
            if i <= current_stage:
                st.write(f"✅ {stage}")
            elif i == current_stage + 1:
                st.write(f"🔄 {stage} (in progress)")
            else:
                st.write(f"⏳ {stage}")
    else:
        st.info("No active deployments")
