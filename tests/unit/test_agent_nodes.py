"""Unit tests for agent nodes."""

from unittest.mock import Mock, patch

import pytest

from src.iac_agents.agents.nodes.cloud_engineer import cloud_engineer_agent
from src.iac_agents.agents.nodes.devops import devops_agent


class TestCloudEngineerAgent:
    """Test cloud engineer agent node."""

    @patch("src.iac_agents.agents.nodes.cloud_engineer.make_llm_call")
    @patch("src.iac_agents.agents.nodes.cloud_engineer.template_manager")
    def test_cloud_engineer_basic_call(self, mock_template_manager, mock_llm_call):
        """Should handle basic cloud engineer call."""
        mock_template_manager.get_prompt.return_value = "Test prompt"
        mock_llm_call.return_value = "Terraform template content"

        state = {
            "user_input": "Create a web app",
            "conversation_history": ["User input"],
            "cloud_architect_analysis": "Analysis",
            "errors": [],
            "warnings": [],
            "completed_stages": [],
        }

        result = cloud_engineer_agent(state)

        assert result["current_agent"] == "cloud_engineer"
        assert "cloud_engineer_response" in result


class TestDevopsAgent:
    """Test devops agent node."""

    @patch("src.iac_agents.agents.nodes.devops.make_llm_call")
    @patch("src.iac_agents.agents.nodes.devops.template_manager")
    def test_devops_basic_call(self, mock_template_manager, mock_llm_call):
        """Should handle basic devops call."""
        mock_template_manager.get_prompt.return_value = "Test prompt"
        mock_llm_call.return_value = "Deployment response"

        state = {
            "user_input": "Deploy infrastructure",
            "conversation_history": ["User input"],
            "final_template": "terraform content",
            "approval_received": True,
            "errors": [],
            "warnings": [],
            "completed_stages": [],
        }

        result = devops_agent(state)

        assert result["current_agent"] == "devops"
        assert "devops_response" in result
