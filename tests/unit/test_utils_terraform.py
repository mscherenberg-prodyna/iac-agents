"""Unit tests for Terraform-related utilities in agents.utils module."""

from unittest.mock import patch

import pytest

from src.iac_agents.agents.utils import extract_terraform_template


class TestExtractTerraformTemplate:
    """Test extract_terraform_template function."""

    def test_extract_empty_input(self):
        """Test extracting template from empty input."""
        assert extract_terraform_template("") == ""
        assert extract_terraform_template(None) == ""

    def test_extract_hcl_code_block(self):
        """Test extracting template from HCL code block."""
        response = """
        Here's your Terraform template:
        
        ```hcl
        resource "azurerm_resource_group" "main" {
          name     = "rg-test"
          location = "West Europe"
        }
        ```
        
        This creates a resource group.
        """

        result = extract_terraform_template(response)
        assert "azurerm_resource_group" in result
        assert "rg-test" in result
        assert "West Europe" in result

    def test_extract_terraform_code_block(self):
        """Test extracting template from terraform code block."""
        response = """
        ```terraform
        terraform {
          required_providers {
            azurerm = {
              source = "hashicorp/azurerm"
            }
          }
        }
        ```
        """

        result = extract_terraform_template(response)
        assert "terraform {" in result
        assert "azurerm" in result

    def test_extract_generic_code_block(self):
        """Test extracting template from generic code block."""
        response = """
        ```
        resource "azurerm_storage_account" "example" {
          name                = "storageaccountname"
          resource_group_name = azurerm_resource_group.example.name
        }
        ```
        """

        with patch(
            "src.iac_agents.agents.utils.is_valid_terraform_content", return_value=True
        ):
            result = extract_terraform_template(response)
            assert "azurerm_storage_account" in result

    def test_extract_no_code_blocks(self):
        """Test extracting template without code blocks."""
        response = """
        resource "azurerm_resource_group" "main" {
          name     = "rg-test"
          location = "West Europe"
        }
        
        provider "azurerm" {
          features {}
        }
        """

        with patch(
            "src.iac_agents.agents.utils.is_valid_terraform_content", return_value=True
        ):
            result = extract_terraform_template(response)
            assert "azurerm_resource_group" in result
            assert "provider" in result

    def test_extract_multiple_hcl_blocks(self):
        """Test extracting template with multiple HCL blocks (returns longest)."""
        response = """
        Short block:
        ```hcl
        variable "test" {}
        ```
        
        Longer block:
        ```hcl
        resource "azurerm_resource_group" "main" {
          name     = "rg-test"
          location = "West Europe"
        }
        
        resource "azurerm_storage_account" "main" {
          name = "storage"
        }
        ```
        """

        result = extract_terraform_template(response)
        assert "azurerm_resource_group" in result
        assert "azurerm_storage_account" in result
        # Should contain the longer block
        assert len(result.split("\n")) > 2

    def test_extract_with_explanatory_text_filtering(self):
        """Test that explanatory text is filtered out properly."""
        response = """
        resource "azurerm_resource_group" "main" {
          name     = "rg-test"
          location = "West Europe"
        }
        
        If you need to customize this template, please modify the variables.
        This template creates basic infrastructure for your needs.
        """

        with patch(
            "src.iac_agents.agents.utils.is_valid_terraform_content", return_value=True
        ):
            result = extract_terraform_template(response)
            # Should stop before explanatory text
            assert "azurerm_resource_group" in result
            assert "customize" not in result
