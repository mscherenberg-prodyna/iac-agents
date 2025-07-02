"""Chat interface components for the Streamlit interface."""

import os

import streamlit as st
import streamlit.components.v1 as components

# pylint: disable=E0402
from ...templates.template_loader import template_loader
from ...templates.template_manager import template_manager


def initialize_chat_messages():
    """Initialize session state for messages with welcome message."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        welcome_content = template_manager.get_prompt("welcome_message")
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": welcome_content,
            }
        )


def display_chat_messages():
    """Display chat messages in a scrollable container."""
    # Create a scrollable container for messages
    message_container = st.container()

    with message_container:
        # Display chat messages
        for _, message in enumerate(st.session_state.messages):
            avatar = os.path.join(os.getcwd(), "assets", "user_logo.png")
            if message["role"] == "assistant":
                avatar = os.path.join(os.getcwd(), "assets", "planner_agent_small.png")

            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])


def trigger_auto_scroll():
    """Trigger auto-scroll to bottom of page."""
    scroll_html = template_loader.load_html_template("auto_scroll")
    components.html(scroll_html, height=0)


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

    # Display messages
    display_chat_messages()

    # Check if we should scroll after a rerun
    if st.session_state.get("should_scroll", False):
        trigger_auto_scroll()
        st.session_state.should_scroll = False

    # Display input and return user input
    return display_chat_input()


def add_message(role: str, content: str):
    """Add a message to the chat history."""
    st.session_state.messages.append({"role": role, "content": content})
    # Set flag to trigger scroll after rerun
    if role == "assistant":
        st.session_state.should_scroll = True


def get_chat_history():
    """Get the current chat history."""
    return st.session_state.messages.copy() if "messages" in st.session_state else []


def clear_chat_history():
    """Clear the chat history and reinitialize with welcome message."""
    if "messages" in st.session_state:
        del st.session_state.messages
    initialize_chat_messages()
