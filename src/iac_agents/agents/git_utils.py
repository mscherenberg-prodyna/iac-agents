"""Utils for executing git commands in a local repository."""

import os
import subprocess
from typing import Any, Dict


def execute_git_command(command: str) -> str:
    """Execute a local git command and return the result."""
    try:
        result = subprocess.run(
            command.split(),
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


git_tools = [
    {
        "name": "git_push",
        "description": "Push commits to remote repository",
        "inputSchema": {
            "type": "object",
            "properties": {
                "remote": {
                    "type": "string",
                    "description": "Remote name (default: origin)",
                    "default": "origin",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (default: current branch)",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force push",
                    "default": False,
                },
            },
        },
    },
    {
        "name": "git_remote_get_url",
        "description": "Get the URL of a git remote (default: origin)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "remote": {
                    "type": "string",
                    "description": "Name of the remote (default: origin)",
                    "default": "origin",
                }
            },
        },
    },
    {
        "name": "git_status",
        "description": "Get git repository status",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "git_branch",
        "description": "List git branches or get current branch",
        "inputSchema": {
            "type": "object",
            "properties": {
                "list_all": {
                    "type": "boolean",
                    "description": "List all branches including remote ones",
                    "default": False,
                }
            },
        },
    },
    {
        "name": "git_log",
        "description": "Show git commit history",
        "inputSchema": {
            "type": "object",
            "properties": {
                "max_count": {
                    "type": "integer",
                    "description": "Maximum number of commits to show",
                    "default": 10,
                },
                "oneline": {
                    "type": "boolean",
                    "description": "Show one line per commit",
                    "default": True,
                },
            },
        },
    },
]


def git_tool_executor(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute git tools using the git command function."""

    command_builders = {
        "git_push": lambda args: f"git push {'--force' if args.get('force', False) else ''} {args.get('remote', 'origin')} {args.get('branch', '')}".strip(),
        "git_remote_get_url": lambda args: f"git remote get-url {args.get('remote', 'origin')}",
        "git_status": "git status --porcelain",
        "git_branch": lambda args: (
            "git branch -a"
            if args.get("list_all", False)
            else "git branch --show-current"
        ),
        "git_log": lambda args: f"git log {'--oneline' if args.get('oneline', True) else ''} -n {args.get('max_count', 10)}".strip(),
    }

    if tool_name not in command_builders:
        return f"Unknown git tool: {tool_name}"

    command = command_builders[tool_name](arguments)
    return execute_git_command(command)
