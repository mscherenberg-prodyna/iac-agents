"""Utils for executing GitHub environment management operations using PyGithub."""

import json
import subprocess
from typing import Any, Dict, List

from github import Auth, Github
from github.GithubException import GithubException

from ..templates.template_loader import template_loader
from .utils import get_github_token


def get_github_env_tools() -> List[Dict[str, Any]]:
    """Load GitHub environment tools from template."""
    try:
        return template_loader.load_tools("github_env_tools")
    except Exception as e:
        print(f"Warning: Failed to load GitHub environment tools: {e}")
        return []


def get_repo_from_arguments(g: Github, arguments: Dict[str, Any]):
    """Get repository from arguments or current git repo."""
    if "owner" in arguments and "repo" in arguments:
        return g.get_repo(f"{arguments['owner']}/{arguments['repo']}")
    if "repository" in arguments:
        return g.get_repo(arguments["repository"])

    # Handle case where only 'repo' is provided - try to get owner from authenticated user
    if "repo" in arguments:
        try:
            user = g.get_user()
            return g.get_repo(f"{user.login}/{arguments['repo']}")
        except Exception:
            # If getting authenticated user fails, try organizations
            pass

    # Default to current repo
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode == 0:
        url = result.stdout.strip()
        if "github.com" in url:
            if url.startswith("git@github.com:"):
                repo_path = url.replace("git@github.com:", "").replace(".git", "")
            else:
                repo_path = url.split("github.com/")[1].replace(".git", "")
            return g.get_repo(repo_path)

    raise ValueError(
        "Could not determine repository. Specify 'owner' and 'repo',"
        "repository', or ensure you're in a GitHub repository directory."
    )


