"""Utility functions for agent operations."""

import re
from typing import Optional

from langchain_openai import AzureChatOpenAI

from ..config.settings import config


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
        if _is_valid_terraform_content(match):
            return match.strip()

    # Look for terraform blocks without code fences
    if "resource " in response or "terraform {" in response:
        lines = response.split("\n")
        terraform_lines = []
        in_terraform_block = False

        for line in lines:
            if any(
                keyword in line.lower()
                for keyword in [
                    "terraform {",
                    "provider ",
                    "resource ",
                    "variable ",
                    "output ",
                ]
            ):
                in_terraform_block = True

            if in_terraform_block:
                terraform_lines.append(line)

        if terraform_lines:
            content = "\n".join(terraform_lines).strip()
            if _is_valid_terraform_content(content):
                return content

    return ""


def _is_valid_terraform_content(content: str) -> bool:
    """Check if content looks like valid Terraform code."""
    if not content:
        return False

    content_lower = content.lower()
    terraform_keywords = ["terraform", "provider", "resource", "variable", "output"]
    has_terraform_keywords = any(
        keyword in content_lower for keyword in terraform_keywords
    )
    has_hcl_syntax = any(char in content for char in ["{", "}", "="])

    return has_terraform_keywords and has_hcl_syntax


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
