"""Basic unit tests for terraform_utils module."""

import pytest

from src.iac_agents.agents.terraform_utils import is_valid_terraform_content


class TestValidateTerraformContent:
    """Test terraform content validation."""

    def test_empty_content_invalid(self):
        """Empty content should be invalid."""
        assert not is_valid_terraform_content("")
        assert not is_valid_terraform_content(None)

    def test_valid_terraform_content(self):
        """Valid terraform content should pass."""
        content = 'resource "azurerm_resource_group" "main" { name = "test" }'
        assert is_valid_terraform_content(content)

    def test_non_terraform_content_invalid(self):
        """Non-terraform content should be invalid."""
        content = "This is just plain text"
        assert not is_valid_terraform_content(content)

    def test_strict_validation_rejects_explanatory_text(self):
        """Strict validation should reject content with too much explanatory text."""
        content = """
        This is explanatory text
        More explanatory text
        Even more text
        resource "test" "test" { name = "test" }
        """
        assert is_valid_terraform_content(content, strict_validation=False)
        assert not is_valid_terraform_content(content, strict_validation=True)
