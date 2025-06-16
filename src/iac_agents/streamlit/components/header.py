"""Header components for the Streamlit interface."""

import base64
from pathlib import Path

import streamlit as st

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
    assets_path = Path(__file__).parent.parent.parent.parent / "assets"
    logo_path = assets_path / "logo.png"

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("# 🤖 Infrastructure as Prompts AI Agent")
        st.markdown(
            "**Transform infrastructure deployment from complex command-line "
            "operations to simple conversational requests.**"
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


def display_navigation():
    """Display navigation tabs or menu."""
    tabs = st.tabs(["💬 Chat", "📊 Dashboard", "⚙️ Settings"])
    return tabs
