"""Utility functions for agent operations."""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import BingGroundingTool, ListSortOrder, MessageRole
from azure.identity import AzureCliCredential
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI

from ..config.settings import config
from ..logging_system import log_agent_start, log_warning


def create_llm_client(agent_name: str, temperature: float) -> AzureChatOpenAI:
    """Create an Azure OpenAI client with standard configuration."""
    return AzureChatOpenAI(
        azure_endpoint=config.azure_openai.endpoint,
        azure_deployment=config.azure_openai.deployment[agent_name],
        api_version=config.azure_openai.api_version,
        api_key=config.azure_openai.api_key,
        temperature=temperature,
    )


def make_llm_call(
    system_prompt: str,
    user_message: str,
    agent_name: Optional[str] = "default",
    temperature: Optional[float] = None,
) -> str:
    """Make a standard LLM call with system and user messages."""
    llm = create_llm_client(
        agent_name, temperature if temperature else config.agents.default_temperature
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]
    response = llm.invoke(messages)
    return response.content


def load_agent_response_schema() -> Dict[str, Any]:
    """Load the agent response JSON schema."""
    schema_path = Path(__file__).parent / "agent_response_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def make_structured_llm_call(
    system_prompt: str,
    user_message: str,
    agent_name: Optional[str] = "default",
    temperature: Optional[float] = None,
    schema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Make a structured LLM call that returns JSON conforming to agent response schema."""
    llm = create_llm_client(
        agent_name, temperature if temperature else config.agents.default_temperature
    )

    # Load schema for structured output
    if schema is None:
        # Load default schema if not provided
        schema = load_agent_response_schema()

    # Create structured LLM with JSON schema
    structured_llm = llm.with_structured_output(schema, method="json_mode")

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    # Returns a dictionary that conforms to the schema
    response = structured_llm.invoke(messages)

    # Ensure response is a dictionary, parse if it's a string
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}") from e

    return response


def get_github_token() -> str:
    """Get GitHub token from environment variable."""
    token = config.github.github_token
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is not set")
    return token


def get_azure_credentials() -> Tuple[str, str, str]:
    """Get Azure credentials from environment variables."""
    tenant_id = config.azure.tenant_id
    client_id = config.azure.client_id
    client_secret = config.azure.client_secret

    if not tenant_id or not client_id or not client_secret:
        raise ValueError("Azure credentials are not set in the configuration")

    return tenant_id, client_id, client_secret


def get_agent_id_base(agent_name: str, prompt: str) -> str:
    """Update or create AI Foundry Agent without any tools."""
    credential = AzureCliCredential()
    agents_client = AgentsClient(
        endpoint=config.azure_ai.project_endpoint, credential=credential
    )
    agents_foundry = {agent.name: agent.id for agent in agents_client.list_agents()}

    if agent_name in agents_foundry.keys():
        agent_id = agents_foundry[agent_name]
        agents_client.update_agent(agent_id=agent_id, instructions=prompt)
        return agent_id

    output = agents_client.create_agent(
        name=agent_name,
        model=config.agents.default_model,
        instructions=prompt,
        temperature=config.agents.default_temperature,
    )
    return output["id"]


def get_agent_id_bing(agent_name: str, prompt: str) -> str:
    """Update or create AI Foundry Agent that uses Bing search."""
    credential = AzureCliCredential()
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


def query_azure_agent(agent_name: str, agent_id: str, query: str) -> Optional[str]:
    """Query an Azure AI Foundry agent."""
    try:
        credential = AzureCliCredential()
        agents_client = AgentsClient(
            endpoint=config.azure_ai.project_endpoint, credential=credential
        )

        thread = agents_client.threads.create()

        # Send query to the agent
        message = agents_client.messages.create(
            thread_id=thread.id,
            role="user",
            content=query,
        )

        run = agents_client.runs.create_and_process(
            thread_id=thread.id, agent_id=agent_id
        )

        if run.status == "failed":
            log_warning(
                agent_name,
                f"Azure AI run failed for agent {agent_name}: {run.last_error}",
            )
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


def add_error_to_state(state: dict, error_message: str) -> dict:
    """Add an error message to the state errors list."""
    errors = state.get("errors", [])
    if errors is None:
        errors = []
    if error_message not in errors:
        errors.append(error_message)

    # Return updated state with the error added
    updated_state = state.copy()
    updated_state["errors"] = errors
    return updated_state


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


def verify_azure_auth(agent_name: str) -> bool:
    """Verify Azure CLI authentication using active session."""
    try:
        # Check if Azure CLI is installed and authenticated
        result = subprocess.run(
            ["az", "account", "show"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if result.returncode == 0:
            log_agent_start(agent_name, "Azure CLI authentication verified")
            return True
        log_warning(agent_name, f"Azure CLI authentication failed: {result.stderr}")
        return False

    except subprocess.TimeoutExpired:
        log_warning(agent_name, "Azure CLI authentication check timed out")
        return False
    except FileNotFoundError:
        log_warning(agent_name, "Azure CLI not found - please install Azure CLI")
        return False
    except Exception as e:
        log_warning(agent_name, f"Azure authentication verification failed: {str(e)}")
        return False
