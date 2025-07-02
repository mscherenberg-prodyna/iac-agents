"""Utility functions for agent operations."""

import json
import subprocess
from typing import Any, Dict, Optional

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import BingGroundingTool, ListSortOrder, MessageRole
from azure.identity import DefaultAzureCredential
from langchain_openai import AzureChatOpenAI

from ..config.settings import config
from ..logging_system import log_warning


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


def get_agent_id(agent_name: str, prompt: str) -> str:
    """Update or create AI Foundry Agent."""
    credential = DefaultAzureCredential()
    agents_client = AgentsClient(
        endpoint=config.azure_ai.project_endpoint, credential=credential
    )
    agents_foundry = {agent.name: agent.id for agent in agents_client.list_agents()}

    if agent_name in agents_foundry.keys():
        agent_id = agents_foundry[agent_name]
        agents_client.update_agent(agent_id=agent_id, instructions=prompt)
        return agent_id

    bing_search_tool = BingGroundingTool(connection_id=config.azure_ai.bing_connection)
    output = agents_client.create_agent(
        name=agent_name,
        model=config.agents.default_model,
        instructions=prompt,
        tools=bing_search_tool.definitions,
        temperature=config.agents.default_temperature,
    )
    return output["id"]


def query_azure_agent(
    agent_name: str, agent_id: str, terraform_query: str
) -> Optional[str]:
    """Query the Azure AI Foundry Terraform Consultant agent."""
    try:
        credential = DefaultAzureCredential()
        agents_client = AgentsClient(
            endpoint=config.azure_ai.project_endpoint, credential=credential
        )

        thread = agents_client.threads.create()

        # Send terraform query to the agent
        message = agents_client.messages.create(
            thread_id=thread.id,
            role="user",
            content=terraform_query,
        )

        run = agents_client.runs.create_and_process(
            thread_id=thread.id, agent_id=agent_id
        )

        if run.status == "failed":
            log_warning(agent_name, f"Azure AI run failed: {run.last_error}")
            return None

        messages = agents_client.messages.list(
            thread_id=thread.id, order=ListSortOrder.ASCENDING
        )

        for message in messages:
            if message.text_messages and message.role == MessageRole.AGENT:
                return message.text_messages[-1].text.value

        return None

    except Exception as e:
        log_warning(agent_name, f"Azure AI query failed: {str(e)}")
        return None


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
