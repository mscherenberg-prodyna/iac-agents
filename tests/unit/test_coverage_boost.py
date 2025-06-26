"""Coverage boost tests for specific uncovered lines."""

from unittest.mock import Mock, patch

import pytest

from src.iac_agents.agents.terraform_utils import enhance_terraform_template
from src.iac_agents.templates.template_manager import template_manager


class TestCoverageBoost:
    """Tests specifically designed to hit uncovered lines."""

    def test_enhance_terraform_template_minimal(self):
        """Test template enhancement with minimal parameters."""
        template = 'resource "test" "test" {}'
        result = enhance_terraform_template(template)

        # Should add terraform and provider blocks
        assert "terraform {" in result
        assert "required_providers" in result

    def test_enhance_terraform_template_custom_params(self):
        """Test template enhancement with custom parameters."""
        template = 'resource "test" "test" {}'
        result = enhance_terraform_template(
            template, project_name="custom-project", default_location="eastus"
        )

        assert "custom-project" in result
        assert "eastus" in result

    @patch("src.iac_agents.templates.template_manager.template_loader")
    def test_template_manager_error_handling(self, mock_loader):
        """Test template manager error handling during load."""
        mock_loader.load_all_prompt_templates.side_effect = Exception("Load error")
        mock_loader.load_all_terraform_templates.side_effect = Exception("Load error")

        from src.iac_agents.templates.template_manager import TemplateManager

        manager = TemplateManager()

        # Should handle errors gracefully
        assert manager._prompt_templates == {}
        assert manager._terraform_templates == {}

    def test_template_manager_terraform_fallback(self):
        """Test terraform template fallback to default."""
        result = template_manager.get_terraform_template("nonexistent_template")

        # Should return default template when specific one not found
        assert result is not None

    def test_template_manager_reload(self):
        """Test template manager reload functionality."""
        # Should not raise error
        template_manager.reload_templates()
        assert True  # Just verify no exception

    def test_terraform_variables_edge_cases(self):
        """Test terraform variable edge cases."""
        from src.iac_agents.agents.terraform_utils import TerraformVariableManager

        # Test with empty template
        variables = TerraformVariableManager.extract_variables_from_template("")
        assert variables == {}

        # Test validation with empty template
        is_valid, issues = TerraformVariableManager.validate_template_variables("")
        assert is_valid is True
        assert issues == []

    def test_logging_convenience_functions_with_details(self):
        """Test logging convenience functions with details parameter."""
        from src.iac_agents.logging_system import log_error, log_info, log_warning

        # These should not raise errors
        log_info("TestAgent", "Test message", {"key": "value"})
        log_warning("TestAgent", "Warning message", {"warning": True})
        log_error("TestAgent", "Error message", {"error_code": 500})
        assert True  # Just verify no exception
