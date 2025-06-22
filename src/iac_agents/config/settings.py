"""Configuration settings for the IAC Agents system."""

from dataclasses import dataclass
from typing import Dict


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
class AgentSettings:
    """AI Agent configuration settings."""

    default_temperature: float = 0.2
    terraform_agent_temperature: float = 0.1
    max_response_tokens: int = 4000
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
        self.compliance = ComplianceSettings()
        self.agents = AgentSettings()
        self.ui = UISettings()
        self.logging = LoggingSettings()
        self.workflow = WorkflowSettings()

    @classmethod
    def load_from_env(cls):
        """Load configuration from environment variables."""
        # This could be extended to read from environment variables
        return cls()


# Global config instance
config = Config()
