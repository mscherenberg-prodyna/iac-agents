"""Enhanced GUI for the Infrastructure as Code AI Agent with improved UX."""

import base64
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from iac_agents.agents import SupervisorAgent
from iac_agents.approval_workflow import TerraformApprovalWorkflow
from iac_agents.config.settings import config
from iac_agents.config.ui_styles import AUTO_SCROLL_JS, MAIN_CSS
from iac_agents.deployment_automation import TerraformDeploymentManager
from iac_agents.logging_system import agent_logger
from iac_agents.showcase_scenarios import SHOWCASE_SCENARIOS, get_all_scenario_titles


def load_image_as_base64(image_path: str) -> str:
    """Load image and convert to base64 for display."""
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return base64.b64encode(image_bytes).decode()
    except (FileNotFoundError, IOError):
        return ""


def setup_page_config():
    """Setup Streamlit page configuration and custom CSS."""
    st.set_page_config(
        page_title=config.ui.page_title,
        page_icon=config.ui.page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Apply custom CSS styling
    st.markdown(MAIN_CSS, unsafe_allow_html=True)


def display_header():
    """Display the application header with branding."""
    # Load company logo
    assets_path = Path(__file__).parent.parent.parent.parent / "assets"
    logo_path = assets_path / "logo.png"

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("# 🤖 Infrastructure as Prompts AI Agent")
        st.markdown(
            "**Transform infrastructure deployment from complex command-line operations to simple conversational requests.**"
        )

    with col2:
        if logo_path.exists():
            logo_b64 = load_image_as_base64(str(logo_path))
            if logo_b64:
                st.markdown(
                    f"""
                <div style="text-align: right;">
                    <img src="data:image/png;base64,{logo_b64}" width="150">
                </div>
                """,
                    unsafe_allow_html=True,
                )


def display_agent_status():
    """Display real-time agent status in sidebar."""
    st.sidebar.markdown(
        """
    <div class="sidebar-section">
        <h3>🤖 Agent Status</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Get active agents from logger
    try:
        active_agents = agent_logger.get_active_agents()
        recent_logs = agent_logger.get_recent_logs(10)
    except Exception:
        active_agents = []
        recent_logs = []

    # Agent status indicators
    agents = [
        ("Supervisor Agent", "🎯", "supervisor"),
        ("Terraform Agent", "🏗️", "terraform"),
        ("Research Agent", "🔍", "research"),
        ("Compliance Agent", "⚖️", "compliance"),
        ("Cost Agent", "💰", "cost"),
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

        st.sidebar.markdown(
            f"""
        <div class="agent-status {status_class}">
            <div class="agent-header">
                {emoji} {agent_name}
            </div>
            <div class="agent-subtext">
                {status_text} - {subtext}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Recent activity with improved formatting using native Streamlit components
    st.sidebar.markdown("### 📊 Recent Activity")

    if recent_logs:
        # Use a container with scrollable content
        with st.sidebar.container():
            for log in recent_logs[
                -config.ui.activity_log_entries :
            ]:  # Show last N activities
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

                # Create a clean, simple display
                st.sidebar.text(f"{level_emoji} [{timestamp}]")
                st.sidebar.text(f"   {log.agent_name}")
                st.sidebar.text(f"   {activity_snippet}")
                st.sidebar.markdown("---")
    else:
        st.sidebar.info(
            "No recent activity. Start a conversation to see agent activity here."
        )


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
            "completed",
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
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": """👋 **Welcome to the Infrastructure as Prompts AI agent!**

I can help you transform your infrastructure requirements into production-ready Azure deployments. Here's what I can do:

• **🏗️ Generate Terraform templates** from natural language descriptions
• **⚖️ Validate compliance** against industry frameworks (PCI DSS, HIPAA, SOX, GDPR, ISO 27001)
• **💰 Estimate costs** for your Azure infrastructure
• **🔍 Research best practices** using current documentation
• **👥 Orchestrate approval workflows** for governance

**To get started:**
1. Choose a demo scenario from the sidebar, or
2. Describe your infrastructure requirements in plain English

*Example: "I need a secure web application for e-commerce with payment processing, auto-scaling, and global CDN."*""",
            }
        )

    # Create a scrollable container for messages with unique key
    message_container = st.container()
    
    # Add a unique element that we can target for scrolling
    scroll_target_key = f"scroll_target_{len(st.session_state.messages)}"

    with message_container:
        # Display chat messages
        for _, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Add an invisible element at the bottom to scroll to
        if len(st.session_state.messages) > 1:
            st.markdown(f'<div id="{scroll_target_key}" style="height: 1px;"></div>', 
                       unsafe_allow_html=True)

    # Auto-scroll to bottom when new messages are added
    if len(st.session_state.messages) > 1:  # More than just welcome message
        # Enhanced autoscroll with fallback strategies
        enhanced_scroll_js = f"""
        <script>
        // Enhanced autoscroll with multiple strategies
        function enhancedScrollToBottom() {{
            var scrolled = false;
            
            // Strategy 1: Scroll to our target element
            try {{
                var target = parent.document.getElementById('{scroll_target_key}');
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'end' }});
                    scrolled = true;
                }}
            }} catch(e) {{
                console.log('Target element scroll failed:', e);
            }}
            
            // Strategy 2: Original chat message scrolling
            if (!scrolled) {{
                try {{
                    var chatMessages = parent.document.querySelectorAll('[data-testid="stChatMessage"]');
                    if (chatMessages.length > 0) {{
                        var lastMessage = chatMessages[chatMessages.length - 1];
                        lastMessage.scrollIntoView({{ behavior: 'smooth', block: 'end' }});
                        scrolled = true;
                    }}
                }} catch(e) {{
                    console.log('Chat message scroll failed:', e);
                }}
            }}
            
            // Strategy 3: Scroll main container
            if (!scrolled) {{
                try {{
                    var mainContainer = parent.document.querySelector('section[data-testid="stMain"]');
                    if (mainContainer) {{
                        mainContainer.scrollTop = mainContainer.scrollHeight;
                        scrolled = true;
                    }}
                }} catch(e) {{
                    console.log('Main container scroll failed:', e);
                }}
            }}
            
            // Strategy 4: Window scroll
            if (!scrolled) {{
                try {{
                    parent.window.scrollTo(0, parent.document.body.scrollHeight);
                }} catch(e) {{
                    console.log('Window scroll failed:', e);
                }}
            }}
            
            return scrolled;
        }}
        
        // Execute with multiple timing attempts
        setTimeout(enhancedScrollToBottom, 50);
        setTimeout(enhancedScrollToBottom, 200);
        setTimeout(enhancedScrollToBottom, 500);
        setTimeout(enhancedScrollToBottom, 1000);
        </script>
        """
        st.markdown(enhanced_scroll_js, unsafe_allow_html=True)

    # Chat input with proper spacing
    st.markdown(
        '<div style="margin-top: 1rem; margin-left: 1rem;">', unsafe_allow_html=True
    )
    user_input = st.chat_input(
        "Describe your infrastructure requirements...", key="main_chat"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    return user_input


def display_showcase_scenarios():
    """Display demo scenarios in sidebar."""
    st.sidebar.markdown("### 🎬 Demo Scenarios")

    scenario_titles = get_all_scenario_titles()
    selected_scenario = st.sidebar.selectbox(
        "Choose a business scenario:",
        ["Custom Request"] + scenario_titles,
        key="scenario_selector",
    )

    if selected_scenario != "Custom Request":
        for scenario_key, scenario in SHOWCASE_SCENARIOS.items():
            if scenario["title"] == selected_scenario:
                with st.sidebar.expander("📋 Scenario Details", expanded=False):
                    st.markdown(f"**Context:** {scenario['business_context']}")
                    st.markdown(f"**Estimated Cost:** {scenario['estimated_cost']}")
                    st.markdown(
                        f"**Compliance:** {', '.join(scenario['compliance_requirements'])}"
                    )

                if st.sidebar.button(
                    "🚀 Load This Scenario", key=f"load_{scenario_key}"
                ):
                    return scenario["user_request"]

    return None


def display_cost_estimation(cost_data: Dict[str, Any]):
    """Display cost estimation in a nice format."""
    if not cost_data:
        return

    total_cost = cost_data.get("total_monthly_usd", 0)
    confidence = cost_data.get("confidence", "medium")

    confidence_color = {"high": "#4caf50", "medium": "#ff9800", "low": "#f44336"}.get(
        confidence, "#9e9e9e"
    )

    st.markdown(
        f"""
    <div class="cost-estimate">
        <h4>💰 Cost Estimation</h4>
        <p><strong>Estimated Monthly Cost: ${total_cost:.2f}</strong></p>
        <p>Confidence Level: <span style="color: {confidence_color}; font-weight: bold;">{confidence.upper()}</span></p>
    </div>
    """,
        unsafe_allow_html=True,
    )


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
                "planning": "🔄",
                "planned": "✅",
                "applying": "⚡",
                "completed": "🎉",
                "failed": "❌",
            }.get(deployment.status, "❓")

            st.sidebar.markdown(
                f"{status_emoji} {deployment.deployment_id[:8]}... ({deployment.status})"
            )

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
                        # Get compliance settings from session state
                        compliance_settings = st.session_state.get(
                            "compliance_settings",
                            {"enforce_compliance": False, "selected_frameworks": []},
                        )

                        response = supervisor_agent.process_user_request(
                            user_input, compliance_settings
                        )

                        # Add to session state
                        st.session_state.messages.append(
                            {"role": "assistant", "content": response}
                        )

                    except Exception as e:
                        error_msg = f"I apologize, but I encountered an error: {str(e)}. Please try again with a different approach."
                        st.session_state.messages.append(
                            {"role": "assistant", "content": error_msg}
                        )
                    
                    # Force rerun to trigger autoscroll with new messages
                    st.rerun()

    with col2:
        # Compliance Framework Selection
        st.markdown(
            """
        <div class="sidebar-section">
            <h3>⚖️ Compliance Settings</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Initialize compliance settings in session state
        if "compliance_settings" not in st.session_state:
            st.session_state.compliance_settings = {
                "enforce_compliance": False,
                "selected_frameworks": [],
            }

        # Compliance enforcement toggle
        enforce_compliance = st.checkbox(
            "🔒 Enforce Compliance Validation",
            value=st.session_state.compliance_settings["enforce_compliance"],
            help="When enabled, templates must meet selected compliance frameworks before deployment recommendation",
        )
        st.session_state.compliance_settings["enforce_compliance"] = enforce_compliance

        # Framework selection (only shown when compliance is enforced)
        if enforce_compliance:
            st.markdown("**Select Compliance Frameworks:**")

            frameworks = config.compliance.available_frameworks

            selected_frameworks = []
            for framework, description in frameworks.items():
                if st.checkbox(
                    framework, help=description, key=f"compliance_{framework}"
                ):
                    selected_frameworks.append(framework)

            st.session_state.compliance_settings["selected_frameworks"] = (
                selected_frameworks
            )

            if selected_frameworks:
                st.success(f"✅ {len(selected_frameworks)} frameworks selected")
            else:
                st.warning("⚠️ Select at least one framework")
        else:
            st.info(
                "💡 Compliance validation disabled - templates will be generated with basic security practices"
            )
            st.session_state.compliance_settings["selected_frameworks"] = []

        # System metrics with improved styling
        st.markdown(
            """
        <div class="sidebar-section">
            <h3>📈 System Metrics</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

        try:
            total_messages = (
                len(st.session_state.messages) if "messages" in st.session_state else 0
            )
            active_agents_count = (
                len(agent_logger.get_active_agents())
                if hasattr(agent_logger, "get_active_agents")
                else 0
            )

            # Display metrics with custom styling
            st.markdown(
                f"""
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
            """,
                unsafe_allow_html=True,
            )

        except Exception:
            st.markdown(
                """
            <div class="metric-container">
                <span class="metric-label">System Status</span>
                <span class="metric-value">🟡 Initializing</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Recent logs with improved display
        st.markdown(
            """
        <div class="sidebar-section">
            <h3>📝 Console Log</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

        try:
            logs = (
                agent_logger.get_recent_logs(5)
                if hasattr(agent_logger, "get_recent_logs")
                else []
            )
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
                        "ERROR": "❌",
                    }.get(
                        (
                            str(log.level).rsplit(".", maxsplit=1)[-1]
                            if hasattr(log, "level")
                            else "INFO"
                        ),
                        "•",
                    )

                    log_html += f"""
                    <div class="activity-entry">
                        <div class="activity-timestamp">{level_emoji} [{timestamp}]</div>
                        <div class="activity-agent">{log.agent_name}</div>
                        <div class="activity-message">{log.activity[:50]}{"..." if len(log.activity) > 50 else ""}</div>
                    </div>
                    """
                log_html += "</div>"
                st.markdown(log_html, unsafe_allow_html=True)
            else:
                st.markdown(
                    """
                <div class="activity-log">
                    <div class="activity-entry">
                        <div class="activity-message">No recent activity. Start a conversation to see logs here.</div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        except Exception:
            st.markdown(
                """
            <div class="activity-log">
                <div class="activity-entry">
                    <div class="activity-message">Console logging initializing...</div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Approval workflow section (bottom of page)
    if approval_workflow.get_pending_requests():
        st.markdown("---")
        st.markdown("## ⚖️ Pending Approvals")

        pending_requests = approval_workflow.get_pending_requests()

        for request in pending_requests:
            with st.expander(
                f"🔍 Review Request {request.id[:12]}... (Created: {request.created_at.strftime('%H:%M')})"
            ):
                st.markdown(f"**Requirements:** {request.requirements[:300]}...")

                col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

                with col_btn1:
                    if st.button("✅ Approve", key=f"approve_{request.id}"):
                        approval_workflow.process_approval_response(
                            f"APPROVE {request.id}"
                        )
                        st.success("Approved! Proceeding with deployment preparation.")
                        st.rerun()

                with col_btn2:
                    if st.button("❌ Reject", key=f"reject_{request.id}"):
                        approval_workflow.process_approval_response(
                            f"REJECT {request.id} Security review required"
                        )
                        st.error("Request rejected. Please address security concerns.")
                        st.rerun()

                with col_btn3:
                    if st.button("🔧 Request Changes", key=f"changes_{request.id}"):
                        approval_workflow.process_approval_response(
                            f"CHANGES {request.id} Requires modifications"
                        )
                        st.warning("Changes requested. Please refine the template.")
                        st.rerun()

                with col_btn4:
                    if st.button("📋 View Details", key=f"details_{request.id}"):
                        st.markdown(approval_workflow.get_approval_summary(request.id))


if __name__ == "__main__":
    main()
