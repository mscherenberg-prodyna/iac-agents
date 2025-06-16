resource "azurerm_storage_account" "test" {
  name                = "teststorage"
  resource_group_name = "test-rg"
  location           = "East US"
  account_tier       = "Standard"
  account_replication_type = "LRS"
}

output "storage_account_id" {
  description = "ID of the storage account"
  value       = azurerm_storage_account.test.id
}