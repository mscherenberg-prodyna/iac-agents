"""Configuration settings for the IAC Agents system."""

import os
from dataclasses import dataclass
from typing import Dict

from dotenv import load_dotenv


@dataclass
class ComplianceSettings:
    """Compliance validation settings."""

    minimum_score_enforced: float = 70.0
    minimum_score_relaxed: float = 40.0
    max_violations_enforced: int = 3
    max_violations_relaxed: int = 8

    available_frameworks: Dict[str, str] = None

    def __post_init__(self):
        if self.available_frameworks is None:
            self.available_frameworks = {
                "PCI DSS": "Payment Card Industry Data Security Standard",
                "HIPAA": "Health Insurance Portability and Accountability Act",
                "SOX": "Sarbanes-Oxley Act",
                "GDPR": "General Data Protection Regulation",
                "ISO 27001": "Information Security Management",
                "SOC 2": "Service Organization Control 2",
            }


@dataclass
class AzureOpenAISettings:
    """Azure OpenAI configuration settings."""

    endpoint: str = None
    api_key: str = None
    deployment: str = None
    api_version: str = "2024-02-15-preview"

    def __post_init__(self):
        if self.endpoint is None:
            self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if self.api_key is None:
            self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if self.deployment is None:
            self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        if api_version_env := os.getenv("AZURE_OPENAI_API_VERSION"):
            self.api_version = api_version_env


@dataclass
class AzureAISettings:
    """Azure AI Project configuration settings."""

    project_endpoint: str = None
    bing_connection: str = None

    def __post_init__(self):
        if self.project_endpoint is None:
            self.project_endpoint = os.getenv("AZURE_PROJECT_ENDPOINT")
        if self.bing_connection is None:
            self.bing_connection = os.getenv("BING_CONNECTION")


@dataclass
class AgentSettings:
    """AI Agent configuration settings."""

    default_temperature: float = 0
    default_model: str = "gpt-4.1"
    max_response_tokens: int = 9999
    request_timeout: int = 120  # seconds


@dataclass
class UISettings:
    """User interface configuration."""

    max_chat_messages: int = 50
    activity_log_entries: int = 5
    auto_scroll_delay: int = 200  # milliseconds
    page_title: str = "Infrastructure as Prompts"
    page_icon: str = "🤖"


@dataclass
class LoggingSettings:
    """Logging configuration."""

    log_level: str = "INFO"
    max_log_entries: int = 100
    log_retention_hours: int = 24


@dataclass
class WorkflowSettings:
    """Workflow execution settings."""

    max_workflow_stages: int = 10
    stage_timeout: int = 300  # seconds
    max_template_regeneration_attempts: int = 2


# Global configuration instance
class Config:
    """Main configuration class."""

    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        self.compliance = ComplianceSettings()
        self.azure_openai = AzureOpenAISettings()
        self.azure_ai = AzureAISettings()
        self.agents = AgentSettings()
        self.ui = UISettings()
        self.logging = LoggingSettings()
        self.workflow = WorkflowSettings()

    @classmethod
    def load_from_env(cls):
        """Load configuration from environment variables."""
        return cls()


# Global config instance
config = Config()
