"""Chat interface components for the Streamlit interface."""

import streamlit as st

from ...templates.ui_loader import ui_loader


def initialize_chat_messages():
    """Initialize session state for messages with welcome message."""
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


def display_chat_messages():
    """Display chat messages in a scrollable container."""
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
            st.markdown(
                f'<div id="{scroll_target_key}" style="height: 1px;"></div>',
                unsafe_allow_html=True,
            )

    return scroll_target_key


def setup_auto_scroll(scroll_target_key: str):
    """Setup auto-scroll functionality for chat messages."""
    if len(st.session_state.messages) > 1:  # More than just welcome message
        # Get enhanced scroll JavaScript
        js_content = ui_loader._loader.load_js_file("enhanced_scroll")

        # Create the script with the scroll target
        enhanced_scroll_js = f"""
        <script>
        {js_content}

        // Execute the enhanced scroll
        setupEnhancedScroll('{scroll_target_key}');
        </script>
        """
        st.markdown(enhanced_scroll_js, unsafe_allow_html=True)


def display_chat_input() -> str:
    """Display chat input field and return user input."""
    # Chat input with proper spacing
    st.markdown(
        '<div style="margin-top: 1rem; margin-left: 1rem;">', unsafe_allow_html=True
    )
    user_input = st.chat_input(
        "Describe your infrastructure requirements...", key="main_chat"
    )
    st.markdown("</div>", unsafe_allow_html=True)

    return user_input


def display_chat_interface():
    """Display the complete chat interface."""
    st.markdown("### 💬 Chat with AI Infrastructure Agent")

    # Initialize messages
    initialize_chat_messages()

    # Display messages and get scroll target
    scroll_target_key = display_chat_messages()

    # Setup auto-scroll
    setup_auto_scroll(scroll_target_key)

    # Display input and return user input
    return display_chat_input()


def add_message(role: str, content: str):
    """Add a message to the chat history."""
    st.session_state.messages.append({"role": role, "content": content})


def get_chat_history():
    """Get the current chat history."""
    return st.session_state.messages.copy() if "messages" in st.session_state else []


def clear_chat_history():
    """Clear the chat history and reinitialize with welcome message."""
    if "messages" in st.session_state:
        del st.session_state.messages
    initialize_chat_messages()
