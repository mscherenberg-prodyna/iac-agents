"""Unit tests for autoscroll functionality."""

import pytest


@pytest.mark.unit
def test_enhanced_scroll_javascript():
    """Test that enhanced scroll JavaScript is properly formatted."""
    from iac_agents.templates.ui_loader import ui_loader

    # Load the enhanced scroll JavaScript
    js_content = ui_loader._loader.load_js_file("enhanced_scroll")

    # Check that the JavaScript contains key autoscroll functions
    assert "enhancedScrollToBottom" in js_content
    assert "setTimeout" in js_content
    assert "scrollIntoView" in js_content
    assert "parent.document" in js_content

    # Check for multiple fallback strategies
    assert "data-testid" in js_content
    assert "stChatMessage" in js_content
    assert "stMain" in js_content

    # Check for the setup function
    assert "setupEnhancedScroll" in js_content


@pytest.mark.unit
def test_main_css_scroll_improvements():
    """Test that CSS includes scroll improvements."""
    from iac_agents.templates.ui_loader import ui_loader

    # Load the main CSS content
    css_content = ui_loader._loader.load_css_file("main_styles")

    # Check for scroll behavior smooth
    assert "scroll-behavior: smooth" in css_content

    # Check for chat message improvements
    assert "stChatMessage" in css_content
    assert "scroll-margin-bottom" in css_content


@pytest.mark.unit
def test_gui_integration():
    """Test that GUI properly integrates autoscroll."""
    # This would normally require a full Streamlit test environment
    # For now, just verify imports work
    from iac_agents.streamlit.gui import main

    # Test that the function exists and is callable
    assert callable(main)
    assert main.__name__ == "main"
