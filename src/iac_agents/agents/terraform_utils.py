"""Terraform template validation and variable management utilities."""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TerraformVariableManager:
    """Manages Terraform variables and template validation."""

    @staticmethod
    def extract_variables_from_template(template_content: str) -> Dict[str, Dict]:
        """Extract variable definitions from Terraform template.

        Returns:
            Dict mapping variable names to their properties (type, default, description, etc.)
        """
        variables = {}

        # Pattern to match variable blocks
        var_pattern = r'variable\s+"([^"]+)"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'

        for match in re.finditer(var_pattern, template_content, re.DOTALL):
            var_name = match.group(1)
            var_block = match.group(2)

            # Parse variable properties
            var_info = {
                "name": var_name,
                "type": TerraformVariableManager._extract_property(var_block, "type"),
                "description": TerraformVariableManager._extract_property(
                    var_block, "description"
                ),
                "default": TerraformVariableManager._extract_property(
                    var_block, "default"
                ),
                "has_default": "default" in var_block,
                "has_validation": "validation" in var_block,
                "required": "default" not in var_block,
            }

            variables[var_name] = var_info

        return variables

    @staticmethod
    def _extract_property(var_block: str, property_name: str) -> Optional[str]:
        """Extract a specific property from a variable block."""
        pattern = rf'{property_name}\s*=\s*"([^"]*)"'
        match = re.search(pattern, var_block)
        return match.group(1) if match else None

    @staticmethod
    def validate_template_variables(template_content: str) -> Tuple[bool, List[str]]:
        """Validate that all required variables have defaults or can be inferred.

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        variables = TerraformVariableManager.extract_variables_from_template(
            template_content
        )
        issues = []

        for var_name, var_info in variables.items():
            if var_info["required"]:
                issues.append(
                    f"Variable '{var_name}' is required but has no default value"
                )

        return len(issues) == 0, issues

    @staticmethod
    def infer_variable_values_from_requirements(
        user_requirements: str,
    ) -> Dict[str, str]:
        """Infer variable values from user requirements text.

        Args:
            user_requirements: Natural language requirements from user

        Returns:
            Dict mapping variable names to inferred values
        """
        inferred_values = {}

        # Default environment based on keywords
        if any(
            keyword in user_requirements.lower()
            for keyword in ["test", "testing", "dev", "development"]
        ):
            inferred_values["environment"] = "dev"
        elif any(
            keyword in user_requirements.lower()
            for keyword in ["staging", "stage", "pre-prod"]
        ):
            inferred_values["environment"] = "staging"
        elif any(
            keyword in user_requirements.lower()
            for keyword in ["prod", "production", "live"]
        ):
            inferred_values["environment"] = "prod"
        else:
            # Default to dev for safety
            inferred_values["environment"] = "dev"

        # Extract resource group if mentioned
        rg_pattern = r"resource\s+group[:\s]+([a-zA-Z0-9_-]+)"
        rg_match = re.search(rg_pattern, user_requirements, re.IGNORECASE)
        if rg_match:
            inferred_values["resource_group_name"] = rg_match.group(1)

        # Extract location/region if mentioned
        azure_regions = [
            "eastus",
            "westus",
            "centralus",
            "northeurope",
            "westeurope",
            "eastasia",
            "southeastasia",
            "japaneast",
            "japanwest",
            "australiaeast",
            "australiasoutheast",
            "brazilsouth",
            "canadacentral",
            "canadaeast",
            "uksouth",
            "ukwest",
        ]

        for region in azure_regions:
            if region in user_requirements.lower():
                inferred_values["location"] = region
                break

        # Default to West Europe if no region specified
        if "location" not in inferred_values:
            inferred_values["location"] = "West Europe"

        return inferred_values

    @staticmethod
    def enhance_template_with_defaults(
        template_content: str, inferred_values: Dict[str, str]
    ) -> str:
        """Add default values to variables that don't have them.

        Args:
            template_content: Original Terraform template
            inferred_values: Variable values inferred from requirements

        Returns:
            Enhanced template with default values added
        """
        variables = TerraformVariableManager.extract_variables_from_template(
            template_content
        )
        enhanced_template = template_content

        for var_name, var_info in variables.items():
            if var_info["required"] and var_name in inferred_values:
                # Add default value to the variable definition
                var_pattern = rf'(variable\s+"{var_name}"\s*\{{[^}}]*?)(\}})'
                default_value = inferred_values[var_name]

                def add_default(match, default_value=default_value):
                    var_block = match.group(1)
                    closing_brace = match.group(2)
                    default_line = f'\n  default = "{default_value}"'
                    return var_block + default_line + "\n" + closing_brace

                enhanced_template = re.sub(
                    var_pattern, add_default, enhanced_template, flags=re.DOTALL
                )

        return enhanced_template

    @staticmethod
    def generate_terraform_vars_file(variables: Dict[str, str]) -> str:
        """Generate a terraform.tfvars file content.

        Args:
            variables: Dict mapping variable names to values

        Returns:
            Content for terraform.tfvars file
        """
        lines = ["# Auto-generated variable values"]

        for var_name, value in variables.items():
            lines.append(f'{var_name} = "{value}"')

        return "\n".join(lines)


def enhance_terraform_template(
    template_content: str,
    context: str = "deployment",
    project_name: str = "iac-agent",
    default_location: str = "West Europe",
) -> str:
    """Enhance Terraform template with provider configuration and standard tags.

    Args:
        template_content: Original template content
        context: Context for template usage ("validation" or "deployment")
        project_name: Project name for resource naming
        default_location: Default Azure location

    Returns:
        Enhanced template with provider config and common variables
    """
    # Check if template already has proper provider configuration
    if "terraform {" not in template_content:
        provider_config = """
terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
  # TODO: Add Azure Storage backend for state management
}

provider "azurerm" {
  features {}
  # Uses active Azure CLI session authentication
  # TODO: Add option to configure different authentication methods
}

"""
        template_content = provider_config + template_content

    # Add common variables if not present
    if 'variable "environment"' not in template_content:
        common_vars = f"""
variable "environment" {{
  description = "Deployment environment"
  type        = string
  default     = "dev"
}}

variable "project_name" {{
  description = "Project name for resource naming"
  type        = string
  default     = "{project_name}"
}}

variable "location" {{
  description = "Azure region for deployment"
  type        = string
  default     = "{default_location}"
}}

"""
        template_content = template_content + "\n" + common_vars

    return template_content


def run_terraform_command(
    working_dir: Path, command: list, timeout: int = 300, context: str = "execution"
) -> dict:
    """Run a Terraform command in the specified directory.

    Args:
        working_dir: Directory to run command in
        command: Terraform command as list
        timeout: Command timeout in seconds
        context: Context description for error messages

    Returns:
        Dict with success, stdout, stderr, returncode
    """
    try:
        result = subprocess.run(
            command,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"{context} command timed out after {timeout} seconds",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"{context} command failed: {str(e)}",
            "returncode": -1,
        }


def is_valid_terraform_content(content: str, strict_validation: bool = False) -> bool:
    """Validate if content appears to be valid Terraform configuration.

    Args:
        content: Content to validate
        strict_validation: If True, applies stricter validation rules

    Returns:
        True if content appears to be valid Terraform
    """
    if not content or not content.strip():
        return False

    content_lower = content.lower()
    terraform_keywords = ["terraform", "provider", "resource", "variable", "output"]
    has_terraform_keywords = any(
        keyword in content_lower for keyword in terraform_keywords
    )
    has_hcl_syntax = any(char in content for char in ["{", "}", "="])

    if strict_validation:
        # Reject if it contains too much explanatory text
        lines = content.split("\n")
        non_comment_lines = [line for line in lines if not line.strip().startswith("#")]
        if len(non_comment_lines) > 0:
            text_ratio = sum(
                1
                for line in non_comment_lines
                if "{" not in line and "}" not in line and "=" not in line
            ) / len(non_comment_lines)
            if text_ratio > 0.5:  # More than 50% explanatory text
                return False

    return has_terraform_keywords and has_hcl_syntax
