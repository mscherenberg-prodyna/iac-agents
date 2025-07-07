"""Terraform template validation and variable management utilities."""

import re
import subprocess
from pathlib import Path


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


def parse_terraform_providers(init_result: dict) -> dict[str, str]:
    """Parse Terraform init output to extract installed providers and their versions.

    Args:
        init_result: Dictionary returned by run_terraform_command for 'terraform init'

    Returns:
        Dict mapping provider names to their versions (e.g., {'aws': '5.31.0', 'random': '3.6.0'})
        Returns empty dict if parsing fails or no providers found
    """
    if not init_result.get("success", False):
        return {}

    stdout = init_result.get("stdout", "")
    providers = {}

    provider_pattern = r"(?:Installing|Using previously-installed|Downloading)\s+(?:registry\.terraform\.io/)?([^/\s]+/)?([^/\s]+)\s+v?(\d+\.\d+\.\d+(?:-[a-zA-Z0-9-]+)?)"

    for line in stdout.split("\n"):
        match = re.search(provider_pattern, line, re.IGNORECASE)
        if match:
            provider_name = match.group(2)
            version = match.group(3)
            providers[provider_name] = version

    return providers


def get_terraform_version() -> str | None:
    """
    Get the currently installed Terraform version as a string.

    Returns:
        str: The Terraform version (e.g., "1.6.4") or None if not found/installed

    Raises:
        Exception: If there's an error running the terraform command
    """

    # Use current directory as working directory
    working_dir = Path.cwd()

    result = run_terraform_command(
        working_dir=working_dir,
        command=["terraform", "version"],
        timeout=30,
        context="check",
    )

    if not result["success"]:
        return None

    version_match = re.search(r"Terraform v(\d+\.\d+\.\d+)", result["stdout"])

    if version_match:
        return version_match.group(1)
    return None


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


def extract_terraform_template(response: str) -> str:
    """Extract Terraform template from LLM response."""
    if not response:
        return ""

    # Find HCL code blocks first
    hcl_pattern = r"```(?:hcl|terraform)\s*\n(.*?)\n```"
    hcl_matches = re.findall(hcl_pattern, response, re.DOTALL | re.IGNORECASE)

    if hcl_matches:
        # Return the longest HCL block
        return max(hcl_matches, key=len).strip()

    # Fall back to generic code blocks
    code_pattern = r"```\s*\n(.*?)\n```"
    code_matches = re.findall(code_pattern, response, re.DOTALL)

    for match in code_matches:
        if is_valid_terraform_content(match, strict_validation=True):
            return match.strip()

    # Look for terraform blocks without code fences
    if "resource " in response or "terraform {" in response:
        lines = response.split("\n")
        terraform_lines = []
        in_terraform_block = False

        for line in lines:
            line_lower = line.lower().strip()

            # Start collecting when we find terraform keywords
            if any(
                keyword in line_lower
                for keyword in [
                    "terraform {",
                    "provider ",
                    "resource ",
                    "variable ",
                    "output ",
                ]
            ):
                in_terraform_block = True
                terraform_lines.append(line)
                continue

            # Stop collecting when we hit non-terraform content
            if in_terraform_block:
                # Stop if we hit explanatory text or sentences
                if (
                    line.strip()
                    and not line_lower.startswith("#")
                    and not any(char in line for char in ["{", "}", "=", '"', "[", "]"])
                    and any(
                        word in line_lower
                        for word in [
                            "if you",
                            "this template",
                            "please",
                            "note:",
                            "important",
                        ]
                    )
                ):
                    break
                # Continue collecting terraform content
                terraform_lines.append(line)

        if terraform_lines:
            content = "\n".join(terraform_lines).strip()
            if is_valid_terraform_content(content, strict_validation=True):
                return content

    return ""
