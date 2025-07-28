"""Utils for executing git commands in a local repository."""

from pathlib import Path
from typing import Any, Dict, List

from ..templates.template_loader import template_loader


def get_iap_tools() -> List[Dict[str, Any]]:
    """Load iap workflow tools from template."""
    try:
        return template_loader.load_tools("iap_workflow_tools")
    except Exception as e:
        print(f"Warning: Failed to load iap workflow tools: {e}")
        return []


def write_terraform_template(template_content: str, working_dir: str) -> str:
    """Write a Terraform template to the specified working directory."""
    try:
        with open(f"{working_dir}/main.tf", "w", encoding="utf-8") as f:
            f.write(template_content)
        return f"Terraform template written to {working_dir}/main.tf"
    except Exception as e:
        return f"Failed to write Terraform template: {e}"


def read_terraform_template(working_dir: str) -> str:
    """Read a Terraform template from the specified working directory."""
    try:
        with open(f"{working_dir}/main.tf", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Failed to read Terraform template: {e}"


def iap_tool_executor(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute iap workflow tools using dynamic command building."""
    try:
        if tool_name == "write_terraform_template":
            return write_terraform_template(
                template_content=arguments.get("template_content", ""),
                working_dir=arguments.get("working_dir", str(Path.cwd())),
            )
        if tool_name == "read_terraform_template":
            return read_terraform_template(
                working_dir=arguments.get("working_dir", str(Path.cwd()))
            )
        return f"Not a valid tool: {tool_name}"
    except Exception as e:
        return f"Failed to execute {tool_name}: {e}"
