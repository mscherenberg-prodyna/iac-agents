resource "azurerm_storage_account" {
  # Missing name
  resource_group_name = 
  location = "invalid location"
  account_tier = "InvalidTier"
}