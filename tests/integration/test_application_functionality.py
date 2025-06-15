"""Integration tests to verify the refactored application works correctly."""

import pytest


@pytest.mark.integration
def test_core_imports():
    """Test that all core components can be imported."""
    from src.iac_agents.agents.research_agent import TerraformResearchAgent
    from src.iac_agents.agents.supervisor_agent import SupervisorAgent
    from src.iac_agents.agents.terraform_agent import TerraformAgent
    from src.iac_agents.config.settings import config
    from src.iac_agents.templates.template_manager import TemplateManager

    # If we reach here, all imports were successful
    assert config is not None
    assert TemplateManager is not None
    assert SupervisorAgent is not None
    assert TerraformAgent is not None
    assert TerraformResearchAgent is not None


@pytest.mark.integration
def test_configuration():
    """Test configuration system."""
    from src.iac_agents.config.settings import config

    # Test compliance settings
    assert config.compliance.minimum_score_enforced == 70.0
    assert config.compliance.minimum_score_relaxed == 40.0
    assert "PCI DSS" in config.compliance.available_frameworks

    # Test UI settings
    assert config.ui.page_title == "Infrastructure as Prompts AI Agent"
    assert config.ui.max_chat_messages > 0

    # Test agent settings
    assert 0 <= config.agents.default_temperature <= 1
    assert config.agents.max_response_tokens > 0


@pytest.mark.integration
def test_template_manager():
    """Test template manager functionality."""
    from src.iac_agents.templates.template_manager import TemplateManager

    tm = TemplateManager()

    # Test that prompts are loaded
    assert len(tm._prompt_templates) > 0

    # Test prompt retrieval with the correct template names
    expected_prompts = [
        "terraform_system",
        "enhanced_terraform",
        "requirements_analysis",
    ]
    for prompt_name in expected_prompts:
        if prompt_name in tm._prompt_templates:
            prompt = tm.get_prompt(prompt_name)
            assert prompt, f"Prompt {prompt_name} should not be empty"

    # Test terraform templates are loaded
    assert len(tm._terraform_templates) > 0
    expected_templates = ["document_storage", "web_application", "default"]
    for template_name in expected_templates:
        template = tm.get_terraform_template(template_name)
        assert template, f"Template {template_name} should not be empty"


@pytest.mark.integration
def test_supervisor_agent():
    """Test supervisor agent instantiation."""
    from src.iac_agents.agents.supervisor_agent import SupervisorAgent

    supervisor = SupervisorAgent()
    assert supervisor is not None


@pytest.mark.integration
def test_agents_instantiate():
    """Test that all agent types can be instantiated."""
    from src.iac_agents.agents.research_agent import TerraformResearchAgent
    from src.iac_agents.agents.supervisor_agent import SupervisorAgent
    from src.iac_agents.agents.terraform_agent import TerraformAgent

    # Test agent instantiation
    supervisor = SupervisorAgent()
    terraform_agent = TerraformAgent()
    research_agent = TerraformResearchAgent()

    assert supervisor is not None
    assert terraform_agent is not None
    assert research_agent is not None
