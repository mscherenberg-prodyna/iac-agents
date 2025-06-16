"""Integration tests for template generation system."""

import pytest

from src.iac_agents.agents import SupervisorAgent


@pytest.mark.integration
@pytest.mark.requires_azure
@pytest.mark.requires_openai
def test_document_storage_request():
    """Test document storage infrastructure request processing."""
    supervisor = SupervisorAgent()

    request = (
        "I have a number of documents that I need to keep for legal reasons. "
        "What would be a good way to do this with Azure infrastructure?"
    )

    response = supervisor.process_user_request(request)

    # Verify response is generated
    assert response, "Response should not be empty"
    assert len(response) > 100, "Response should be substantial"

    # Verify HCL template is present
    assert "```hcl" in response, "Response should contain HCL code block"

    # Extract and validate template
    start = response.find("```hcl") + 6
    end = response.find("```", start)
    template = response[start:end].strip()

    assert template, "Template should not be empty"
    assert len(template) > 50, "Template should be substantial"
    assert (
        "terraform" in template.lower()
    ), "Template should contain terraform configuration"
    assert "azurerm" in template.lower(), "Template should use Azure provider"


@pytest.mark.integration
@pytest.mark.requires_azure
@pytest.mark.requires_openai
def test_web_application_request():
    """Test web application infrastructure request processing."""
    supervisor = SupervisorAgent()

    request = (
        "I need to deploy a secure web application with auto-scaling and monitoring."
    )

    response = supervisor.process_user_request(request)

    # Verify response is generated
    assert response, "Response should not be empty"
    assert "```hcl" in response, "Response should contain HCL code block"

    # Extract template
    start = response.find("```hcl") + 6
    end = response.find("```", start)
    template = response[start:end].strip()

    assert (
        "terraform" in template.lower()
    ), "Template should contain terraform configuration"
    assert (
        "resource" in template.lower()
    ), "Template should contain resource definitions"


@pytest.mark.integration
@pytest.mark.requires_azure
@pytest.mark.requires_openai
def test_compliance_validation():
    """Test that compliance validation works correctly."""
    supervisor = SupervisorAgent()

    # Test with compliance enforcement
    compliance_settings = {
        "enforce_compliance": True,
        "selected_frameworks": ["PCI DSS", "GDPR"],
    }

    request = "Create a database for storing customer payment information."

    response = supervisor.process_user_request(request, compliance_settings)

    assert response, "Response should not be empty"
    assert (
        "compliance" in response.lower() or "validation" in response.lower()
    ), "Response should mention compliance when enforced"


@pytest.mark.integration
@pytest.mark.slow
def test_template_extraction_robustness():
    """Test template extraction with various response formats."""
    supervisor = SupervisorAgent()

    # Test multiple different request types
    requests = [
        "Simple VM setup",
        "Container orchestration platform",
        "Data analytics pipeline",
        "IoT device management system",
    ]

    for request in requests:
        response = supervisor.process_user_request(request)

        # Should always get a response
        assert response, f"Should get response for request: {request}"

        # Should contain either template or explanation
        has_template = "```hcl" in response
        has_explanation = len(response) > 50

        assert (
            has_template or has_explanation
        ), f"Should have template or explanation for: {request}"
