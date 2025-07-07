"""Header components for the Streamlit interface."""

import base64
import os

import streamlit as st

# pylint: disable=E0402
from ...config.settings import config
from ...templates.ui_loader import ui_loader


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
    st.markdown(ui_loader.get_main_css(), unsafe_allow_html=True)


def display_header():
    """Display the application header with branding."""
    # Load company logo
    logo_path = os.path.join(os.getcwd(), "assets", "logo.png")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("# 🤖 Infrastructure as Prompts")
        st.markdown(
            "**Transform infrastructure deployments from complex command-line "
            "operations to simple conversational requests through AI agents.**"
        )

    with col2:
        if os.path.exists(logo_path):
            logo_b64 = load_image_as_base64(str(logo_path))
            if logo_b64:
                st.markdown(
                    f"""
                <div style="text-align: center;">
                    <img src="data:image/png;base64,{logo_b64}" width="150">
                </div>
                """,
                    unsafe_allow_html=True,
                )

    # Add gap below header
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
