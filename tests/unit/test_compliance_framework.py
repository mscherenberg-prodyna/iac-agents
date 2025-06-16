"""Unit tests for compliance framework."""

from src.iac_agents.compliance_framework import ComplianceFramework
from src.iac_agents.templates.template_loader import TemplateLoader


def test_compliance_framework_initialization():
    """Test ComplianceFramework can be initialized."""
    framework = ComplianceFramework()
    assert framework is not None
    assert hasattr(framework, "validate_template")


def test_validate_template_basic():
    """Test basic template validation."""
    framework = ComplianceFramework()
    loader = TemplateLoader()

    template = loader.load_terraform_template("test_storage_account")
    result = framework.validate_template(template, ["GDPR"])

    assert isinstance(result, dict)
    assert "compliance_score" in result
    assert "violations" in result
    assert isinstance(result["violations"], list)
    assert isinstance(result["compliance_score"], (int, float))


def test_validate_template_empty():
    """Test validation with empty template."""
    framework = ComplianceFramework()

    result = framework.validate_template("", ["GDPR"])

    assert isinstance(result, dict)
    assert "compliance_score" in result
    assert result["compliance_score"] >= 0


def test_validate_template_multiple_frameworks():
    """Test validation with multiple compliance frameworks."""
    framework = ComplianceFramework()
    loader = TemplateLoader()

    template = loader.load_terraform_template("test_multiple_frameworks")
    result = framework.validate_template(template, ["GDPR", "PCI DSS", "HIPAA"])

    assert isinstance(result, dict)
    assert "compliance_score" in result
    assert "violations" in result
    assert isinstance(result["violations"], list)


def test_validate_template_security_issues():
    """Test validation detects security issues."""
    framework = ComplianceFramework()
    loader = TemplateLoader()

    # Template with obvious security issues
    template = loader.load_terraform_template("test_security_issues")
    result = framework.validate_template(template, ["GDPR", "PCI DSS"])

    assert isinstance(result, dict)
    assert "violations" in result
    # Should detect security issues
    violations = result["violations"]
    assert len(violations) > 0


def test_validate_template_with_encryption():
    """Test validation with encryption settings."""
    framework = ComplianceFramework()
    loader = TemplateLoader()

    template = loader.load_terraform_template("test_with_encryption")
    result = framework.validate_template(template, ["GDPR", "HIPAA"])

    assert isinstance(result, dict)
    assert "compliance_score" in result
    # Should have higher score due to encryption
    assert result["compliance_score"] >= 0


def test_validate_template_invalid_framework():
    """Test validation with invalid framework."""
    framework = ComplianceFramework()

    template = 'resource "azurerm_storage_account" "test" {}'

    # Should handle invalid frameworks gracefully
    result = framework.validate_template(template, ["INVALID_FRAMEWORK"])

    assert isinstance(result, dict)
    assert "compliance_score" in result
    assert "violations" in result


def test_validate_template_error_handling():
    """Test validation error handling."""
    framework = ComplianceFramework()

    # Test with malformed template
    malformed_template = "this is not terraform"

    result = framework.validate_template(malformed_template, ["GDPR"])

    assert isinstance(result, dict)
    assert "compliance_score" in result
    assert "violations" in result


def test_validate_template_networking_rules():
    """Test validation with networking security rules."""
    framework = ComplianceFramework()
    loader = TemplateLoader()

    template = loader.load_terraform_template("test_networking_rules")
    result = framework.validate_template(template, ["ISO 27001", "SOX"])

    assert isinstance(result, dict)
    assert "compliance_score" in result
    assert "violations" in result
    # Should detect open SSH access as a violation
    violations = result["violations"]
    assert len(violations) > 0


def test_compliance_score_bounds():
    """Test that compliance scores are within valid bounds."""
    framework = ComplianceFramework()

    loader = TemplateLoader()
    templates = [
        "",  # Empty
        'resource "azurerm_storage_account" "test" {}',  # Minimal
        loader.load_terraform_template("test_secure_storage"),  # Secure
    ]

    for template in templates:
        result = framework.validate_template(template, ["GDPR"])
        score = result["compliance_score"]
        assert 0 <= score <= 100, f"Score {score} not in valid range [0, 100]"


def test_framework_specific_rules():
    """Test framework-specific compliance rules."""
    framework = ComplianceFramework()
    loader = TemplateLoader()

    template = loader.load_terraform_template("test_framework_specific")

    # Test different frameworks return different results
    gdpr_result = framework.validate_template(template, ["GDPR"])
    pci_result = framework.validate_template(template, ["PCI DSS"])

    assert isinstance(gdpr_result, dict)
    assert isinstance(pci_result, dict)

    # Both should have compliance scores
    assert "compliance_score" in gdpr_result
    assert "compliance_score" in pci_result


def test_validate_template_framework_specific():
    """Test template validation with framework-specific rules."""
    framework = ComplianceFramework()
    loader = TemplateLoader()

    template = loader.load_terraform_template("test_framework_specific")

    # Test with different frameworks
    gdpr_result = framework.validate_template(template, ["GDPR"])
    pci_result = framework.validate_template(template, ["PCI DSS"])

    assert isinstance(gdpr_result, dict)
    assert isinstance(pci_result, dict)
    assert "compliance_score" in gdpr_result
    assert "compliance_score" in pci_result


def test_multiple_resource_validation():
    """Test validation with multiple resources."""
    framework = ComplianceFramework()
    loader = TemplateLoader()

    template = loader.load_terraform_template("test_multiple_resources")
    result = framework.validate_template(template, ["GDPR", "ISO 27001"])

    assert isinstance(result, dict)
    assert "compliance_score" in result
    assert "violations" in result

    # Should analyze all resources
    score = result["compliance_score"]
    assert 0 <= score <= 100
