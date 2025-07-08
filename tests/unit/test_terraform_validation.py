"""Tests for terraform content validation functions."""

from pathlib import Path

import pytest

from iac_agents.agents.terraform_utils import is_valid_terraform_content


class TestIsValidTerraformContent:
    """Test suite for is_valid_terraform_content function."""

    def test_valid_terraform_content(self):
        """Test valid terraform content validation."""
        test_data_path = Path(__file__).parent.parent / "test_data"
        with open(test_data_path / "valid_terraform_template.tf", "r") as f:
            valid_content = f.read()

        assert is_valid_terraform_content(valid_content) is True

    def test_empty_content_validation(self):
        """Test empty content validation."""
        assert is_valid_terraform_content("") is False
        assert is_valid_terraform_content("   ") is False

    def test_none_content_validation(self):
        """Test None content validation."""
        assert is_valid_terraform_content(None) is False

    def test_content_without_terraform_keywords(self):
        """Test content without terraform keywords."""
        invalid_content = "This is just regular text with { and } and = signs"

        assert is_valid_terraform_content(invalid_content) is False

    def test_content_without_hcl_syntax(self):
        """Test content with terraform keywords but no HCL syntax."""
        invalid_content = "terraform provider resource variable output"

        assert is_valid_terraform_content(invalid_content) is False

    def test_strict_validation_with_explanatory_text(self):
        """Test strict validation with excessive explanatory text."""
        content_with_explanations = (
            "This is a terraform configuration.\n"
            "It creates resources in AWS.\n"
            "Please note that you need credentials.\n"
            "The template is comprehensive.\n"
            "You should review it carefully.\n"
            'resource "aws_instance" "example" {\n'
            '  ami = "ami-12345"\n'
            "}\n"
        )

        assert (
            is_valid_terraform_content(
                content_with_explanations, strict_validation=False
            )
            is True
        )
        assert (
            is_valid_terraform_content(
                content_with_explanations, strict_validation=True
            )
            is False
        )

    def test_strict_validation_with_comments(self):
        """Test strict validation with valid content and comments."""
        content_with_comments = (
            "# This is a comment\n"
            'resource "aws_instance" "example" {\n'
            '  ami = "ami-12345"\n'
            '  instance_type = "t2.micro"\n'
            "}\n"
            'output "instance_id" {\n'
            "  value = aws_instance.example.id\n"
            "}"
        )

        assert (
            is_valid_terraform_content(content_with_comments, strict_validation=True)
            is True
        )

    def test_basic_terraform_blocks(self):
        """Test basic terraform block validation."""
        terraform_block = 'terraform { required_providers { aws = "~> 5.0" } }'
        provider_block = 'provider "aws" { region = "us-east-1" }'
        variable_block = 'variable "name" { type = string }'

        assert is_valid_terraform_content(terraform_block) is True
        assert is_valid_terraform_content(provider_block) is True
        assert is_valid_terraform_content(variable_block) is True
