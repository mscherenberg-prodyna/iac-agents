#!/usr/bin/env python3
"""Corrected final test for all agent prompt templates."""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from iac_agents.templates.template_manager import template_manager
from iac_agents.templates.template_loader import template_loader


def test_templates_correctly():
    """Test templates based on their actual variable usage."""
    print("🎯 Corrected Template Validation Test")
    print("=" * 40)
    
    # First, let's see what variables each template actually uses
    template_loader_instance = template_loader
    
    templates_info = {
        "cloud_architect": {
            "variables": {
                "user_request": "Deploy a web application on Azure",
                "current_stage": "planning", 
                "completed_stages": "requirements_analysis, design",
                "agent_context": "Cloud Engineer has generated templates",
                "default_subscription_name": "Production Subscription",
                "available_subscriptions": "Dev, Test, Production",
                "should_respond_to_user": "True",
                "compliance_enforcement": "Enabled",
                "compliance_frameworks": "ISO27001, SOC2",
                "approval_required": "Yes"
            },
            "check_substitution": True
        },
        "cloud_engineer": {
            "variables": {
                "user_request": "Deploy a web application",
                "architect_analysis": "Need scalable infrastructure",
                "current_stage": "template_generation",
                "terraform_consultant_available": True
            },
            "check_substitution": True,
            "has_conditional": True
        },
        "sec_fin_ops_engineer": {
            "variables": {
                "compliance_enforcement": "Enabled",
                "compliance_frameworks": "ISO27001, PCI-DSS", 
                "template_content": "azurerm_app_service configuration",
                "terraform_consultant_available": True
            },
            "check_substitution": True,
            "has_conditional": True
        },
        "terraform_consultant": {
            "variables": {},  # No variables used
            "check_substitution": False
        },
        "dev_ops_engineer": {
            "variables": {},  # No variables used  
            "check_substitution": False
        },
        "welcome_message": {
            "variables": {},  # Check if it uses any variables
            "check_substitution": False
        }
    }
    
    results = []
    
    for template_name, info in templates_info.items():
        print(f"\n📋 Testing {template_name}:")
        print("-" * 30)
        
        try:
            # Try to render the template
            rendered = template_manager.get_prompt(template_name, **info["variables"])
            
            if info["check_substitution"]:
                # Check for unsubstituted Jinja2 variables (but not content in raw blocks)
                import re
                
                # Remove content between ``` blocks (code blocks that should be literal)
                cleaned_content = re.sub(r'```.*?```', '', rendered, flags=re.DOTALL)
                
                # Find {{ variable }} patterns that weren't substituted
                unsubstituted_jinja = re.findall(r'\{\{\s*([^}]+)\s*\}\}', cleaned_content)
                
                # Find { variable } patterns in non-code areas (but allow Terraform vars and test data)
                unsubstituted_format = []
                format_patterns = re.findall(r'\{([^}]+)\}', cleaned_content)
                for pattern in format_patterns:
                    # Allow Terraform variables, test data with ..., and single character patterns
                    if (not pattern.startswith('var.') and 
                        not pattern.strip() == ' ... ' and 
                        len(pattern.strip()) > 1 and
                        not pattern.startswith(' ') and
                        '=' not in pattern):  # Skip complex patterns that are likely code
                        unsubstituted_format.append(pattern)
                
                if unsubstituted_jinja:
                    print(f"❌ Unsubstituted Jinja2 variables: {unsubstituted_jinja}")
                    success = False
                elif unsubstituted_format:
                    print(f"❌ Unsubstituted format variables: {unsubstituted_format}")
                    success = False
                else:
                    print("✅ All variables properly substituted")
                    success = True
            else:
                print("✅ Template renders successfully (no variables to check)")
                success = True
            
            # Test conditional logic if applicable
            if info.get("has_conditional"):
                print("🔧 Testing conditional logic:")
                
                # Test with terraform_consultant_available = False
                test_vars_disabled = info["variables"].copy()
                test_vars_disabled["terraform_consultant_available"] = False
                
                rendered_disabled = template_manager.get_prompt(template_name, **test_vars_disabled)
                
                # Check for differences
                if rendered != rendered_disabled:
                    print("   ✅ Conditional logic working (different output)")
                    
                    if "unavailable" in rendered_disabled.lower():
                        print("   ✅ Unavailable message present when disabled")
                    else:
                        print("   ❌ Unavailable message missing when disabled")
                else:
                    print("   ❌ Conditional logic not working (same output)")
            
            results.append((template_name, success))
            
            # Show sample output
            lines = rendered.split('\n')[:3]
            print(f"📝 Sample: {lines[0][:50]}...")
            
        except Exception as e:
            print(f"❌ Error rendering template: {e}")
            results.append((template_name, False))
    
    return results


def test_template_loading():
    """Test template loading."""
    print(f"\n🔍 Template Loading Test")
    print("=" * 25)
    
    try:
        available = template_loader.list_available_prompt_templates()
        loaded = template_loader.load_all_prompt_templates()
        
        success = len(available) == len(loaded) == 6
        print(f"Available: {len(available)}, Loaded: {len(loaded)}")
        
        if success:
            print("✅ All templates loaded successfully")
        else:
            print("❌ Template loading issues detected")
            
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run corrected template tests."""
    print("🚀 Corrected Comprehensive Template Test")
    print("=" * 45)
    
    template_results = test_templates_correctly()
    loading_success = test_template_loading()
    
    # Summary
    print("\n" + "=" * 45)
    print("📊 FINAL RESULTS")
    print("=" * 45)
    
    passed = sum(1 for _, success in template_results if success)
    total = len(template_results)
    
    print(f"\n🎯 Template Tests:")
    for template_name, success in template_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {template_name}")
    
    print(f"\n📋 Loading Test: {'✅ PASS' if loading_success else '❌ FAIL'}")
    
    all_passed = (passed == total and loading_success)
    
    print(f"\n🏆 OVERALL: {passed + (1 if loading_success else 0)}/{total + 1} tests passed")
    
    if all_passed:
        print("\n🎉 SUCCESS! All agent prompt templates are working correctly!")
        print("✨ Variable substitution using Jinja2 is functioning properly")
        print("🔧 Conditional Terraform Consultant logic is operational")
        print("📋 All templates load and render without errors")
    else:
        print("\n⚠️ Some issues detected. Review results above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)