"""Unit tests for UI loader."""

from unittest.mock import Mock, patch

import pytest

from src.iac_agents.templates.ui_loader import UIStyleLoader, ui_loader


class TestUIStyleLoader:
    """Test UI style loader class."""

    @patch("src.iac_agents.templates.ui_loader.template_loader")
    def test_get_main_css(self, mock_template_loader):
        """Should load and wrap CSS content."""
        mock_template_loader.load_css_file.return_value = "body { color: red; }"

        loader = UIStyleLoader()
        result = loader.get_main_css()

        assert "<style>" in result
        assert "body { color: red; }" in result
        assert "</style>" in result

    @patch("src.iac_agents.templates.ui_loader.template_loader")
    def test_get_activity_entry_template(self, mock_template_loader):
        """Should load HTML template."""
        mock_template_loader.load_html_template.return_value = "<div>{agent_name}</div>"

        loader = UIStyleLoader()
        result = loader.get_activity_entry_template()

        assert "<div>{agent_name}</div>" == result

    @patch("src.iac_agents.templates.ui_loader.template_loader")
    def test_format_activity_entry(self, mock_template_loader):
        """Should format activity entry with template."""
        mock_template_loader.load_html_template.return_value = (
            "<div>{timestamp} - {agent_name}: {activity_message}</div>"
        )

        loader = UIStyleLoader()
        result = loader.format_activity_entry("12:00", "TestAgent", "Testing")

        assert "12:00 - TestAgent: Testing" in result

    def test_global_ui_loader_exists(self):
        """Should have global ui_loader instance."""
        assert ui_loader is not None
        assert isinstance(ui_loader, UIStyleLoader)
