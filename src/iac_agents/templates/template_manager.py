"""Template manager for prompts and Terraform templates."""

from typing import Dict, List, Optional
from .template_loader import template_loader


class TemplateManager:
    """Manages prompts and Terraform templates."""
    
    def __init__(self):
        self._prompt_templates = None
        self._terraform_templates = None
        self._load_templates()
    
    def _load_templates(self):
        """Load all templates from files."""
        try:
            self._prompt_templates = template_loader.load_all_prompt_templates()
            self._terraform_templates = template_loader.load_all_terraform_templates()
        except Exception as e:
            # Fallback to empty dictionaries if loading fails
            self._prompt_templates = {}
            self._terraform_templates = {}
            print(f"Warning: Failed to load templates: {e}")
    
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
        return template_loader.list_available_prompt_templates()
    
    def list_available_terraform_templates(self) -> List[str]:
        """List all available Terraform templates."""
        return template_loader.list_available_terraform_templates()
    
    def reload_templates(self):
        """Reload all templates from files."""
        self._load_templates()


# Global template manager instance
template_manager = TemplateManager()