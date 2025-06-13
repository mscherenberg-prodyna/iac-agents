"""Enhanced GUI for the Infrastructure as Code AI Agent with improved UX."""

import streamlit as st
import time
import base64
from pathlib import Path
from typing import Dict, Any

from iac_agents.agents import SupervisorAgent
from iac_agents.approval_workflow import TerraformApprovalWorkflow
from iac_agents.deployment_automation import TerraformDeploymentManager
from iac_agents.showcase_scenarios import SHOWCASE_SCENARIOS, get_all_scenario_titles
from iac_agents.logging_system import agent_logger


def load_image_as_base64(image_path: str) -> str:
    """Load image and convert to base64 for display."""
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return base64.b64encode(image_bytes).decode()
    except:
        return ""


def setup_page_config():
    """Setup Streamlit page configuration and custom CSS."""
    st.set_page_config(
        page_title="PRODYNA - Infrastructure as Code AI Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    /* Main container styling */
    .main-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
    }
    
    /* Chat container with proper scrolling */
    .chat-container {
        height: 600px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        background-color: #fafafa;
        margin-bottom: 1rem;
    }
    
    /* Auto-scroll to bottom for new messages */
    .element-container:last-child {
        margin-bottom: 0;
    }
    
    /* Chat input spacing */
    .stChatInput {
        margin-left: 1rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    
    .stChatInput > div {
        margin-left: 1rem;
    }
    
    /* Agent status indicators - Fixed styling */
    .agent-status {
        display: flex;
        flex-direction: column;
        margin: 0.5rem 0;
        padding: 0.75rem;
        border-radius: 8px;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        transition: all 0.2s ease;
    }
    
    .agent-status:hover {
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .agent-status.active {
        background-color: #d4edda;
        border-color: #28a745;
        border-left: 4px solid #28a745;
    }
    
    .agent-status.working {
        background-color: #fff3cd;
        border-color: #ffc107;
        border-left: 4px solid #ffc107;
        animation: pulse 2s infinite;
    }
    
    .agent-status.idle {
        background-color: #f8f9fa;
        border-color: #6c757d;
        color: #6c757d;
    }
    
    .agent-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: bold;
        font-size: 0.9rem;
    }
    
    .agent-subtext {
        font-size: 0.8rem;
        margin-top: 0.25rem;
        opacity: 0.8;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    /* Progress indicators */
    .workflow-stage {
        display: flex;
        align-items: center;
        margin: 0.25rem 0;
        font-size: 0.9rem;
        padding: 0.25rem 0;
    }
    
    .workflow-stage.completed {
        color: #28a745;
        font-weight: 500;
    }
    
    .workflow-stage.current {
        color: #ffc107;
        font-weight: bold;
        background-color: #fff8dc;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
    }
    
    .workflow-stage.pending {
        color: #6c757d;
    }
    
    /* Logo styling */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    /* Cost estimation styling */
    .cost-estimate {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Activity log styling - Fixed */
    .activity-log {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 0.75rem;
        max-height: 250px;
        overflow-y: auto;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 0.75rem;
        line-height: 1.4;
    }
    
    .activity-entry {
        margin-bottom: 0.5rem;
        padding: 0.25rem 0;
        border-bottom: 1px solid #e9ecef;
    }
    
    .activity-entry:last-child {
        border-bottom: none;
        margin-bottom: 0;
    }
    
    .activity-timestamp {
        color: #6c757d;
        font-weight: 500;
    }
    
    .activity-agent {
        color: #495057;
        font-weight: 600;
    }
    
    .activity-message {
        color: #343a40;
        margin-top: 0.1rem;
    }
    
    /* Sidebar sections */
    .sidebar-section {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #e9ecef;
    }
    
    .sidebar-section h3 {
        margin-top: 0;
        margin-bottom: 0.75rem;
        color: #495057;
        border-bottom: 2px solid #e9ecef;
        padding-bottom: 0.5rem;
    }
    
    /* System metrics styling */
    .metric-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem;
        background-color: #f8f9fa;
        border-radius: 4px;
        margin: 0.25rem 0;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #6c757d;
    }
    
    .metric-value {
        font-size: 1.1rem;
        font-weight: bold;
        color: #495057;
    }
    </style>
    """, unsafe_allow_html=True)


def display_header():
    """Display the application header with branding."""
    # Load company logo
    assets_path = Path(__file__).parent.parent.parent.parent / "assets"
    logo_path = assets_path / "prodyna.png"
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("# 🤖 Infrastructure as Code AI Agent")
        st.markdown("**Transform infrastructure deployment from complex command-line operations to simple conversational requests.**")
    
    with col2:
        if logo_path.exists():
            logo_b64 = load_image_as_base64(str(logo_path))
            if logo_b64:
                st.markdown(f"""
                <div style="text-align: right;">
                    <img src="data:image/png;base64,{logo_b64}" width="150">
                </div>
                """, unsafe_allow_html=True)


def display_agent_status():
    """Display real-time agent status in sidebar."""
    st.sidebar.markdown("""
    <div class="sidebar-section">
        <h3>🤖 Agent Status</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Get active agents from logger
    try:
        active_agents = agent_logger.get_active_agents()
        recent_logs = agent_logger.get_recent_logs(10)
    except Exception as e:
        active_agents = []
        recent_logs = []
    
    # Agent status indicators
    agents = [
        ("Supervisor Agent", "🎯", "supervisor"),
        ("Terraform Agent", "🏗️", "terraform"),
        ("Research Agent", "🔍", "research"),
        ("Compliance Agent", "⚖️", "compliance"),
        ("Cost Agent", "💰", "cost")
    ]
    
    for agent_name, emoji, agent_key in agents:
        is_active = any(agent_key.lower() in active.lower() for active in active_agents)
        
        if is_active:
            status_class = "working"
            status_text = "WORKING"
            subtext = "Processing your request..."
        else:
            status_class = "idle"
            status_text = "READY"
            subtext = "Standing by for tasks"
        
        st.sidebar.markdown(f"""
        <div class="agent-status {status_class}">
            <div class="agent-header">
                {emoji} {agent_name}
            </div>
            <div class="agent-subtext">
                {status_text} - {subtext}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent activity with improved formatting
    if recent_logs:
        st.sidebar.markdown("""
        <div class="sidebar-section">
            <h3>📊 Recent Activity</h3>
        </div>
        """, unsafe_allow_html=True)
        
        activity_html = '<div class="activity-log">'
        for log in recent_logs[-5:]:  # Show last 5 activities
            timestamp = log.timestamp.strftime("%H:%M:%S")
            activity_snippet = log.activity[:60] + ("..." if len(log.activity) > 60 else "")
            
            activity_html += f'''
            <div class="activity-entry">
                <div class="activity-timestamp">[{timestamp}]</div>
                <div class="activity-agent">{log.agent_name}</div>
                <div class="activity-message">{activity_snippet}</div>
            </div>
            '''
        activity_html += '</div>'
        
        st.sidebar.markdown(activity_html, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("""
        <div class="sidebar-section">
            <h3>📊 Recent Activity</h3>
            <div class="activity-log">
                <div class="activity-entry">
                    <div class="activity-message">No recent activity. Start a conversation to see agent activity here.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def display_workflow_progress(supervisor_agent: SupervisorAgent):
    """Display current workflow progress."""
    workflow_status = supervisor_agent.get_workflow_status()
    
    if workflow_status["status"] == "active":
        st.sidebar.markdown("### 🔄 Workflow Progress")
        
        # Define all possible stages
        all_stages = [
            "requirements_analysis",
            "research_and_planning", 
            "template_generation",
            "validation_and_compliance",
            "cost_estimation",
            "approval_preparation",
            "completed"
        ]
        
        completed = workflow_status.get("completed_stages", [])
        current = workflow_status.get("current_stage", "")
        
        for stage in all_stages:
            stage_name = stage.replace("_", " ").title()
            
            if stage in completed:
                st.sidebar.markdown(f"✅ {stage_name}")
            elif stage == current:
                st.sidebar.markdown(f"🔄 {stage_name} *(in progress)*")
            else:
                st.sidebar.markdown(f"⏳ {stage_name}")


def display_chat_interface():
    """Display the main chat interface with proper scrolling."""
    st.markdown("### 💬 Chat with AI Infrastructure Agent")
    
    # Initialize session state for messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant",
            "content": """👋 **Welcome to PRODYNA's Infrastructure as Code AI Agent!**

I can help you transform your infrastructure requirements into production-ready Azure deployments. Here's what I can do:

• **🏗️ Generate Terraform templates** from natural language descriptions
• **⚖️ Validate compliance** against industry frameworks (PCI DSS, HIPAA, SOX, GDPR, ISO 27001)
• **💰 Estimate costs** for your Azure infrastructure
• **🔍 Research best practices** using current documentation
• **👥 Orchestrate approval workflows** for governance

**To get started:**
1. Choose a demo scenario from the sidebar, or
2. Describe your infrastructure requirements in plain English

*Example: "I need a secure web application for e-commerce with payment processing, auto-scaling, and global CDN."*"""
        })
    
    # Create a container for messages that will be scrollable
    message_container = st.container()
    
    with message_container:
        # Display chat messages
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Auto-scroll to bottom when new messages are added
    if len(st.session_state.messages) > 1:  # More than just welcome message
        st.markdown("""
        <script>
        // Auto-scroll to bottom of chat
        function scrollToBottom() {
            var chatContainer = parent.document.querySelector('[data-testid="stChatMessage"]');
            if (chatContainer) {
                var lastMessage = chatContainer.parentElement.lastElementChild;
                if (lastMessage) {
                    lastMessage.scrollIntoView({ behavior: 'smooth', block: 'end' });
                }
            }
        }
        
        // Scroll after a small delay to ensure content is rendered
        setTimeout(scrollToBottom, 100);
        </script>
        """, unsafe_allow_html=True)
    
    # Chat input with proper spacing
    st.markdown('<div style="margin-top: 1rem; margin-left: 1rem;">', unsafe_allow_html=True)
    user_input = st.chat_input("Describe your infrastructure requirements...", key="main_chat")
    st.markdown('</div>', unsafe_allow_html=True)
    
    return user_input


def display_showcase_scenarios():
    """Display demo scenarios in sidebar."""
    st.sidebar.markdown("### 🎬 Demo Scenarios")
    
    scenario_titles = get_all_scenario_titles()
    selected_scenario = st.sidebar.selectbox(
        "Choose a business scenario:",
        ["Custom Request"] + scenario_titles,
        key="scenario_selector"
    )
    
    if selected_scenario != "Custom Request":
        for scenario_key, scenario in SHOWCASE_SCENARIOS.items():
            if scenario["title"] == selected_scenario:
                with st.sidebar.expander("📋 Scenario Details", expanded=False):
                    st.markdown(f"**Context:** {scenario['business_context']}")
                    st.markdown(f"**Estimated Cost:** {scenario['estimated_cost']}")
                    st.markdown(f"**Compliance:** {', '.join(scenario['compliance_requirements'])}")
                
                if st.sidebar.button("🚀 Load This Scenario", key=f"load_{scenario_key}"):
                    return scenario["user_request"]
    
    return None


def display_cost_estimation(cost_data: Dict[str, Any]):
    """Display cost estimation in a nice format."""
    if not cost_data:
        return
    
    total_cost = cost_data.get("total_monthly_usd", 0)
    confidence = cost_data.get("confidence", "medium")
    
    confidence_color = {
        "high": "#4caf50",
        "medium": "#ff9800", 
        "low": "#f44336"
    }.get(confidence, "#9e9e9e")
    
    st.markdown(f"""
    <div class="cost-estimate">
        <h4>💰 Cost Estimation</h4>
        <p><strong>Estimated Monthly Cost: ${total_cost:.2f}</strong></p>
        <p>Confidence Level: <span style="color: {confidence_color}; font-weight: bold;">{confidence.upper()}</span></p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application function."""
    setup_page_config()
    display_header()
    
    # Initialize agents
    if "supervisor_agent" not in st.session_state:
        st.session_state.supervisor_agent = SupervisorAgent()
    
    if "approval_workflow" not in st.session_state:
        st.session_state.approval_workflow = TerraformApprovalWorkflow()
    
    if "deployment_manager" not in st.session_state:
        st.session_state.deployment_manager = TerraformDeploymentManager()
    
    supervisor_agent = st.session_state.supervisor_agent
    approval_workflow = st.session_state.approval_workflow
    deployment_manager = st.session_state.deployment_manager
    
    # Sidebar content
    display_agent_status()
    display_workflow_progress(supervisor_agent)
    
    # Demo scenarios
    scenario_request = display_showcase_scenarios()
    
    # Deployment status
    deployments = deployment_manager.list_deployments()
    if deployments:
        st.sidebar.markdown("### 📊 Recent Deployments")
        for deployment in deployments[-3:]:
            status_emoji = {
                "planning": "🔄", "planned": "✅", "applying": "⚡", 
                "completed": "🎉", "failed": "❌"
            }.get(deployment.status, "❓")
            
            st.sidebar.markdown(f"{status_emoji} {deployment.deployment_id[:8]}... ({deployment.status})")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Chat interface
        user_input = display_chat_interface()
        
        # Handle scenario loading
        if scenario_request:
            user_input = scenario_request
        
        # Process user input
        if user_input:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Show processing message immediately
            with st.chat_message("assistant"):
                with st.spinner("🤖 Processing your request..."):
                    # Process with supervisor agent
                    try:
                        response = supervisor_agent.process_user_request(user_input)
                        
                        # Add to session state
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                    except Exception as e:
                        error_msg = f"I apologize, but I encountered an error: {str(e)}. Please try again with a different approach."
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
            # Force auto-scroll after processing
            st.markdown("""
            <script>
            setTimeout(function() {
                var elements = parent.document.querySelectorAll('[data-testid="stChatMessage"]');
                if (elements.length > 0) {
                    var lastElement = elements[elements.length - 1];
                    lastElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
                }
            }, 200);
            </script>
            """, unsafe_allow_html=True)
            
            # Rerun to update the interface
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="sidebar-section">
            <h3>🔧 System Status</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Show agent images
        assets_path = Path(__file__).parent.parent.parent.parent / "assets"
        
        planner_img = assets_path / "planner_agent_small.png"
        worker_img = assets_path / "worker_agent_small.png"
        
        agent_images_displayed = False
        
        if planner_img.exists():
            planner_b64 = load_image_as_base64(str(planner_img))
            if planner_b64:
                st.markdown("**🎯 Planner Agent**")
                st.markdown(f'<img src="data:image/png;base64,{planner_b64}" width="100" style="border-radius: 8px; margin-bottom: 1rem;">', unsafe_allow_html=True)
                agent_images_displayed = True
        
        if worker_img.exists():
            worker_b64 = load_image_as_base64(str(worker_img))
            if worker_b64:
                st.markdown("**🔧 Worker Agent**")
                st.markdown(f'<img src="data:image/png;base64,{worker_b64}" width="100" style="border-radius: 8px; margin-bottom: 1rem;">', unsafe_allow_html=True)
                agent_images_displayed = True
        
        if not agent_images_displayed:
            st.markdown("**🤖 AI Agents**")
            st.markdown("🎯 Planner Agent - Ready")
            st.markdown("🔧 Worker Agent - Ready")
        
        # System metrics with improved styling
        st.markdown("""
        <div class="sidebar-section">
            <h3>📈 System Metrics</h3>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            total_messages = len(st.session_state.messages) if "messages" in st.session_state else 0
            active_agents_count = len(agent_logger.get_active_agents()) if hasattr(agent_logger, 'get_active_agents') else 0
            
            # Display metrics with custom styling
            st.markdown(f"""
            <div class="metric-container">
                <span class="metric-label">Total Messages</span>
                <span class="metric-value">{total_messages}</span>
            </div>
            <div class="metric-container">
                <span class="metric-label">Active Agents</span>
                <span class="metric-value">{active_agents_count}</span>
            </div>
            <div class="metric-container">
                <span class="metric-label">Session Status</span>
                <span class="metric-value">🟢 Active</span>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown("""
            <div class="metric-container">
                <span class="metric-label">System Status</span>
                <span class="metric-value">🟡 Initializing</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent logs with improved display
        st.markdown("""
        <div class="sidebar-section">
            <h3>📝 Console Log</h3>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            logs = agent_logger.get_recent_logs(5) if hasattr(agent_logger, 'get_recent_logs') else []
            if logs:
                log_html = '<div class="activity-log">'
                for log in reversed(logs[-3:]):  # Show newest 3 first
                    timestamp = log.timestamp.strftime("%H:%M:%S")
                    level_emoji = {
                        "AGENT_START": "🚀",
                        "AGENT_COMPLETE": "✅", 
                        "USER_UPDATE": "💬",
                        "INFO": "ℹ️",
                        "WARNING": "⚠️",
                        "ERROR": "❌"
                    }.get(str(log.level).split('.')[-1] if hasattr(log, 'level') else "INFO", "•")
                    
                    log_html += f'''
                    <div class="activity-entry">
                        <div class="activity-timestamp">{level_emoji} [{timestamp}]</div>
                        <div class="activity-agent">{log.agent_name}</div>
                        <div class="activity-message">{log.activity[:50]}{"..." if len(log.activity) > 50 else ""}</div>
                    </div>
                    '''
                log_html += '</div>'
                st.markdown(log_html, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="activity-log">
                    <div class="activity-entry">
                        <div class="activity-message">No recent activity. Start a conversation to see logs here.</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown("""
            <div class="activity-log">
                <div class="activity-entry">
                    <div class="activity-message">Console logging initializing...</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Approval workflow section (bottom of page)
    if approval_workflow.get_pending_requests():
        st.markdown("---")
        st.markdown("## ⚖️ Pending Approvals")
        
        pending_requests = approval_workflow.get_pending_requests()
        
        for request in pending_requests:
            with st.expander(f"🔍 Review Request {request.id[:12]}... (Created: {request.created_at.strftime('%H:%M')})"):
                st.markdown(f"**Requirements:** {request.requirements[:300]}...")
                
                col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                
                with col_btn1:
                    if st.button("✅ Approve", key=f"approve_{request.id}"):
                        result = approval_workflow.process_approval_response(f"APPROVE {request.id}")
                        st.success("Approved! Proceeding with deployment preparation.")
                        st.rerun()
                
                with col_btn2:
                    if st.button("❌ Reject", key=f"reject_{request.id}"):
                        result = approval_workflow.process_approval_response(f"REJECT {request.id} Security review required")
                        st.error("Request rejected. Please address security concerns.")
                        st.rerun()
                
                with col_btn3:
                    if st.button("🔧 Request Changes", key=f"changes_{request.id}"):
                        result = approval_workflow.process_approval_response(f"CHANGES {request.id} Requires modifications")
                        st.warning("Changes requested. Please refine the template.")
                        st.rerun()
                
                with col_btn4:
                    if st.button("📋 View Details", key=f"details_{request.id}"):
                        st.markdown(approval_workflow.get_approval_summary(request.id))


if __name__ == "__main__":
    main()