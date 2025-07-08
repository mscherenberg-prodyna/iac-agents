"""Tests for TemplateManager class."""

from unittest.mock import Mock, patch

import pytest
from jinja2 import Template

from iac_agents.templates.template_manager import TemplateManager


class TestTemplateManager:
    """Test suite for TemplateManager class."""

    @patch("iac_agents.templates.template_manager.template_loader")
    def test_template_manager_initialization(self, mock_template_loader):
        """Test TemplateManager initialization."""
        mock_template_loader.load_all_prompt_templates.return_value = {"test": Mock()}
        mock_template_loader.load_all_terraform_templates.return_value = {
            "test": "content"
        }

        manager = TemplateManager()

        assert hasattr(manager, "_prompt_templates")
        assert hasattr(manager, "_terraform_templates")

    @patch("iac_agents.templates.template_manager.template_loader")
    def test_get_prompt_success(self, mock_template_loader):
        """Test successful prompt retrieval."""
        mock_template = Mock(spec=Template)
        mock_template.render.return_value = "Rendered prompt"
        mock_template_loader.load_all_prompt_templates.return_value = {
            "test_prompt": mock_template
        }
        mock_template_loader.load_all_terraform_templates.return_value = {}

        manager = TemplateManager()
        prompt = manager.get_prompt("test_prompt", variable="value")

        assert prompt == "Rendered prompt"
        mock_template.render.assert_called_once_with(variable="value")

    @patch("iac_agents.templates.template_manager.template_loader")
    def test_get_prompt_not_found(self, mock_template_loader):
        """Test prompt retrieval when prompt doesn't exist."""
        mock_template_loader.load_all_prompt_templates.return_value = {}
        mock_template_loader.load_all_terraform_templates.return_value = {}

        manager = TemplateManager()

        with pytest.raises(ValueError, match="Unknown prompt template"):
            manager.get_prompt("nonexistent_prompt")

    @patch("iac_agents.templates.template_manager.template_loader")
    def test_get_terraform_template_success(self, mock_template_loader):
        """Test successful Terraform template retrieval."""
        templates = {"web_app": "web app template", "default": "default template"}
        mock_template_loader.load_all_prompt_templates.return_value = {}
        mock_template_loader.load_all_terraform_templates.return_value = templates

        manager = TemplateManager()
        template = manager.get_terraform_template("web_app")

        assert template == "web app template"

    @patch("iac_agents.templates.template_manager.template_loader")
    def test_get_terraform_template_fallback_to_default(self, mock_template_loader):
        """Test Terraform template retrieval falls back to default."""
        templates = {"default": "default template"}
        mock_template_loader.load_all_prompt_templates.return_value = {}
        mock_template_loader.load_all_terraform_templates.return_value = templates

        manager = TemplateManager()
        template = manager.get_terraform_template("nonexistent")

        assert template == "default template"

    @patch("iac_agents.templates.template_manager.template_loader")
    def test_list_available_prompts(self, mock_template_loader):
        """Test listing available prompts."""
        mock_template_loader.list_available_prompt_templates.return_value = [
            "prompt1",
            "prompt2",
        ]
        mock_template_loader.load_all_prompt_templates.return_value = {}
        mock_template_loader.load_all_terraform_templates.return_value = {}

        manager = TemplateManager()
        prompts = manager.list_available_prompts()

        assert prompts == ["prompt1", "prompt2"]

    @patch("iac_agents.templates.template_manager.template_loader")
    def test_list_available_terraform_templates(self, mock_template_loader):
        """Test listing available Terraform templates."""
        mock_template_loader.list_available_terraform_templates.return_value = [
            "template1",
            "template2",
        ]
        mock_template_loader.load_all_prompt_templates.return_value = {}
        mock_template_loader.load_all_terraform_templates.return_value = {}

        manager = TemplateManager()
        templates = manager.list_available_terraform_templates()

        assert templates == ["template1", "template2"]

    @patch("iac_agents.templates.template_manager.template_loader")
    def test_reload_templates(self, mock_template_loader):
        """Test template reloading."""
        mock_template_loader.load_all_prompt_templates.return_value = {}
        mock_template_loader.load_all_terraform_templates.return_value = {}

        manager = TemplateManager()
        manager.reload_templates()

        # Should be called twice: once during init, once during reload
        assert mock_template_loader.load_all_prompt_templates.call_count == 2
        assert mock_template_loader.load_all_terraform_templates.call_count == 2

    @patch("iac_agents.templates.template_manager.template_loader")
    @patch("builtins.print")
    def test_template_loading_exception_handling(
        self, mock_print, mock_template_loader
    ):
        """Test exception handling during template loading."""
        mock_template_loader.load_all_prompt_templates.side_effect = Exception(
            "Load error"
        )

        manager = TemplateManager()

        assert manager._prompt_templates == {}
        assert manager._terraform_templates == {}
        mock_print.assert_called_once_with(
            "Warning: Failed to load templates: Load error"
        )
