variable "storage_name" {
  description = "Name of the storage account"
  type        = string
  default     = "defaultstorage"
}

resource "azurerm_storage_account" "test" {
  name                = var.storage_name
  resource_group_name = "test-rg"
  location           = "East US"
  account_tier       = "Standard"
  account_replication_type = "LRS"
}