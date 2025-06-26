"""Unit tests for template manager."""

from unittest.mock import Mock, patch

import pytest

from src.iac_agents.templates.template_manager import TemplateManager


class TestTemplateManager:
    """Test TemplateManager class."""

    @patch("src.iac_agents.templates.template_manager.template_loader")
    def test_initialization(self, mock_loader):
        """Should initialize with loaded templates."""
        mock_loader.load_all_prompt_templates.return_value = {"test": "template"}
        mock_loader.load_all_terraform_templates.return_value = {"default": "tf"}

        manager = TemplateManager()

        assert manager._prompt_templates == {"test": "template"}
        assert manager._terraform_templates == {"default": "tf"}

    @patch("src.iac_agents.templates.template_manager.template_loader")
    def test_get_prompt_success(self, mock_loader):
        """Should return rendered prompt template."""
        mock_template = Mock()
        mock_template.render.return_value = "rendered content"
        mock_loader.load_all_prompt_templates.return_value = {"test": mock_template}
        mock_loader.load_all_terraform_templates.return_value = {}

        manager = TemplateManager()
        result = manager.get_prompt("test", var="value")

        assert result == "rendered content"
        mock_template.render.assert_called_once_with(var="value")

    @patch("src.iac_agents.templates.template_manager.template_loader")
    def test_get_prompt_not_found(self, mock_loader):
        """Should raise error for unknown prompt."""
        mock_loader.load_all_prompt_templates.return_value = {}
        mock_loader.load_all_terraform_templates.return_value = {}

        manager = TemplateManager()

        with pytest.raises(ValueError, match="Unknown prompt template"):
            manager.get_prompt("nonexistent")

    @patch("src.iac_agents.templates.template_manager.template_loader")
    def test_get_terraform_template(self, mock_loader):
        """Should return terraform template."""
        mock_loader.load_all_prompt_templates.return_value = {}
        mock_loader.load_all_terraform_templates.return_value = {
            "webapp": "terraform webapp content",
            "default": "default content",
        }

        manager = TemplateManager()

        assert manager.get_terraform_template("webapp") == "terraform webapp content"
        assert manager.get_terraform_template("nonexistent") == "default content"
