"""Test Terraform template extraction through end-to-end workflow."""

from src.iac_agents.agents import SupervisorAgent


def test_template_extraction_through_workflow():
    """Test extraction of Terraform templates through complete workflow."""
    supervisor = SupervisorAgent()

    # Test with complex nested response that should extract proper template
    test_request = "Create an Azure storage account with proper compliance settings"

    response = supervisor.process_user_request(test_request)

    # Verify response contains HCL template
    assert "```hcl" in response, "Response should contain HCL code block"

    # Extract template from response
    start = response.find("```hcl") + 6
    end = response.find("```", start)

    if end > start:
        template = response[start:end].strip()

        # Verify template content
        assert template, "Template should not be empty"
        assert len(template) > 50, "Template should be substantial"
        assert (
            "terraform" in template.lower()
            or "provider" in template.lower()
            or "resource" in template.lower()
        ), "Template should contain Terraform configuration elements"
        assert (
            "azurerm" in template.lower() or "azure" in template.lower()
        ), "Template should reference Azure provider"


def test_workflow_template_generation_stage():
    """Test that template generation stage produces valid templates."""
    supervisor = SupervisorAgent()

    test_cases = [
        "Create a simple storage account",
        "Set up a web application with database",
        "Deploy a secure document storage solution",
    ]

    for test_case in test_cases:
        response = supervisor.process_user_request(test_case)

        # Should have a response
        assert response, f"Should get response for: {test_case}"

        # Should contain infrastructure elements
        response_lower = response.lower()
        infrastructure_keywords = [
            "terraform",
            "resource",
            "provider",
            "azure",
            "infrastructure",
        ]
        assert any(
            keyword in response_lower for keyword in infrastructure_keywords
        ), f"Response should contain infrastructure keywords for: {test_case}"

        # Check workflow completed template generation
        status = supervisor.get_workflow_status()
        completed_stages = status.get("completed_stages", [])
        assert (
            "template_generation" in completed_stages
        ), f"Should complete template generation for: {test_case}"

        # Clear history for next test
        supervisor.clear_history()


def test_template_validation_integration():
    """Test that generated templates go through validation."""
    supervisor = SupervisorAgent()

    # Request that should generate a template
    request = "Create a compliant database storage solution"
    response = supervisor.process_user_request(request)

    assert response

    # Check that validation stage was completed
    status = supervisor.get_workflow_status()
    completed_stages = status.get("completed_stages", [])
    assert (
        "validation_and_compliance" in completed_stages
    ), "Should complete validation stage"

    # Should have compliance information
    assert (
        "compliance_score" in status or "quality_gate_passed" in status
    ), "Should have compliance validation results"


def test_multiple_template_extraction_patterns():
    """Test template extraction with different response patterns."""
    supervisor = SupervisorAgent()

    # Test cases with different complexity
    test_requests = [
        "Simple storage account",
        "Complex multi-tier web application with security",
        "Minimal VM setup",
    ]

    for request in test_requests:
        response = supervisor.process_user_request(request)

        # Should always get a substantial response
        assert response, f"Should get response for: {request}"
        assert len(response) > 50, f"Response should be substantial for: {request}"

        # Should either contain template or explanation
        has_template = "```hcl" in response or "```" in response
        has_explanation = len(response.split()) > 20

        assert (
            has_template or has_explanation
        ), f"Should have template or detailed explanation for: {request}"

        supervisor.clear_history()


if __name__ == "__main__":
    # Test template extraction
    test_template_extraction_through_workflow()
    print("✅ Template extraction test passed")

    # Test workflow integration
    test_workflow_template_generation_stage()
    print("✅ Workflow template generation test passed")
