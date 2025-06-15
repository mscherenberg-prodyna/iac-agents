"""Template file loader utilities."""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class TemplateLoader:
    """Load templates from various file formats."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize template loader with base path."""
        if base_path is None:
            self.base_path = Path(__file__).parent
        else:
            self.base_path = Path(base_path)

    def load_text_file(self, file_path: str) -> str:
        """Load content from a text file."""
        full_path = self.base_path / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"Template file not found: {full_path}")

        with open(full_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def load_terraform_template(self, template_name: str) -> str:
        """Load a Terraform template file."""
        file_path = f"terraform/{template_name}.tf"
        return self.load_text_file(file_path)

    def load_prompt_template(self, prompt_name: str) -> str:
        """Load a prompt template file."""
        file_path = f"prompts/{prompt_name}.txt"
        return self.load_text_file(file_path)

    def load_all_terraform_templates(self) -> Dict[str, str]:
        """Load all available Terraform templates."""
        terraform_dir = self.base_path / "terraform"
        templates = {}

        if terraform_dir.exists():
            for tf_file in terraform_dir.glob("*.tf"):
                template_name = tf_file.stem
                templates[template_name] = self.load_terraform_template(template_name)

        return templates

    def load_all_prompt_templates(self) -> Dict[str, str]:
        """Load all available prompt templates."""
        prompts_dir = self.base_path / "prompts"
        prompts = {}

        if prompts_dir.exists():
            for txt_file in prompts_dir.glob("*.txt"):
                prompt_name = txt_file.stem
                prompts[prompt_name] = self.load_prompt_template(prompt_name)

        return prompts

    def list_available_terraform_templates(self) -> list:
        """List all available Terraform template names."""
        terraform_dir = self.base_path / "terraform"

        if not terraform_dir.exists():
            return []

        return [tf_file.stem for tf_file in terraform_dir.glob("*.tf")]

    def list_available_prompt_templates(self) -> list:
        """List all available prompt template names."""
        prompts_dir = self.base_path / "prompts"

        if not prompts_dir.exists():
            return []

        return [txt_file.stem for txt_file in prompts_dir.glob("*.txt")]

    def load_json_data(self, file_path: str) -> Dict[str, Any]:
        """Load data from a JSON file."""
        full_path = self.base_path / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"JSON file not found: {full_path}")

        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_html_template(self, template_name: str) -> str:
        """Load an HTML template file."""
        file_path = f"html/{template_name}.html"
        return self.load_text_file(file_path)

    def load_css_file(self, css_name: str) -> str:
        """Load a CSS file."""
        file_path = f"html/{css_name}.css"
        return self.load_text_file(file_path)

    def load_js_file(self, js_name: str) -> str:
        """Load a JavaScript file."""
        file_path = f"html/{js_name}.js"
        return self.load_text_file(file_path)

    def load_showcase_scenarios(self) -> Dict[str, Any]:
        """Load showcase scenarios from JSON."""
        return self.load_json_data("data/showcase_scenarios.json")

    def list_available_html_templates(self) -> list:
        """List all available HTML template names."""
        html_dir = self.base_path / "html"

        if not html_dir.exists():
            return []

        return [html_file.stem for html_file in html_dir.glob("*.html")]


# Global template loader instance
template_loader = TemplateLoader()
