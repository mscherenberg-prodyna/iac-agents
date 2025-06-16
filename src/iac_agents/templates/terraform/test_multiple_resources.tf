resource "azurerm_resource_group" "main" {
  name     = "test-rg"
  location = "East US"
}

resource "azurerm_storage_account" "test" {
  name                     = "mystorageaccount"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  enable_https_traffic_only = true
  allow_blob_public_access  = false
}

resource "azurerm_key_vault" "test" {
  name                = "test-keyvault"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  
  enabled_for_disk_encryption = true
  purge_protection_enabled    = true
}