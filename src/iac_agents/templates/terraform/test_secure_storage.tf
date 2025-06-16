resource "azurerm_storage_account" "secure" {
  enable_https_traffic_only = true
  allow_blob_public_access  = false
  min_tls_version          = "TLS1_2"
}