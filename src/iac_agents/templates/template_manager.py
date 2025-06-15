"""Template manager for prompts and Terraform templates."""

from typing import Dict, List, Optional
from .prompts.terraform_generation import (
    TERRAFORM_SYSTEM_PROMPT,
    ENHANCED_TERRAFORM_PROMPT_TEMPLATE,
    REQUIREMENTS_ANALYSIS_PROMPT
)
from .terraform.document_storage import DOCUMENT_STORAGE_TEMPLATE
from .terraform.web_application import WEB_APPLICATION_TEMPLATE, DEFAULT_TEMPLATE


class TemplateManager:
    """Manages prompts and Terraform templates."""
    
    def __init__(self):
        self._prompt_templates = {
            "terraform_system": TERRAFORM_SYSTEM_PROMPT,
            "enhanced_terraform": ENHANCED_TERRAFORM_PROMPT_TEMPLATE,
            "requirements_analysis": REQUIREMENTS_ANALYSIS_PROMPT
        }
        
        self._terraform_templates = {
            "document_storage": DOCUMENT_STORAGE_TEMPLATE,
            "web_application": WEB_APPLICATION_TEMPLATE,
            "default": DEFAULT_TEMPLATE
        }
    
    def get_prompt(self, prompt_name: str, **kwargs) -> str:
        """Get a prompt template with optional formatting."""
        if prompt_name not in self._prompt_templates:
            raise ValueError(f"Unknown prompt template: {prompt_name}")
        
        template = self._prompt_templates[prompt_name]
        
        if kwargs:
            return template.format(**kwargs)
        return template
    
    def get_terraform_template(self, template_type: str) -> str:
        """Get a Terraform template by type."""
        if template_type not in self._terraform_templates:
            return self._terraform_templates["default"]
        
        return self._terraform_templates[template_type]
    
    def get_fallback_template(self, requirements: str) -> str:
        """Get appropriate fallback template based on requirements."""
        requirements_lower = requirements.lower()
        
        # Document storage template
        if any(keyword in requirements_lower for keyword in ["document", "file", "storage", "legal", "retention"]):
            return self.get_terraform_template("document_storage")
        
        # Web application template  
        elif any(keyword in requirements_lower for keyword in ["web", "app", "application", "website"]):
            return self.get_terraform_template("web_application")
        
        # Default template
        else:
            return self.get_terraform_template("default")
    
    def list_available_prompts(self) -> List[str]:
        """List all available prompt templates."""
        return list(self._prompt_templates.keys())
    
    def list_available_terraform_templates(self) -> List[str]:
        """List all available Terraform templates."""
        return list(self._terraform_templates.keys())


# Global template manager instance
template_manager = TemplateManager()