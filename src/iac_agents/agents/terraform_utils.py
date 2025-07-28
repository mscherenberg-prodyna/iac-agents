"""Terraform template validation and variable management utilities."""

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from ..templates.template_loader import template_loader


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


def execute_terraform_command(command: str, working_dir: str = None) -> str:
    """Execute a terraform command and return the result."""
    try:
        # Split command into parts
        cmd_parts = command.split()

        # Set working directory
        cwd = Path(working_dir) if working_dir else Path.cwd()

        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=cwd,
            check=False,
        )

        if result.returncode == 0:
            return (
                result.stdout.strip()
                if result.stdout
                else "Command executed successfully"
            )
        return f"Error: {result.stderr.strip()}"

    except Exception as e:
        return f"Command execution failed: {e}"


def get_terraform_tools() -> List[Dict[str, Any]]:
    """Load terraform tools from template."""
    try:
        return template_loader.load_tools("terraform_tools")
    except Exception as e:
        print(f"Warning: Failed to load terraform tools: {e}")
        return []


def build_terraform_command(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Build terraform command string from tool name and arguments."""

    # Extract terraform command from tool name
    tf_cmd = tool_name.replace("terraform_", "", 1)

    # Start with base command
    cmd_parts = ["terraform"]

    # Handle workspace commands specially
    if tf_cmd.startswith("workspace_"):
        workspace_action = tf_cmd.replace("workspace_", "", 1)
        cmd_parts.extend(["workspace", workspace_action])

        if workspace_action in ["new", "select", "delete"] and "name" in arguments:
            cmd_parts.append(arguments["name"])

        # Add workspace-specific flags
        if workspace_action == "delete" and arguments.get("force", False):
            cmd_parts.append("-force")
        if workspace_action == "new" and "state" in arguments:
            cmd_parts.extend(["-state", arguments["state"]])
    else:
        cmd_parts.append(tf_cmd)

        # Handle specific commands with positional arguments
        if tf_cmd == "import" and "address" in arguments and "id" in arguments:
            cmd_parts.extend([arguments["address"], arguments["id"]])
        elif tf_cmd in ["taint", "untaint"] and "address" in arguments:
            cmd_parts.append(arguments["address"])
        elif tf_cmd == "output" and "name" in arguments:
            cmd_parts.append(arguments["name"])
        elif tf_cmd == "show" and "file" in arguments:
            cmd_parts.append(arguments["file"])
        elif tf_cmd == "apply" and "plan_file" in arguments:
            cmd_parts.append(arguments["plan_file"])

    # Map common boolean arguments to flags
    bool_flag_mappings = {
        "auto_approve": "-auto-approve",
        "destroy": "-destroy",
        "detailed_exitcode": "-detailed-exitcode",
        "no_color": "-no-color",
        "json": "-json",
        "raw": "-raw",
        "check": "-check",
        "diff": "-diff",
        "write": "-write",
        "list": "-list",
        "recursive": "-recursive",
        "refresh_only": "-refresh-only",
        "compact_warnings": "-compact-warnings",
        "upgrade": "-upgrade",
        "reconfigure": "-reconfigure",
        "migrate_state": "-migrate-state",
        "force_copy": "-force-copy",
    }

    # Add boolean flags that are true
    for arg, flag in bool_flag_mappings.items():
        if arguments.get(arg, False):
            cmd_parts.append(flag)

    # Add boolean flags that can be explicitly disabled
    disable_flags = ["input", "lock", "get", "backend", "refresh"]
    for flag in disable_flags:
        if flag in arguments:
            if arguments[flag]:
                cmd_parts.append(f'-{flag.replace("_", "-")}')
            else:
                cmd_parts.append(f'-{flag.replace("_", "-")}=false')

    # Handle string arguments with flags
    string_mappings = {
        "out": "-out",
        "backup": "-backup",
        "state": "-state",
        "state_out": "-state-out",
        "lock_timeout": "-lock-timeout",
        "lockfile": "-lockfile",
        "from_module": "-from-module",
    }

    for arg, flag in string_mappings.items():
        if arg in arguments and arguments[arg]:
            cmd_parts.extend([flag, arguments[arg]])

    # Handle integer arguments
    if "parallelism" in arguments:
        cmd_parts.extend(["-parallelism", str(arguments["parallelism"])])

    # Handle array arguments
    if "var_file" in arguments:
        for var_file in arguments["var_file"]:
            cmd_parts.extend(["-var-file", var_file])

    if "var" in arguments:
        for key, value in arguments["var"].items():
            cmd_parts.extend(["-var", f"{key}={value}"])

    if "backend_config" in arguments:
        for config in arguments["backend_config"]:
            cmd_parts.extend(["-backend-config", config])

    if "replace" in arguments:
        for resource in arguments["replace"]:
            cmd_parts.extend(["-replace", resource])

    if "target" in arguments:
        for target in arguments["target"]:
            cmd_parts.extend(["-target", target])

    return " ".join(cmd_parts)


def terraform_tool_executor(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute terraform tools using the terraform command function."""

    try:
        # Build command
        command = build_terraform_command(tool_name, arguments)

        # Get working directory
        working_dir = arguments.get("working_dir")

        # Execute command
        return execute_terraform_command(command, working_dir)

    except Exception as e:
        return f"Failed to execute {tool_name}: {e}"
