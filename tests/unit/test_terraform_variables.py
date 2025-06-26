"""Unit tests for terraform variable management."""

import pytest

from src.iac_agents.agents.terraform_utils import TerraformVariableManager


class TestVariableExtraction:
    """Test variable extraction from templates."""

    def test_extract_simple_variable(self):
        """Test extracting a simple variable."""
        template = 'variable "test" { type = string }'
        vars = TerraformVariableManager.extract_variables_from_template(template)

        assert "test" in vars
        assert vars["test"]["name"] == "test"
        assert vars["test"]["required"] is True

    def test_extract_variable_with_default(self):
        """Test extracting variable with default value."""
        template = 'variable "env" { default = "dev" }'
        vars = TerraformVariableManager.extract_variables_from_template(template)

        assert vars["env"]["has_default"] is True
        assert vars["env"]["required"] is False


class TestVariableValidation:
    """Test variable validation."""

    def test_validate_all_variables_have_defaults(self):
        """All variables with defaults should be valid."""
        template = 'variable "test" { default = "value" }'
        is_valid, issues = TerraformVariableManager.validate_template_variables(
            template
        )

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_missing_defaults(self):
        """Variables without defaults should be invalid."""
        template = 'variable "test" { type = string }'
        is_valid, issues = TerraformVariableManager.validate_template_variables(
            template
        )

        assert is_valid is False
        assert len(issues) == 1
        assert "test" in issues[0]


class TestVariableInference:
    """Test variable value inference."""

    def test_infer_dev_environment(self):
        """Should infer dev environment from keywords."""
        requirements = "Create a development environment for testing"
        values = TerraformVariableManager.infer_variable_values_from_requirements(
            requirements
        )

        assert values["environment"] == "dev"

    def test_infer_production_environment(self):
        """Should infer production environment."""
        requirements = "Deploy to production"
        values = TerraformVariableManager.infer_variable_values_from_requirements(
            requirements
        )

        assert values["environment"] == "prod"

    def test_infer_location(self):
        """Should infer location from requirements."""
        requirements = "Deploy in eastus region"
        values = TerraformVariableManager.infer_variable_values_from_requirements(
            requirements
        )

        assert values["location"] == "eastus"
