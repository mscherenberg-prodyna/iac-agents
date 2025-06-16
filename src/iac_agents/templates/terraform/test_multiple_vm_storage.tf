resource "azurerm_storage_account" "test" {
  name = "test"
}
resource "azurerm_virtual_machine" "vm" {
  name = "testvm"
}