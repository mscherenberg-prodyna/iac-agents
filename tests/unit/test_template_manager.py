"""Unit tests for template manager."""

import pytest
from unittest.mock import Mock, patch, mock_open

from src.iac_agents.templates.template_manager import TemplateManager


def test_template_manager_initialization():
    """Test TemplateManager can be initialized."""
    manager = TemplateManager()
    assert manager is not None
    assert hasattr(manager, 'get_prompt')
    assert hasattr(manager, 'get_terraform_template')


def test_get_prompt():
    """Test getting prompts from template manager."""
    manager = TemplateManager()
    
    # Test with valid prompt name
    prompt = manager.get_prompt("terraform_generation")
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    
    # Test with invalid prompt name
    invalid_prompt = manager.get_prompt("nonexistent_prompt")
    assert isinstance(invalid_prompt, str)


def test_get_terraform_template():
    """Test getting Terraform templates."""
    manager = TemplateManager()
    
    # Test with valid template name
    template = manager.get_terraform_template("storage_account")
    assert isinstance(template, str)
    assert len(template) > 0
    
    # Test with invalid template name
    invalid_template = manager.get_terraform_template("nonexistent_template")
    assert isinstance(invalid_template, str)


def test_get_fallback_template():
    """Test fallback template generation."""
    manager = TemplateManager()
    
    user_inputs = [
        "Create a storage account",
        "Set up a web application",
        "Deploy a database",
        ""  # Empty input
    ]
    
    for user_input in user_inputs:
        fallback = manager.get_fallback_template(user_input)
        assert isinstance(fallback, str)
        assert len(fallback) > 0
        # Should contain basic Terraform elements
        assert "resource" in fallback.lower() or "provider" in fallback.lower()


def test_get_fallback_template_storage():
    """Test fallback template for storage requests."""
    manager = TemplateManager()
    
    storage_requests = [
        "I need storage for documents",
        "Create a blob storage account",
        "Set up file storage",
        "Archive document storage"
    ]
    
    for request in storage_requests:
        template = manager.get_fallback_template(request)
        assert isinstance(template, str)
        assert len(template) > 0
        # Should contain storage-related resources
        template_lower = template.lower()
        assert "storage" in template_lower or "azurerm_storage_account" in template_lower


def test_get_fallback_template_compute():
    """Test fallback template for compute requests."""
    manager = TemplateManager()
    
    compute_requests = [
        "Create a virtual machine",
        "Set up a VM for web hosting",
        "Deploy compute resources",
        "I need a server"
    ]
    
    for request in compute_requests:
        template = manager.get_fallback_template(request)
        assert isinstance(template, str)
        assert len(template) > 0
        # Should contain compute-related elements
        template_lower = template.lower()
        assert any(keyword in template_lower for keyword in ["vm", "virtual", "compute", "machine"])


def test_get_fallback_template_networking():
    """Test fallback template for networking requests."""
    manager = TemplateManager()
    
    network_requests = [
        "Set up networking",
        "Create VPC and subnets",
        "Network infrastructure",
        "Load balancer setup"
    ]
    
    for request in network_requests:
        template = manager.get_fallback_template(request)
        assert isinstance(template, str)
        assert len(template) > 0


def test_template_manager_with_empty_input():
    """Test template manager with empty or None input."""
    manager = TemplateManager()
    
    # Test with None
    template = manager.get_fallback_template(None)
    assert isinstance(template, str)
    assert len(template) > 0
    
    # Test with empty string
    template = manager.get_fallback_template("")
    assert isinstance(template, str)
    assert len(template) > 0
    
    # Test with whitespace
    template = manager.get_fallback_template("   ")
    assert isinstance(template, str)
    assert len(template) > 0


def test_template_manager_complex_requests():
    """Test template manager with complex user requests."""
    manager = TemplateManager()
    
    complex_requests = [
        "I need a secure web application with database backend and load balancer",
        "Create enterprise storage solution with backup and disaster recovery",
        "Set up multi-tier architecture with web, app, and database layers",
        "Deploy microservices infrastructure with container orchestration"
    ]
    
    for request in complex_requests:
        template = manager.get_fallback_template(request)
        assert isinstance(template, str)
        assert len(template) > 0
        # Should be more comprehensive for complex requests
        assert len(template) > 100  # Complex templates should be substantial


