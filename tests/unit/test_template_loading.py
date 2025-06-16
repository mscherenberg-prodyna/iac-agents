"""Unit tests for the refactored template system."""

import pytest

from src.iac_agents.templates.template_loader import TemplateLoader
from src.iac_agents.templates.template_manager import TemplateManager, template_manager


@pytest.mark.unit
def test_template_loader_initialization():
    """Test that template loader initializes correctly."""
    loader = TemplateLoader()
    assert loader.base_path.exists()
    assert loader.base_path.name == "templates"


@pytest.mark.unit
def test_template_loader_lists_files():
    """Test that template loader can list available templates."""
    loader = TemplateLoader()

    # Test terraform templates
    terraform_templates = loader.list_available_terraform_templates()
    assert isinstance(terraform_templates, list)
    expected_tf_templates = ["document_storage", "web_application", "default"]
    for template in expected_tf_templates:
        assert (
            template in terraform_templates
        ), f"Missing terraform template: {template}"

    # Test prompt templates
    prompt_templates = loader.list_available_prompt_templates()
    assert isinstance(prompt_templates, list)
    expected_prompts = [
        "terraform_system",
        "enhanced_terraform",
        "requirements_analysis",
    ]
    for prompt in expected_prompts:
        assert prompt in prompt_templates, f"Missing prompt template: {prompt}"


@pytest.mark.unit
def test_template_loader_loads_files():
    """Test that template loader can load template files."""
    loader = TemplateLoader()

    # Test loading terraform templates
    for template_name in ["document_storage", "web_application", "default"]:
        template_content = loader.load_terraform_template(template_name)
        assert template_content, f"Template {template_name} should not be empty"
        assert (
            "terraform" in template_content
        ), f"Template {template_name} should contain terraform block"
        assert (
            "provider" in template_content
        ), f"Template {template_name} should contain provider block"

    # Test loading prompt templates
    for prompt_name in [
        "terraform_system",
        "enhanced_terraform",
        "requirements_analysis",
    ]:
        prompt_content = loader.load_prompt_template(prompt_name)
        assert prompt_content, f"Prompt {prompt_name} should not be empty"
        assert len(prompt_content) > 10, f"Prompt {prompt_name} should be substantial"


@pytest.mark.unit
def test_template_manager_initialization():
    """Test that template manager initializes correctly."""
    tm = TemplateManager()
    assert tm._prompt_templates is not None
    assert tm._terraform_templates is not None
    assert len(tm._prompt_templates) > 0
    assert len(tm._terraform_templates) > 0


@pytest.mark.unit
def test_template_manager_get_prompt():
    """Test template manager prompt retrieval."""
    tm = TemplateManager()

    # Test basic prompt retrieval
    for prompt_name in [
        "terraform_system",
        "enhanced_terraform",
        "requirements_analysis",
    ]:
        prompt = tm.get_prompt(prompt_name)
        assert prompt, f"Prompt {prompt_name} should not be empty"

    # Test prompt with formatting
    formatted_prompt = tm.get_prompt(
        "enhanced_terraform",
        enhancement_guidance="Test guidance",
        requirements="Test requirements",
    )
    assert "Test guidance" in formatted_prompt
    assert "Test requirements" in formatted_prompt

    # Test error handling
    with pytest.raises(ValueError, match="Unknown prompt template"):
        tm.get_prompt("nonexistent_prompt")


@pytest.mark.unit
def test_template_manager_get_terraform_template():
    """Test template manager terraform template retrieval."""
    tm = TemplateManager()

    # Test basic template retrieval
    for template_name in ["document_storage", "web_application", "default"]:
        template = tm.get_terraform_template(template_name)
        assert template, f"Template {template_name} should not be empty"
        assert (
            "terraform" in template
        ), f"Template {template_name} should contain terraform block"

    # Test fallback to default for unknown template
    unknown_template = tm.get_terraform_template("nonexistent_template")
    default_template = tm.get_terraform_template("default")
    assert unknown_template == default_template


@pytest.mark.unit
def test_template_manager_fallback_logic():
    """Test template manager fallback template logic."""
    tm = TemplateManager()

    # Test document storage keywords
    doc_template = tm.get_fallback_template("I need to store legal documents")
    expected_doc = tm.get_terraform_template("document_storage")
    assert doc_template == expected_doc

    # Test web application keywords
    web_template = tm.get_fallback_template("Create a web application")
    expected_web = tm.get_terraform_template("web_application")
    assert web_template == expected_web

    # Test default fallback
    default_template = tm.get_fallback_template("Create some infrastructure")
    expected_default = tm.get_terraform_template("default")
    assert default_template == expected_default


@pytest.mark.unit
def test_global_template_manager():
    """Test that global template manager instance works."""
    assert template_manager is not None
    assert isinstance(template_manager, TemplateManager)

    # Test it can load templates
    prompts = template_manager.list_available_prompts()
    templates = template_manager.list_available_terraform_templates()

    assert len(prompts) > 0
    assert len(templates) > 0


@pytest.mark.unit
def test_template_manager_lists():
    """Test template manager list methods."""
    tm = TemplateManager()

    prompts = tm.list_available_prompts()
    templates = tm.list_available_terraform_templates()

    # Check expected prompts are present
    expected_prompts = [
        "terraform_system",
        "enhanced_terraform",
        "requirements_analysis",
    ]
    for prompt in expected_prompts:
        assert prompt in prompts

    # Check expected templates are present
    expected_templates = ["document_storage", "web_application", "default"]
    for template in expected_templates:
        assert template in templates


@pytest.mark.unit
def test_template_reload():
    """Test template manager reload functionality."""
    tm = TemplateManager()

    # Get initial counts
    initial_prompts = len(tm._prompt_templates)
    initial_templates = len(tm._terraform_templates)

    # Reload templates
    tm.reload_templates()

    # Should have same counts after reload
    assert len(tm._prompt_templates) == initial_prompts
    assert len(tm._terraform_templates) == initial_templates
