"""Integration tests for template generation pipeline."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from iac_agents.agents.terraform_utils import (
    extract_terraform_template,
    is_valid_terraform_content,
    parse_terraform_providers,
)
from iac_agents.templates.template_manager import TemplateManager


class TestTemplatePipeline:
    """Test suite for template generation pipeline."""

    def test_terraform_template_extraction_and_validation(self):
        """Test terraform template extraction and validation pipeline."""
        test_data_path = Path(__file__).parent.parent / "test_data"
        with open(test_data_path / "llm_response_with_terraform.txt", "r") as f:
            llm_response = f.read()

        # Extract template from LLM response
        extracted_template = extract_terraform_template(llm_response)

        # Validate extracted template
        is_valid = is_valid_terraform_content(extracted_template)

        assert extracted_template != ""
        assert is_valid is True
        assert 'resource "aws_instance" "web"' in extracted_template

    @patch("iac_agents.templates.template_manager.template_loader")
    def test_template_manager_prompt_rendering(self, mock_template_loader):
        """Test template manager prompt rendering pipeline."""
        mock_template = Mock()
        mock_template.render.return_value = "Rendered prompt with context"
        mock_template_loader.load_all_prompt_templates.return_value = {
            "test_prompt": mock_template
        }
        mock_template_loader.load_all_terraform_templates.return_value = {}

        template_manager = TemplateManager()

        rendered_prompt = template_manager.get_prompt(
            "test_prompt", context="test context", role="engineer"
        )

        assert rendered_prompt == "Rendered prompt with context"
        mock_template.render.assert_called_once_with(
            context="test context", role="engineer"
        )

    def test_terraform_provider_parsing_pipeline(self):
        """Test terraform provider parsing pipeline."""
        test_data_path = Path(__file__).parent.parent / "test_data"
        with open(test_data_path / "terraform_init_output.txt", "r") as f:
            init_output = f.read()

        init_result = {
            "success": True,
            "stdout": init_output,
            "stderr": "",
            "returncode": 0,
        }

        # Parse providers from init output
        providers = parse_terraform_providers(init_result)

        # Validate parsed providers
        assert isinstance(providers, dict)
        assert len(providers) > 0
        assert "aws" in providers
        assert providers["aws"] == "5.31.0"

    @patch("iac_agents.templates.template_manager.template_loader")
    def test_template_fallback_mechanism(self, mock_template_loader):
        """Test template fallback mechanism in pipeline."""
        mock_template_loader.load_all_prompt_templates.return_value = {}
        mock_template_loader.load_all_terraform_templates.return_value = {
            "default": "default terraform template"
        }

        template_manager = TemplateManager()

        # Request non-existent template, should fallback to default
        template = template_manager.get_terraform_template("nonexistent_template")

        assert template == "default terraform template"

    def test_template_content_validation_pipeline(self):
        """Test template content validation pipeline."""
        test_data_path = Path(__file__).parent.parent / "test_data"
        with open(test_data_path / "valid_terraform_template.tf", "r") as f:
            terraform_content = f.read()

        # Test validation pipeline
        is_valid_basic = is_valid_terraform_content(terraform_content)
        is_valid_strict = is_valid_terraform_content(
            terraform_content, strict_validation=True
        )

        assert is_valid_basic is True
        assert is_valid_strict is True

    def test_invalid_template_rejection_pipeline(self):
        """Test that invalid templates are rejected in pipeline."""
        invalid_content = "This is just regular text without terraform syntax"

        # Should be rejected by validation
        is_valid = is_valid_terraform_content(invalid_content)

        assert is_valid is False

    def test_template_extraction_error_handling(self):
        """Test template extraction error handling."""
        # Test with empty response
        empty_extracted = extract_terraform_template("")
        assert empty_extracted == ""

        # Test with None response
        none_extracted = extract_terraform_template(None)
        assert none_extracted == ""

        # Test with response containing no terraform
        no_terraform_response = "This response contains no terraform code at all"
        no_terraform_extracted = extract_terraform_template(no_terraform_response)
        assert no_terraform_extracted == ""


@pytest.mark.integration
class TestTemplatePipelineIntegration:
    """Integration tests for complete template pipeline."""

    @patch("iac_agents.templates.template_manager.template_loader")
    def test_complete_template_pipeline(self, mock_template_loader):
        """Test complete template generation pipeline."""
        # Mock template manager setup
        mock_prompt_template = Mock()
        mock_prompt_template.render.return_value = "Generate infrastructure for web app"
        mock_template_loader.load_all_prompt_templates.return_value = {
            "cloud_engineer": mock_prompt_template
        }
        mock_template_loader.load_all_terraform_templates.return_value = {
            "default": 'terraform { required_providers { aws = "~> 5.0" } }'
        }

        template_manager = TemplateManager()

        # Step 1: Get rendered prompt
        prompt = template_manager.get_prompt(
            "cloud_engineer", requirements="web application"
        )

        # Step 2: Simulate LLM response
        llm_response = """
        Here's your terraform template:
        
        ```hcl
        resource "aws_instance" "web" {
          ami = "ami-12345"
          instance_type = "t2.micro"
        }
        ```
        """

        # Step 3: Extract template from response
        extracted_template = extract_terraform_template(llm_response)

        # Step 4: Validate extracted template
        is_valid = is_valid_terraform_content(
            extracted_template, strict_validation=True
        )

        # Verify pipeline works end-to-end
        assert prompt == "Generate infrastructure for web app"
        assert extracted_template != ""
        assert is_valid is True
        assert 'resource "aws_instance" "web"' in extracted_template