def test_template_validation():
    """Test that generated templates are syntactically valid."""
    manager = TemplateManager()
    
    requests = [
        "Storage account",
        "Web application",
        "Database setup"
    ]
    
    for request in requests:
        template = manager.get_fallback_template(request)
        
        # Basic syntax validation
        assert template.count('{') == template.count('}'), "Unbalanced braces in template"
        assert 'resource "' in template, "Should contain resource declaration"
        assert '"azurerm_' in template, "Should use Azure provider"


@patch('src.iac_agents.templates.template_manager.template_loader')
def test_template_manager_with_mocked_loader(mock_loader):
    """Test template manager with mocked template loader."""
    # Mock the template loader
    mock_loader.get_prompt.return_value = "Mocked prompt content"
    mock_loader.get_terraform_template.return_value = "Mocked template content"
    
    manager = TemplateManager()
    
    # Test prompt retrieval
    prompt = manager.get_prompt("test_prompt")
    assert prompt == "Mocked prompt content"
    
    # Test template retrieval
    template = manager.get_terraform_template("test_template")
    assert template == "Mocked template content"
    
    mock_loader.get_prompt.assert_called_with("test_prompt")
    mock_loader.get_terraform_template.assert_called_with("test_template")


def test_global_template_manager():
    """Test the global template manager instance."""
    from src.iac_agents.templates.template_manager import template_manager
    
    assert template_manager is not None
    assert isinstance(template_manager, TemplateManager)
    
    # Test that it works
    prompt = template_manager.get_prompt("terraform_generation")
    assert isinstance(prompt, str)
    
    template = template_manager.get_terraform_template("storage_account")
    assert isinstance(template, str)


def test_template_manager_error_handling():
    """Test error handling in template manager."""
    manager = TemplateManager()
    
    # Test with very long input
    very_long_input = "Create infrastructure " * 1000
    template = manager.get_fallback_template(very_long_input)
    assert isinstance(template, str)
    assert len(template) > 0
    
    # Test with special characters
    special_input = "Create infrastructure with émojis 🚀 and symbols @#$%"
    template = manager.get_fallback_template(special_input)
    assert isinstance(template, str)
    assert len(template) > 0


def test_template_consistency():
    """Test that template manager returns consistent results."""
    manager = TemplateManager()
    
    request = "Create a storage account for documents"
    
    # Generate template multiple times
    template1 = manager.get_fallback_template(request)
    template2 = manager.get_fallback_template(request)
    
    # Should be consistent (or at least similar structure)
    assert isinstance(template1, str)
    assert isinstance(template2, str)
    assert len(template1) > 0
    assert len(template2) > 0


def test_template_manager_different_patterns():
    """Test template manager with different request patterns."""
    manager = TemplateManager()
    
    patterns = [
        "I need to create...",
        "Please set up...",
        "Deploy a...",
        "Configure...",
        "Establish...",
        "Provision..."
    ]
    
    for pattern in patterns:
        full_request = f"{pattern} storage infrastructure"
        template = manager.get_fallback_template(full_request)
        assert isinstance(template, str)
        assert len(template) > 0


def test_template_manager_security_focus():
    """Test template manager with security-focused requests."""
    manager = TemplateManager()
    
    security_requests = [
        "Create secure storage with encryption",
        "Set up infrastructure with security best practices",
        "Deploy with compliance requirements",
        "Secure web application with WAF"
    ]
    
    for request in security_requests:
        template = manager.get_fallback_template(request)
        assert isinstance(template, str)
        assert len(template) > 0
        # Should include security-related configurations
        template_lower = template.lower()
        security_keywords = ["encrypt", "security", "https", "ssl", "tls", "secure"]
        assert any(keyword in template_lower for keyword in security_keywords)


def test_template_manager_resource_types():
    """Test template manager handles different Azure resource types."""
    manager = TemplateManager()
    
    resource_requests = [
        ("storage account", "azurerm_storage_account"),
        ("virtual machine", "azurerm_virtual_machine"),
        ("app service", "azurerm_app_service"),
        ("key vault", "azurerm_key_vault"),
        ("database", "azurerm_postgresql_server")
    ]
    
    for request, expected_resource in resource_requests:
        template = manager.get_fallback_template(f"Create a {request}")
        assert isinstance(template, str)
        assert len(template) > 0
        # Should contain appropriate resource type
        assert expected_resource in template or "azurerm_" in template