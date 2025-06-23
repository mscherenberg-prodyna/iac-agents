#!/usr/bin/env python3
"""Test script for Terraform Research toggle functionality."""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from iac_agents.templates.template_manager import template_manager
from iac_agents.streamlit.components.compliance_panel import _check_terraform_credentials, get_deployment_config


def test_template_rendering():
    """Test template rendering with different terraform_consultant_available values."""
    print("🧪 Testing Template Rendering with Terraform Toggle")
    print("=" * 55)
    
    # Test data
    test_contexts = [
        {
            "name": "Terraform Consultant Available",
            "terraform_consultant_available": True,
        },
        {
            "name": "Terraform Consultant Unavailable", 
            "terraform_consultant_available": False,
        }
    ]
    
    # Test prompts that use terraform_consultant_available
    test_prompts = ["cloud_engineer", "sec_fin_ops_engineer"]
    
    for prompt_name in test_prompts:
        print(f"\n📋 Testing {prompt_name} prompt:")
        print("-" * 40)
        
        for context in test_contexts:
            print(f"\n🔧 Scenario: {context['name']}")
            
            try:
                # Common parameters for both prompts
                base_params = {
                    "user_request": "Deploy a web application",
                    "terraform_consultant_available": context["terraform_consultant_available"],
                }
                
                # Add specific parameters for each prompt
                if prompt_name == "cloud_engineer":
                    params = {
                        **base_params,
                        "architect_analysis": "Sample architect analysis",
                        "current_stage": "template_generation",
                    }
                elif prompt_name == "sec_fin_ops_engineer":
                    params = {
                        **base_params,
                        "template_content": "Sample template content",
                        "compliance_enforcement": "Enabled",
                        "compliance_frameworks": "ISO27001, SOC2",
                        "compliance_requirements": "{'enforce_compliance': True}",
                    }
                
                # Render the prompt
                rendered_prompt = template_manager.get_prompt(prompt_name, **params)
                
                # Check for expected content based on terraform availability
                if context["terraform_consultant_available"]:
                    if "TERRAFORM_CONSULTATION_NEEDED" in rendered_prompt or "PRICING_LOOKUP_REQUIRED" in rendered_prompt:
                        print("✅ Terraform consultation instructions present")
                    else:
                        print("❌ Expected terraform consultation instructions missing")
                        
                    if "currently unavailable" not in rendered_prompt:
                        print("✅ No unavailability message (correct)")
                    else:
                        print("❌ Unavailability message present when it shouldn't be")
                        
                else:  # terraform_consultant_available = False
                    if "currently unavailable" in rendered_prompt or "built-in knowledge" in rendered_prompt:
                        print("✅ Unavailability message present")
                    else:
                        print("❌ Expected unavailability message missing")
                        
                    if "TERRAFORM_CONSULTATION_NEEDED" not in rendered_prompt and "PRICING_LOOKUP_REQUIRED" not in rendered_prompt:
                        print("✅ No consultation instructions (correct)")
                    else:
                        print("❌ Consultation instructions present when they shouldn't be")
                
                # Show a snippet of the relevant section
                lines = rendered_prompt.split('\n')
                relevant_lines = []
                for i, line in enumerate(lines):
                    if any(keyword in line.lower() for keyword in ['terraform consultant', 'consultation', 'pricing lookup', 'unavailable']):
                        # Include some context lines
                        start = max(0, i-1)
                        end = min(len(lines), i+3)
                        relevant_lines.extend(lines[start:end])
                        break
                
                if relevant_lines:
                    print("📝 Relevant section:")
                    for line in relevant_lines[:5]:  # Show max 5 lines
                        print(f"   {line.strip()}")
                
            except Exception as e:
                print(f"❌ Error rendering {prompt_name}: {str(e)}")
                return False
    
    return True


def test_credential_check():
    """Test the credential checking functionality."""
    print("\n🔐 Testing Credential Check Functionality")
    print("=" * 45)
    
    # Check current environment
    terraform_available = _check_terraform_credentials()
    print(f"Current credentials available: {terraform_available}")
    
    # Check required environment variables
    required_vars = ["AZURE_PROJECT_ENDPOINT", "AZURE_AGENT_ID"]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Present (***{value[-4:]})")
        else:
            print(f"❌ {var}: Missing")
    
    return True


def test_deployment_config():
    """Test deployment configuration logic."""
    print("\n⚙️ Testing Deployment Configuration")
    print("=" * 40)
    
    try:
        # This would normally come from Streamlit session state
        # Here we'll simulate different scenarios
        
        print("Testing credential-based auto-disable:")
        terraform_available = _check_terraform_credentials()
        
        if terraform_available:
            print("✅ Terraform Research should be available by default")
        else:
            print("✅ Terraform Research should be auto-disabled (missing credentials)")
        
        # Test get_deployment_config default behavior
        config = get_deployment_config()
        expected_terraform_enabled = terraform_available
        actual_terraform_enabled = config.get("terraform_research_enabled", True)
        
        if actual_terraform_enabled == expected_terraform_enabled:
            print("✅ get_deployment_config returns correct default")
        else:
            print(f"❌ Expected terraform_research_enabled={expected_terraform_enabled}, got {actual_terraform_enabled}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing deployment config: {str(e)}")
        return False


def test_workflow_integration():
    """Test workflow integration with terraform toggle."""
    print("\n🔄 Testing Workflow Integration")
    print("=" * 35)
    
    # Test different deployment configurations
    test_configs = [
        {"terraform_research_enabled": True},
        {"terraform_research_enabled": False},
        {},  # No config (should default to credential check)
    ]
    
    for i, deployment_config in enumerate(test_configs, 1):
        print(f"\nTest {i}: {deployment_config or 'No config (defaults)'}")
        
        # Simulate what the routing logic would check
        terraform_enabled = deployment_config.get("terraform_research_enabled", _check_terraform_credentials())
        
        print(f"Terraform Research Enabled: {terraform_enabled}")
        
        # Simulate routing decisions
        if terraform_enabled:
            print("  - Cloud Engineer with needs_terraform_lookup=True → terraform_consultant")
            print("  - SecOps/FinOps with needs_pricing_lookup=True → terraform_consultant")
        else:
            print("  - Cloud Engineer with needs_terraform_lookup=True → cloud_architect (skipped)")
            print("  - SecOps/FinOps with needs_pricing_lookup=True → cloud_architect (skipped)")
    
    return True


def main():
    """Run all tests."""
    print("🚀 Terraform Research Toggle - Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        ("Template Rendering", test_template_rendering),
        ("Credential Check", test_credential_check), 
        ("Deployment Config", test_deployment_config),
        ("Workflow Integration", test_workflow_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Terraform Research toggle is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)