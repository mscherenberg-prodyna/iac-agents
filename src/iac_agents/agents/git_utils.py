"""Utils for executing git commands in a local repository."""

import os
import shlex
import subprocess
from typing import Any, Dict, List, Union

from ..templates.template_loader import template_loader


def execute_git_command(command: Union[str, List[str]]) -> str:
    """Execute a local git command and return the result."""
    try:
        # Handle command as string or list
        if isinstance(command, str):
            cmd_list = shlex.split(command)
        else:
            cmd_list = command

        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd(),
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


def get_git_tools() -> List[Dict[str, Any]]:
    """Load git tools from template."""
    try:
        return template_loader.load_tools("git_tools")
    except Exception as e:
        print(f"Warning: Failed to load git tools: {e}")
        return []


def build_git_command(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Build git command from tool name and arguments using simple mapping."""

    # Extract git command from tool name
    git_cmd = tool_name.replace("git_", "", 1)

    # Start with base command
    cmd_parts = ["git", git_cmd]

    # Map common argument patterns to git flags
    arg_mappings = {
        "all": "-a",
        "force": "--force",
        "cached": "--cached",
        "porcelain": "--porcelain",
        "oneline": "--oneline",
        "graph": "--graph",
        "short": "--short",
        "verbose": "-v",
        "no_ff": "--no-ff",
        "squash": "--squash",
        "hard": "--hard",
        "soft": "--soft",
        "mixed": "--mixed",
        "interactive": "-i",
        "rebase": "--rebase",
        "amend": "--amend",
        "name_only": "--name-only",
        "set_upstream": "-u",
        "create_branch": "-b",
        "force_delete": "-D",
        "include_untracked": "-u",
        "dry_run": "--dry-run",
        "directories": "-d",
        "ignore_case": "-i",
        "summary": "--summary",
        "numbered": "--numbered",
        "tags": "--tags",
        "others": "--others",
        "ignored": "--ignored",
        "global": "--global",
        "bare": "--bare",
        "no_commit": "--no-commit",
        "recursive": "--recursive",
    }

    # Add boolean flags
    for arg, flag in arg_mappings.items():
        if arguments.get(arg, False):
            cmd_parts.append(flag)

    # Handle special cases
    if "message" in arguments:
        cmd_parts.extend(["-m", arguments["message"]])

    if "max_count" in arguments:
        cmd_parts.extend(["-n", str(arguments["max_count"])])

    if "remote" in arguments and git_cmd in ["push", "pull", "remote_get_url"]:
        cmd_parts.append(arguments["remote"])

    if "branch" in arguments and git_cmd in ["push", "pull", "checkout"]:
        cmd_parts.append(arguments["branch"])

    if "files" in arguments:
        cmd_parts.extend(arguments["files"])

    # Handle specific command logic
    if git_cmd == "remote_get_url":
        cmd_parts = ["git", "remote", "get-url", arguments.get("remote", "origin")]

    elif git_cmd == "branch" and not any(
        k in arguments for k in ["create", "delete", "all"]
    ):
        cmd_parts.append("--show-current")

    elif git_cmd == "remote" and "action" in arguments:
        action = arguments["action"]
        if action == "get-url":
            cmd_parts = ["git", "remote", "get-url", arguments.get("name", "origin")]
        elif action in ["add", "remove"] and "name" in arguments:
            cmd_parts.extend([action, arguments["name"]])
            if action == "add" and "url" in arguments:
                cmd_parts.append(arguments["url"])

    elif git_cmd == "stash" and "action" in arguments:
        action = arguments["action"]
        cmd_parts = ["git", "stash", action]

    return " ".join(cmd_parts)


def git_tool_executor(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute git tools using dynamic command building."""
    try:
        command = build_git_command(tool_name, arguments)
        return execute_git_command(command)
    except Exception as e:
        return f"Failed to execute {tool_name}: {e}"
