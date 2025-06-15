"""Test Terraform template extraction from nested code blocks."""

from src.iac_agents.agents.supervisor_agent import SupervisorAgent


def test_nested_code_blocks():
    """Test extraction of Terraform templates from responses with nested HCL code blocks that previously caused parsing issues."""
    supervisor = SupervisorAgent()

    # Simulate the problematic response format
    sample_response = """## Generated Terraform Template

```hcl
A good solution for storing documents for legal retention is to use Azure Blob Storage with immutable policies. Below is a Terraform template:

```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = "legal-docs-rg"
  location = "East US"
}

resource "azurerm_storage_account" "main" {
  name                     = "legaldocsstorage"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
```
```"""

    # Test extraction
    extracted = supervisor._extract_template(sample_response)

    # Check if it's valid terraform
    is_valid = supervisor._is_valid_terraform_content(extracted)

    # Verify extraction worked correctly
    assert extracted
    assert len(extracted) > 0
    assert "terraform" in extracted.lower()
    assert "azurerm" in extracted.lower()
    assert is_valid


if __name__ == "__main__":
    test_extraction_with_sample()
