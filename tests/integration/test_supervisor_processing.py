"""Test supervisor agent request processing and template extraction capabilities."""

from src.iac_agents.agents.supervisor_agent import SupervisorAgent
from src.iac_agents.logging_system import log_user_update


def test_terraform_extraction():
    """Test that supervisor agent correctly extracts Terraform templates from various response formats including HCL code blocks, direct terraform content, empty responses, and non-terraform responses."""
    supervisor = SupervisorAgent()

    # Test cases for template extraction
    test_cases = [
        # Standard HCL format
        """Here's your infrastructure:

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

resource "azurerm_storage_account" "example" {
  name                     = "examplestorageacct"
  resource_group_name      = "example"
  location                 = "West US"
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
```

This will create a storage account for your documents.
""",
        # No code blocks, direct terraform
        """Based on your requirements, I recommend:

terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
    }
  }
}

resource "azurerm_resource_group" "main" {
  name     = "example-rg"
  location = "East US"
}

This creates a basic resource group.""",
        # Empty response
        "",
        # Response with no terraform
        "I cannot generate infrastructure for this request.",
    ]

    for i, test_case in enumerate(test_cases):
        template = supervisor._extract_template(test_case)

        # Verify extraction behavior
        if i < 2:  # First two cases should extract templates
            assert template
            assert len(template) > 0
        else:  # Last two cases should not extract templates
            assert not template or len(template) == 0


def test_basic_request_processing():
    """Test that supervisor agent can process simple infrastructure requests and return appropriate responses with rate limiting protection."""
    log_user_update("Testing simple infrastructure request")

    supervisor = SupervisorAgent()

    # Simple test request
    simple_request = "I need a basic storage account for documents in Azure."

    try:
        response = supervisor.process_user_request(simple_request)

        # Verify response
        assert response
        assert len(response) > 0

        # Check if response contains expected infrastructure content
        response_lower = response.lower()
        assert "azure" in response_lower or "storage" in response_lower

    except Exception as e:
        # If there's an error, fail the test
        assert False, f"Error processing request: {e}"


if __name__ == "__main__":
    # Test template extraction
    test_template_extraction()

    # Test simple request
    test_simple_request()
