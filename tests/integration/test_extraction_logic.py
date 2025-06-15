"""Test the extraction logic directly."""

from src.iac_agents.agents.supervisor_agent import SupervisorAgent


def test_extraction_with_sample():
    """Test extraction with a sample response that mimics the issue."""
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

    print("🧪 Testing extraction logic with sample nested code blocks")
    print(f"Sample response length: {len(sample_response)} characters")
    print()
    
    # Test extraction
    extracted = supervisor._extract_template(sample_response)
    
    print(f"✅ Extracted template length: {len(extracted)} characters")
    print()
    print("📋 Extracted content:")
    print("-" * 40)
    print(extracted)
    print("-" * 40)
    
    # Check if it's valid terraform
    is_valid = supervisor._is_valid_terraform_content(extracted)
    print(f"\n🔍 Is valid Terraform content: {is_valid}")


if __name__ == "__main__":
    test_extraction_with_sample()