class GitHubEnvironmentAPI:
    """GitHub Environment API operations using native PyGithub methods."""

    def __init__(self, repo):
        self.repo = repo

    def create_environment(self, arguments: Dict[str, Any]) -> str:
        """Create a GitHub environment using native PyGithub."""
        env_name = arguments["environment_name"]

        # Use native PyGithub environment creation
        env = self.repo.create_environment(
            environment_name=env_name,
            wait_timer=arguments.get("wait_timer", 0),
            reviewers=arguments.get("reviewers", []),
            deployment_branch_policy={
                "protected_branches": arguments.get("protected_branches", False),
                "custom_branch_policies": arguments.get("custom_branch_policies", True),
            },
        )
        return f"Environment creation result: {env}"

    def list_environments(
        self, arguments: Dict[str, Any]  # pylint: disable=unused-argument
    ) -> str:
        """List all environments using native PyGithub."""
        environments = self.repo.get_environments()
        env_list = []
        for env in environments:
            env_data = {
                "name": env.name,
                "id": env.id,
                "created_at": env.created_at.isoformat() if env.created_at else None,
                "updated_at": env.updated_at.isoformat() if env.updated_at else None,
            }
            env_list.append(env_data)
        return json.dumps({"environments": env_list}, indent=2)

    def get_environment(self, arguments: Dict[str, Any]) -> str:
        """Get environment details using native PyGithub."""
        env_name = arguments["environment_name"]
        env = self.repo.get_environment(env_name)
        env_data = {
            "name": env.name,
            "id": env.id,
            "created_at": env.created_at.isoformat() if env.created_at else None,
            "updated_at": env.updated_at.isoformat() if env.updated_at else None,
        }
        return json.dumps(env_data, indent=2)

    def delete_environment(self, arguments: Dict[str, Any]) -> str:
        """Delete environment using native PyGithub."""
        env_name = arguments["environment_name"]
        env = self.repo.get_environment(env_name)
        env.delete()
        return f"Environment '{env_name}' deleted successfully"

    def create_secret(self, arguments: Dict[str, Any]) -> str:
        """Create an environment secret using native PyGithub."""
        env_name = arguments["environment_name"]
        secret_name = arguments.get("secret_name") or arguments.get("name")
        secret_value = arguments.get("secret_value") or arguments.get("value")

        if not secret_name:
            raise ValueError("Secret name is required (use 'secret_name' or 'name')")
        if not secret_value:
            raise ValueError("Secret value is required (use 'secret_value' or 'value')")

        env = self.repo.get_environment(env_name)
        env.create_secret(secret_name, secret_value)
        return f"Secret '{secret_name}' created in environment '{env_name}'"

    def list_secrets(self, arguments: Dict[str, Any]) -> str:
        """List environment secrets using native PyGithub."""
        env_name = arguments["environment_name"]
        env = self.repo.get_environment(env_name)
        secrets = env.get_secrets()

        secret_list = []
        for secret in secrets:
            secret_data = {
                "name": secret.name,
                "created_at": (
                    secret.created_at.isoformat() if secret.created_at else None
                ),
                "updated_at": (
                    secret.updated_at.isoformat() if secret.updated_at else None
                ),
            }
            secret_list.append(secret_data)
        return json.dumps({"secrets": secret_list}, indent=2)

    def delete_secret(self, arguments: Dict[str, Any]) -> str:
        """Delete an environment secret using native PyGithub."""
        env_name = arguments["environment_name"]
        secret_name = arguments.get("secret_name") or arguments.get("name")

        if not secret_name:
            raise ValueError("Secret name is required (use 'secret_name' or 'name')")

        env = self.repo.get_environment(env_name)
        secret = env.get_secret(secret_name)
        secret.delete()
        return f"Secret '{secret_name}' deleted from environment '{env_name}'"

    def create_variable(self, arguments: Dict[str, Any]) -> str:
        """Create an environment variable using native PyGithub."""
        env_name = arguments["environment_name"]
        var_name = arguments.get("variable_name") or arguments.get("name")
        var_value = arguments.get("variable_value") or arguments.get("value")

        if not var_name:
            raise ValueError(
                "Variable name is required (use 'variable_name' or 'name')"
            )
        if not var_value:
            raise ValueError(
                "Variable value is required (use 'variable_value' or 'value')"
            )

        env = self.repo.get_environment(env_name)
        env.create_variable(var_name, var_value)
        return f"Variable '{var_name}' created in environment '{env_name}'"

    def list_variables(self, arguments: Dict[str, Any]) -> str:
        """List environment variables using native PyGithub."""
        env_name = arguments["environment_name"]
        env = self.repo.get_environment(env_name)
        variables = env.get_variables()

        var_list = []
        for var in variables:
            var_data = {
                "name": var.name,
                "value": var.value,
                "created_at": var.created_at.isoformat() if var.created_at else None,
                "updated_at": var.updated_at.isoformat() if var.updated_at else None,
            }
            var_list.append(var_data)
        return json.dumps({"variables": var_list}, indent=2)

    def delete_variable(self, arguments: Dict[str, Any]) -> str:
        """Delete an environment variable using native PyGithub."""
        env_name = arguments["environment_name"]
        var_name = arguments.get("variable_name") or arguments.get("name")

        if not var_name:
            raise ValueError(
                "Variable name is required (use 'variable_name' or 'name')"
            )

        env = self.repo.get_environment(env_name)
        variable = env.get_variable(var_name)
        variable.delete()
        return f"Variable '{var_name}' deleted from environment '{env_name}'"


def github_env_tool_executor(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute GitHub environment tools using command dispatch."""
    try:
        token = get_github_token()
        auth = Auth.Token(token)
        g = Github(auth=auth)

        repo = get_repo_from_arguments(g, arguments)
        api = GitHubEnvironmentAPI(repo)

        # Extract command and dispatch (tool names come without prefix from MultiMCPClient)
        command = tool_name
        handler = getattr(api, command, None)

        if not handler:
            return f"Unknown command: {command}"

        return handler(arguments)

    except GithubException as e:
        return f"GitHub API error: {e.status} - {e.data.get('message', str(e))}"
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"
