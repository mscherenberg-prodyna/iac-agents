"""Tests for TemplateLoader listing functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from iac_agents.templates.template_loader import TemplateLoader


class TestTemplateLoaderListing:
    """Test suite for TemplateLoader listing functionality."""

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.glob")
    def test_list_available_terraform_templates(self, mock_glob, mock_exists):
        """Test listing available Terraform templates."""
        mock_files = [
            Mock(stem="template1"),
            Mock(stem="template2"),
            Mock(stem="template3"),
        ]
        mock_glob.return_value = mock_files
        loader = TemplateLoader()

        templates = loader.list_available_terraform_templates()

        assert templates == ["template1", "template2", "template3"]

    @patch("pathlib.Path.exists", return_value=False)
    def test_list_terraform_templates_directory_not_exists(self, mock_exists):
        """Test listing Terraform templates when directory doesn't exist."""
        loader = TemplateLoader()

        templates = loader.list_available_terraform_templates()

        assert templates == []

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.glob")
    def test_list_available_prompt_templates(self, mock_glob, mock_exists):
        """Test listing available prompt templates."""
        mock_files = [Mock(stem="prompt1"), Mock(stem="prompt2")]
        mock_glob.return_value = mock_files
        loader = TemplateLoader()

        prompts = loader.list_available_prompt_templates()

        assert prompts == ["prompt1", "prompt2"]

    @patch("pathlib.Path.exists", return_value=False)
    def test_list_prompt_templates_directory_not_exists(self, mock_exists):
        """Test listing prompt templates when directory doesn't exist."""
        loader = TemplateLoader()

        prompts = loader.list_available_prompt_templates()

        assert prompts == []

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.glob")
    def test_list_available_html_templates(self, mock_glob, mock_exists):
        """Test listing available HTML templates."""
        mock_files = [Mock(stem="index"), Mock(stem="layout")]
        mock_glob.return_value = mock_files
        loader = TemplateLoader()

        html_templates = loader.list_available_html_templates()

        assert html_templates == ["index", "layout"]

    @patch("pathlib.Path.exists", return_value=False)
    def test_list_html_templates_directory_not_exists(self, mock_exists):
        """Test listing HTML templates when directory doesn't exist."""
        loader = TemplateLoader()

        html_templates = loader.list_available_html_templates()

        assert html_templates == []

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.glob")
    def test_load_all_terraform_templates(self, mock_glob, mock_exists):
        """Test loading all Terraform templates."""
        mock_files = [Mock(stem="template1")]
        mock_glob.return_value = mock_files

        with patch.object(TemplateLoader, "load_terraform_template") as mock_load:
            mock_load.return_value = "terraform content"
            loader = TemplateLoader()

            templates = loader.load_all_terraform_templates()

            assert templates == {"template1": "terraform content"}

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.glob")
    def test_load_all_prompt_templates(self, mock_glob, mock_exists):
        """Test loading all prompt templates."""
        mock_files = [Mock(stem="prompt1")]
        mock_glob.return_value = mock_files

        with patch.object(TemplateLoader, "load_prompt_template") as mock_load:
            mock_template = Mock()
            mock_load.return_value = mock_template
            loader = TemplateLoader()

            prompts = loader.load_all_prompt_templates()

            assert prompts == {"prompt1": mock_template}
