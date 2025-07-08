"""Tests for TemplateLoader class."""

import json
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
from jinja2 import Template

from iac_agents.templates.template_loader import TemplateLoader


class TestTemplateLoader:
    """Test suite for TemplateLoader class."""

    def test_template_loader_initialization(self):
        """Test TemplateLoader initialization with default path."""
        loader = TemplateLoader()

        assert loader.base_path.name == "templates"
        assert hasattr(loader, "jinja_env")

    def test_template_loader_custom_path(self):
        """Test TemplateLoader initialization with custom path."""
        custom_path = Path("/custom/path")
        loader = TemplateLoader(base_path=custom_path)

        assert loader.base_path == custom_path

    @patch("builtins.open", new_callable=mock_open, read_data="test content")
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_text_file_success(self, mock_exists, mock_file):
        """Test successful text file loading."""
        loader = TemplateLoader()

        content = loader.load_text_file("test.txt")

        assert content == "test content"

    @patch("pathlib.Path.exists", return_value=False)
    def test_load_text_file_not_found(self, mock_exists):
        """Test text file loading when file doesn't exist."""
        loader = TemplateLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_text_file("nonexistent.txt")

    @patch.object(TemplateLoader, "load_text_file")
    def test_load_terraform_template(self, mock_load_text):
        """Test Terraform template loading."""
        mock_load_text.return_value = "terraform content"
        loader = TemplateLoader()

        content = loader.load_terraform_template("example")

        assert content == "terraform content"
        mock_load_text.assert_called_once_with("terraform/example.tf")

    def test_load_prompt_template(self):
        """Test prompt template loading."""
        loader = TemplateLoader()
        mock_template = Mock(spec=Template)

        with patch.object(loader, "jinja_env") as mock_jinja_env:
            mock_jinja_env.get_template.return_value = mock_template

            template = loader.load_prompt_template("test_prompt")

            assert template == mock_template
            mock_jinja_env.get_template.assert_called_once_with(
                "prompts/test_prompt.txt"
            )

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_json_data_success(self, mock_exists, mock_file):
        """Test successful JSON data loading."""
        loader = TemplateLoader()

        data = loader.load_json_data("test.json")

        assert data == {"key": "value"}

    @patch("pathlib.Path.exists", return_value=False)
    def test_load_json_data_not_found(self, mock_exists):
        """Test JSON data loading when file doesn't exist."""
        loader = TemplateLoader()

        with pytest.raises(FileNotFoundError):
            loader.load_json_data("nonexistent.json")

    @patch.object(TemplateLoader, "load_text_file")
    def test_load_html_template(self, mock_load_text):
        """Test HTML template loading."""
        mock_load_text.return_value = "<html>content</html>"
        loader = TemplateLoader()

        content = loader.load_html_template("example")

        assert content == "<html>content</html>"
        mock_load_text.assert_called_once_with("html/example.html")

    @patch.object(TemplateLoader, "load_json_data")
    def test_load_showcase_scenarios(self, mock_load_json):
        """Test showcase scenarios loading."""
        expected_data = {"scenarios": []}
        mock_load_json.return_value = expected_data
        loader = TemplateLoader()

        data = loader.load_showcase_scenarios()

        assert data == expected_data
        mock_load_json.assert_called_once_with("data/showcase_scenarios.json")
