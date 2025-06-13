"""Test the fixes for rate limiting and template extraction."""

from src.iac_agents.agents.supervisor_agent import SupervisorAgent
from src.iac_agents.logging_system import log_user_update


def test_template_extraction():
    """Test template extraction with various formats."""
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
        "I cannot generate infrastructure for this request."
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n🧪 Test Case {i+1}:")
        print(f"Input length: {len(test_case)} characters")
        
        template = supervisor._extract_template(test_case)
        
        print(f"Extracted template length: {len(template)} characters")
        if template:
            print(f"Template preview: {template[:100]}...")
        else:
            print("❌ No template extracted")


def test_simple_request():
    """Test a simple request with rate limiting protection."""
    log_user_update("🧪 Testing simple infrastructure request")
    
    supervisor = SupervisorAgent()
    
    # Simple test request
    simple_request = "I need a basic storage account for documents in Azure."
    
    print(f"📝 Processing request: {simple_request}")
    print("🔍 Watch console for agent activity...")
    
    try:
        response = supervisor.process_user_request(simple_request)
        print(f"\n✅ Request processed successfully!")
        print(f"Response length: {len(response)} characters")
        
        if "```hcl" in response:
            print("✅ Terraform template found in response")
        else:
            print("⚠️ No Terraform template in response")
            
    except Exception as e:
        print(f"❌ Error processing request: {e}")


if __name__ == "__main__":
    print("🔧 Testing Enhanced Infrastructure as Code AI Agent")
    print("=" * 60)
    
    # Test template extraction
    test_template_extraction()
    
    print("\n" + "=" * 60)
    
    # Test simple request
    test_simple_request()