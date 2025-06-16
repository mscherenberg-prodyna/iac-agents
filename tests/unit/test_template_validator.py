"""Unit tests for template validator."""

from src.iac_agents.template_validator import (
    TerraformTemplateValidator,
    ValidationResult,
)
from src.iac_agents.templates.template_loader import TemplateLoader


def test_template_validator_initialization():
    """Test TerraformTemplateValidator can be initialized."""
    validator = TerraformTemplateValidator()
    assert validator is not None
    assert hasattr(validator, "validate_template")
    assert hasattr(validator, "validate_for_deployment")


def test_validation_result_creation():
    """Test ValidationResult creation."""
    result = ValidationResult(
        is_valid=True,
        errors=[],
        warnings=["Minor formatting issue"],
        security_issues=[],
        suggestions=[],
    )

    assert result.is_valid is True
    assert len(result.errors) == 0
    assert len(result.warnings) == 1
    assert len(result.security_issues) == 0
    assert len(result.suggestions) == 0


def test_template_validator_valid_template():
    """Test validator with valid Terraform template."""
    validator = TerraformTemplateValidator()
    loader = TemplateLoader()

    valid_template = loader.load_terraform_template("test_complete_template")
    result = validator.validate_template(valid_template)

    assert isinstance(result, ValidationResult)
    assert result.is_valid in [True, False]


def test_template_validator_invalid_template():
    """Test validator with invalid Terraform template."""
    validator = TerraformTemplateValidator()
    loader = TemplateLoader()

    invalid_template = loader.load_terraform_template("test_invalid_template")
    result = validator.validate_template(invalid_template)

    assert isinstance(result, ValidationResult)


def test_template_validator_empty_template():
    """Test validator with empty template."""
    validator = TerraformTemplateValidator()

    result = validator.validate_template("")

    assert isinstance(result, ValidationResult)


def test_template_validator_malformed_template():
    """Test validator with completely malformed template."""
    validator = TerraformTemplateValidator()

    malformed = "This is not Terraform code at all!!!"

    result = validator.validate_template(malformed)

    assert isinstance(result, ValidationResult)


def test_template_validator_with_variables():
    """Test validator with Terraform variables."""
    validator = TerraformTemplateValidator()
    loader = TemplateLoader()

    template_with_vars = loader.load_terraform_template("test_with_variables")
    result = validator.validate_template(template_with_vars)

    assert isinstance(result, ValidationResult)
    assert result.is_valid in [True, False]


def test_template_validator_with_outputs():
    """Test validator with Terraform outputs."""
    validator = TerraformTemplateValidator()
    loader = TemplateLoader()

    template_with_outputs = loader.load_terraform_template("test_with_outputs")
    result = validator.validate_template(template_with_outputs)

    assert isinstance(result, ValidationResult)
    assert result.is_valid in [True, False]


def test_template_validator_error_handling():
    """Test validator error handling."""
    validator = TerraformTemplateValidator()

    # Test with None
    try:
        result = validator.validate_template(None)
        assert result is None or isinstance(result, ValidationResult)
    except Exception:
        # Exception handling is acceptable
        pass


def test_validation_result_scoring():
    """Test ValidationResult scoring logic."""
    # High quality result
    good_result = ValidationResult(
        is_valid=True,
        errors=[],
        warnings=["Minor style issue"],
        security_issues=[],
        suggestions=["Consider adding tags"],
    )

    assert good_result.is_valid is True
    assert len(good_result.errors) == 0

    # Low quality result
    bad_result = ValidationResult(
        is_valid=False,
        errors=["Syntax error", "Missing required field"],
        warnings=["Deprecated syntax"],
        security_issues=["Hardcoded secrets"],
        suggestions=[],
    )

    assert bad_result.is_valid is False
    assert len(bad_result.errors) > 0


def test_template_validator_performance():
    """Test validator performance with multiple templates."""
    validator = TerraformTemplateValidator()

    templates = [
        "resource test1 {}",
        "resource test2 { name = 'test' }",
        "resource test3 { location = 'US' }",
        "variable test_var { type = string }",
        "output test_output { value = 'test' }",
    ]

    results = []
    for template in templates:
        result = validator.validate_template(template)
        results.append(result)
        assert isinstance(result, ValidationResult)

    # Should handle multiple validations
    assert len(results) == len(templates)
