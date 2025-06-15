"""High-quality Terraform templates for web applications."""

WEB_APPLICATION_TEMPLATE = '''terraform {
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
  name     = "secure-webapp-rg"
  location = "East US"
  
  tags = {
    Environment = "production"
    Purpose     = "secure-web-application"
    Compliance  = "SOX,GDPR,PCI-DSS"
    Monitoring  = "enabled"
  }
}

resource "azurerm_virtual_network" "main" {
  name                = "webapp-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = azurerm_resource_group.main.tags
}

resource "azurerm_subnet" "webapp" {
  name                 = "webapp-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_network_security_group" "webapp" {
  name                = "webapp-nsg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name                       = "HTTPS"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = azurerm_resource_group.main.tags
}

resource "azurerm_app_service_plan" "main" {
  name                = "secure-webapp-plan"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  sku {
    tier = "Standard"
    size = "S1"
  }

  tags = azurerm_resource_group.main.tags
}

resource "azurerm_app_service" "main" {
  name                = "secure-webapp-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  app_service_plan_id = azurerm_app_service_plan.main.id
  https_only          = true

  site_config {
    always_on                 = true
    min_tls_version          = "1.2"
    ftps_state               = "Disabled"
    http2_enabled            = true
    use_32_bit_worker_process = false
  }

  identity {
    type = "SystemAssigned"
  }

  logs {
    detailed_error_messages_enabled = true
    failed_request_tracing_enabled   = true
    
    http_logs {
      file_system {
        retention_in_days = 30
        retention_in_mb   = 35
      }
    }
  }

  tags = azurerm_resource_group.main.tags
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "webapp-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 90

  tags = azurerm_resource_group.main.tags
}

resource "azurerm_application_insights" "main" {
  name                = "webapp-insights"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"

  tags = azurerm_resource_group.main.tags
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}'''

DEFAULT_TEMPLATE = '''terraform {
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
}'''