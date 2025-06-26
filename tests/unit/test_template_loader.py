"""Unit tests for template loader."""

from unittest.mock import Mock, mock_open, patch

import pytest

from src.iac_agents.templates.template_loader import TemplateLoader


class TestTemplateLoader:
    """Test TemplateLoader class."""

    @patch("src.iac_agents.templates.template_loader.Path")
    def test_get_prompt_templates_dir(self, mock_path):
        """Should return prompts directory path."""
        loader = TemplateLoader()
        mock_path.return_value = Mock()

        result = loader.get_prompt_templates_dir()
        assert result is not None

    @patch("src.iac_agents.templates.template_loader.Path")
    def test_list_available_prompt_templates(self, mock_path):
        """Should list available prompt templates."""
        loader = TemplateLoader()

        # Mock directory with .txt files
        mock_dir = Mock()
        mock_dir.exists.return_value = True
        mock_dir.glob.return_value = [Mock(stem="template1"), Mock(stem="template2")]
        mock_path.return_value = mock_dir

        result = loader.list_available_prompt_templates()
        assert "template1" in result
        assert "template2" in result

    @patch("src.iac_agents.templates.template_loader.Path")
    def test_list_available_terraform_templates(self, mock_path):
        """Should list available terraform templates."""
        loader = TemplateLoader()

        mock_dir = Mock()
        mock_dir.exists.return_value = True
        mock_dir.glob.return_value = [Mock(stem="webapp"), Mock(stem="database")]
        mock_path.return_value = mock_dir

        result = loader.list_available_terraform_templates()
        assert "webapp" in result
        assert "database" in result
