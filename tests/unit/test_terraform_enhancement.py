"""Unit tests for terraform template enhancement."""

import pytest

from src.iac_agents.agents.terraform_utils import enhance_terraform_template


class TestEnhanceTerraformTemplate:
    """Test terraform template enhancement."""

    def test_adds_provider_config(self):
        """Should add provider configuration when missing."""
        template = 'resource "azurerm_resource_group" "main" { name = "test" }'
        result = enhance_terraform_template(template)

        assert "terraform {" in result
        assert 'provider "azurerm"' in result

    def test_preserves_existing_provider(self):
        """Should not duplicate existing provider config."""
        template = """
        terraform {
          required_providers {
            azurerm = { source = "hashicorp/azurerm" }
          }
        }
        resource "test" "test" {}
        """
        result = enhance_terraform_template(template)

        # Should only have one terraform block
        assert result.count("terraform {") == 1

    def test_adds_common_variables(self):
        """Should add standard variables."""
        template = 'resource "test" "test" {}'
        result = enhance_terraform_template(template, project_name="my-project")

        assert 'variable "environment"' in result
        assert 'variable "project_name"' in result
        assert 'default     = "my-project"' in result

    def test_preserves_existing_variables(self):
        """Should not duplicate existing variables."""
        template = """
        variable "environment" { default = "custom" }
        resource "test" "test" {}
        """
        result = enhance_terraform_template(template)

        # Should only have one environment variable
        assert result.count('variable "environment"') == 1
