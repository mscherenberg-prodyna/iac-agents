"""Utility functions for agent operations."""

import json
import re
import subprocess
from typing import Any, Dict, Optional

from langchain_openai import AzureChatOpenAI

from ..config.settings import config
from .terraform_utils import is_valid_terraform_content


def create_llm_client(temperature: Optional[float] = None) -> AzureChatOpenAI:
    """Create an Azure OpenAI client with standard configuration."""
    return AzureChatOpenAI(
        azure_endpoint=config.azure_openai.endpoint,
        azure_deployment=config.azure_openai.deployment,
        api_version=config.azure_openai.api_version,
        api_key=config.azure_openai.api_key,
        temperature=temperature or config.agents.default_temperature,
        max_tokens=config.agents.max_response_tokens,
    )


def make_llm_call(
    system_prompt: str, user_message: str, temperature: Optional[float] = None
) -> str:
    """Make a standard LLM call with system and user messages."""
    llm = create_llm_client(temperature)
    messages = [("system", system_prompt), ("human", user_message)]
    response = llm.invoke(messages)
    return response.content


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


def add_error_to_state(state: dict, error_message: str) -> list:
    """Add an error message to the state errors list."""
    errors = state.get("errors", [])
    if error_message not in errors:
        errors.append(error_message)
    return errors


def mark_stage_completed(state: dict, stage: str) -> list:
    """Mark a workflow stage as completed."""
    completed_stages = state.get("completed_stages", [])
    if stage not in completed_stages:
        completed_stages.append(stage)
    return completed_stages


def get_azure_subscription_info() -> Dict[str, Any]:
    """Get Azure subscription information using Azure CLI."""
    try:
        # Run az account list command to get subscription information
        result = subprocess.run(
            ["az", "account", "list", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if result.returncode == 0:
            subscriptions = json.loads(result.stdout)

            # Find the default subscription
            default_sub = None
            for sub in subscriptions:
                if sub.get("isDefault", False):
                    default_sub = sub
                    break

            if default_sub:
                return {
                    "default_subscription_name": default_sub.get("name", "Unknown"),
                    "default_subscription_id": default_sub.get("id", "Unknown"),
                    "total_subscriptions": len(subscriptions),
                    "available_subscriptions": [
                        sub.get("name", "Unknown") for sub in subscriptions
                    ],
                }
            return {
                "default_subscription_name": "None (not logged in)",
                "default_subscription_id": "Unknown",
                "total_subscriptions": 0,
                "available_subscriptions": [],
            }
        return {
            "default_subscription_name": "Azure CLI error",
            "default_subscription_id": "Unknown",
            "total_subscriptions": 0,
            "available_subscriptions": [],
        }

    except (
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        FileNotFoundError,
    ):
        return {
            "default_subscription_name": "Azure CLI not available",
            "default_subscription_id": "Unknown",
            "total_subscriptions": 0,
            "available_subscriptions": [],
        }
