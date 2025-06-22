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
  name     = "secure-infrastructure-rg"
  location = "East US"

  tags = {
    Environment = "production"
    Purpose     = "secure-infrastructure"
    Compliance  = "enterprise-standards"
    ManagedBy   = "terraform"
    Monitoring  = "enabled"
  }
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "infrastructure-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 90

  tags = azurerm_resource_group.main.tags
}