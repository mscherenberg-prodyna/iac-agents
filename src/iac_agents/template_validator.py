"""Terraform template validation and security checking module."""

import re
import json
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of template validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    security_issues: List[str]
    suggestions: List[str]


class TerraformTemplateValidator:
    """Validates Terraform templates for syntax, security, and best practices."""
    
    def __init__(self):
        self.security_patterns = {
            "hardcoded_secrets": [
                r'password\s*=\s*"[^$][^"]*"',
                r'secret\s*=\s*"[^$][^"]*"',
                r'key\s*=\s*"[^$][^"]*"',
                r'token\s*=\s*"[^$][^"]*"'
            ],
            "public_access": [
                r'source_address_prefix\s*=\s*"\*"',
                r'cidr_blocks\s*=\s*\["0\.0\.0\.0/0"\]',
                r'from_port\s*=\s*0.*to_port\s*=\s*65535'
            ],
            "admin_access": [
                r'admin_username\s*=\s*"admin"',
                r'username\s*=\s*"administrator"',
                r'user\s*=\s*"root"'
            ]
        }
        
        self.required_blocks = ["terraform", "provider"]
        self.azure_best_practices = [
            "resource_group",
            "tags",
            "location"
        ]
    
    def validate_template(self, template: str) -> ValidationResult:
        """Comprehensive validation of Terraform template."""
        errors = []
        warnings = []
        security_issues = []
        suggestions = []
        
        # Basic syntax validation
        syntax_errors = self._validate_syntax(template)
        errors.extend(syntax_errors)
        
        # Structure validation
        structure_warnings = self._validate_structure(template)
        warnings.extend(structure_warnings)
        
        # Security validation
        security_problems = self._validate_security(template)
        security_issues.extend(security_problems)
        
        # Best practices check
        practice_suggestions = self._check_best_practices(template)
        suggestions.extend(practice_suggestions)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            security_issues=security_issues,
            suggestions=suggestions
        )
    
    def _validate_syntax(self, template: str) -> List[str]:
        """Validate basic HCL syntax."""
        errors = []
        
        if not template.strip():
            errors.append("Template is empty")
            return errors
        
        # Check brace matching
        open_braces = template.count('{')
        close_braces = template.count('}')
        if open_braces != close_braces:
            errors.append(f"Mismatched braces: {open_braces} opening, {close_braces} closing")
        
        # Check quote matching
        quote_count = template.count('"')
        if quote_count % 2 != 0:
            errors.append("Unmatched quotes in template")
        
        # Check for common syntax errors
        if re.search(r'resource\s+"[^"]*"\s+"[^"]*"\s*[^{]', template):
            errors.append("Missing opening brace after resource declaration")
            
        return errors
    
    def _validate_structure(self, template: str) -> List[str]:
        """Validate template structure and required blocks."""
        warnings = []
        
        # Check for required blocks
        for block in self.required_blocks:
            if not re.search(rf'\b{block}\s*{{', template, re.IGNORECASE):
                warnings.append(f"Missing {block} block")
        
        # Check for resource blocks
        if not re.search(r'\bresource\s+', template, re.IGNORECASE):
            warnings.append("No resource blocks found")
        
        # Check for variables
        if "var." in template and not re.search(r'\bvariable\s+', template):
            warnings.append("Using variables but no variable blocks defined")
        
        # Check for outputs
        if not re.search(r'\boutput\s+', template, re.IGNORECASE):
            warnings.append("Consider adding output blocks for important values")
            
        return warnings
    
    def _validate_security(self, template: str) -> List[str]:
        """Check for security issues in template."""
        security_issues = []
        
        for issue_type, patterns in self.security_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, template, re.IGNORECASE)
                if matches:
                    security_issues.append(f"Potential {issue_type.replace('_', ' ')}: {len(matches)} occurrence(s)")
        
        # Check for missing encryption
        if "storage_account" in template.lower() and "enable_https_traffic_only" not in template.lower():
            security_issues.append("Storage account should enforce HTTPS traffic")
            
        if "virtual_machine" in template.lower() and "disable_password_authentication" not in template.lower():
            security_issues.append("Consider disabling password authentication for VMs")
            
        return security_issues
    
    def _check_best_practices(self, template: str) -> List[str]:
        """Check adherence to Terraform best practices."""
        suggestions = []
        
        # Check for provider version constraints
        if re.search(r'provider\s+"[^"]*"\s*{', template) and "version" not in template.lower():
            suggestions.append("Consider adding version constraints to provider blocks")
        
        # Check for resource tagging (Azure focus)
        if "azurerm" in template.lower():
            resource_blocks = re.findall(r'resource\s+"azurerm_[^"]*"', template)
            tagged_resources = re.findall(r'tags\s*=', template)
            if len(resource_blocks) > len(tagged_resources):
                suggestions.append("Consider adding tags to Azure resources for better management")
        
        # Check for naming conventions
        if re.search(r'name\s*=\s*"[A-Z]', template):
            suggestions.append("Consider using lowercase names following cloud provider conventions")
        
        # Check for hardcoded locations
        location_matches = re.findall(r'location\s*=\s*"[^"]*"', template)
        if location_matches and not any("var." in match for match in location_matches):
            suggestions.append("Consider using variables for location/region values")
        
        # Check for resource dependencies
        if template.count("resource") > 3 and "depends_on" not in template:
            suggestions.append("Consider explicit dependencies for complex resource relationships")
            
        return suggestions
    
    def validate_for_deployment(self, template: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate template specifically for deployment readiness."""
        result = self.validate_template(template)
        
        deployment_ready = (
            result.is_valid and 
            len(result.security_issues) == 0 and
            self._has_required_deployment_elements(template)
        )
        
        deployment_info = {
            "ready_for_deployment": deployment_ready,
            "validation_result": result,
            "deployment_requirements": self._get_deployment_requirements(template),
            "estimated_resources": self._estimate_resource_count(template)
        }
        
        return deployment_ready, deployment_info
    
    def _has_required_deployment_elements(self, template: str) -> bool:
        """Check if template has elements required for deployment."""
        has_terraform_block = bool(re.search(r'\bterraform\s*{', template))
        has_provider = bool(re.search(r'\bprovider\s+', template))
        has_resources = bool(re.search(r'\bresource\s+', template))
        
        return has_terraform_block and has_provider and has_resources
    
    def _get_deployment_requirements(self, template: str) -> List[str]:
        """Get list of requirements for deploying this template."""
        requirements = []
        
        if "azurerm" in template.lower():
            requirements.append("Azure CLI authentication or service principal")
            requirements.append("Terraform AzureRM provider")
            
        if "random" in template.lower():
            requirements.append("Terraform Random provider")
            
        if "backend" in template.lower():
            requirements.append("Configured Terraform backend for state management")
        else:
            requirements.append("Consider configuring remote state backend")
            
        if "var." in template:
            requirements.append("Variable values (terraform.tfvars file)")
            
        return requirements
    
    def _estimate_resource_count(self, template: str) -> int:
        """Estimate number of resources that will be created."""
        resource_matches = re.findall(r'\bresource\s+"[^"]*"', template)
        return len(resource_matches)