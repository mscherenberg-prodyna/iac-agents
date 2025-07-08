"""Tests for extract_terraform_template function."""

from pathlib import Path

import pytest

from iac_agents.agents.terraform_utils import extract_terraform_template


class TestExtractTerraformTemplate:
    """Test suite for extract_terraform_template function."""

    def test_extract_from_hcl_code_block(self):
        """Test extracting terraform from HCL code block."""
        test_data_path = Path(__file__).parent.parent / "test_data"
        with open(test_data_path / "llm_response_with_terraform.txt", "r") as f:
            response = f.read()

        extracted = extract_terraform_template(response)

        assert 'resource "aws_instance" "web"' in extracted
        assert 'ami           = "ami-12345678"' in extracted
        assert 'instance_type = "t2.micro"' in extracted

    def test_extract_from_terraform_code_block(self):
        """Test extracting terraform from terraform code block."""
        response = '```terraform\nprovider "aws" {\n  region = "us-east-1"\n}\n```'

        extracted = extract_terraform_template(response)
        expected = 'provider "aws" {\n  region = "us-east-1"\n}'

        assert extracted == expected

    def test_extract_from_generic_code_block(self):
        """Test extracting terraform from generic code block."""
        response = (
            "```\n"
            'resource "aws_s3_bucket" "example" {\n'
            '  bucket = "my-terraform-bucket"\n'
            "}\n"
            "```"
        )

        extracted = extract_terraform_template(response)
        expected = (
            'resource "aws_s3_bucket" "example" {\n  bucket = "my-terraform-bucket"\n}'
        )

        assert extracted == expected

    def test_extract_with_multiple_code_blocks(self):
        """Test extracting terraform with multiple code blocks."""
        response = (
            "First block:\n"
            "```hcl\n"
            'resource "aws_instance" "short" {\n'
            '  ami = "ami-123"\n'
            "}\n"
            "```\n"
            "Second block:\n"
            "```hcl\n"
            'resource "aws_instance" "long" {\n'
            '  ami = "ami-12345"\n'
            '  instance_type = "t2.micro"\n'
            "  tags = {\n"
            '    Name = "example"\n'
            "  }\n"
            "}\n"
            "```"
        )

        extracted = extract_terraform_template(response)

        assert 'resource "aws_instance" "long"' in extracted
        assert "tags = {" in extracted

    def test_extract_with_no_terraform_content(self):
        """Test extracting with no terraform content."""
        response = (
            "This is just a regular text response.\n"
            "No terraform content here.\n"
            "```\n"
            'print("hello world")\n'
            "```"
        )

        extracted = extract_terraform_template(response)

        assert extracted == ""

    def test_extract_empty_or_none_response(self):
        """Test extracting from empty or None response."""
        assert extract_terraform_template("") == ""
        assert extract_terraform_template(None) == ""
