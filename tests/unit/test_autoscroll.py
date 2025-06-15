"""Unit tests for autoscroll functionality."""

import pytest

@pytest.mark.unit
def test_autoscroll_javascript():
    """Test that autoscroll JavaScript is properly formatted."""
    from src.iac_agents.config.ui_styles import AUTO_SCROLL_JS
    
    # Check that the JavaScript contains key autoscroll functions
    assert "scrollToBottom" in AUTO_SCROLL_JS
    assert "setTimeout" in AUTO_SCROLL_JS
    assert "scrollIntoView" in AUTO_SCROLL_JS
    assert "parent.document" in AUTO_SCROLL_JS
    print("✅ Autoscroll JavaScript contains expected functions")
    
    # Check for multiple fallback strategies
    assert "data-testid" in AUTO_SCROLL_JS
    assert "stChatMessage" in AUTO_SCROLL_JS
    assert "stMain" in AUTO_SCROLL_JS
    print("✅ Autoscroll JavaScript contains fallback strategies")
    
    # Check for DOM mutation observer
    assert "MutationObserver" in AUTO_SCROLL_JS
    assert "observer.observe" in AUTO_SCROLL_JS
    print("✅ Autoscroll JavaScript includes DOM mutation observer")

@pytest.mark.unit
def test_css_scroll_improvements():
    """Test that CSS includes scroll improvements."""
    from src.iac_agents.config.ui_styles import MAIN_CSS
    
    # Check for scroll behavior smooth
    assert "scroll-behavior: smooth" in MAIN_CSS
    print("✅ CSS includes smooth scroll behavior")
    
    # Check for chat message improvements
    assert "stChatMessage" in MAIN_CSS
    assert "scroll-margin-bottom" in MAIN_CSS
    print("✅ CSS includes chat message scroll improvements")

@pytest.mark.unit
def test_enhanced_gui_integration():
    """Test that enhanced GUI properly integrates autoscroll."""
    # This would normally require a full Streamlit test environment
    # For now, just verify imports work
    from src.iac_agents.streamlit.enhanced_gui import display_chat_interface
    
    # Test that the function exists and is callable
    assert callable(display_chat_interface)
    assert display_chat_interface.__name__ == "display_chat_interface"

# Tests can be run with: python -m pytest tests/unit/test_autoscroll.py -v