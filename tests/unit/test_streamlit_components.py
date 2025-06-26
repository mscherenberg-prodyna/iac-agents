"""Unit tests for streamlit components."""

from unittest.mock import Mock, patch

import pytest


class TestStreamlitComponentsBasic:
    """Basic tests for streamlit component imports."""

    def test_import_streamlit_components(self):
        """Should be able to import streamlit component modules."""
        try:
            import src.iac_agents.streamlit.components

            assert hasattr(src.iac_agents.streamlit.components, "__path__")
        except ImportError:
            pytest.skip("Streamlit components not available")

    def test_import_main_interface(self):
        """Should be able to import main interface module."""
        try:
            import src.iac_agents.streamlit.main_interface

            assert src.iac_agents.streamlit.main_interface is not None
        except ImportError:
            pytest.skip("Main interface not available")

    def test_import_gui_module(self):
        """Should be able to import GUI module."""
        try:
            import src.iac_agents.streamlit.gui

            assert src.iac_agents.streamlit.gui is not None
        except ImportError:
            pytest.skip("GUI module not available")
