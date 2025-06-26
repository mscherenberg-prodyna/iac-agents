"""Basic agent execution tests for coverage."""

from unittest.mock import Mock, patch

import pytest


class TestSecopsAgent:
    """Test secops finops agent basics."""

    @patch("src.iac_agents.agents.nodes.secops_finops.make_llm_call")
    @patch("src.iac_agents.agents.nodes.secops_finops.template_manager")
    def test_executes_successfully(self, mock_template, mock_llm):
        """Should execute and return valid state."""
        from src.iac_agents.agents.nodes.secops_finops import secops_finops_agent

        mock_template.get_prompt.return_value = "prompt"
        mock_llm.return_value = "analysis"

        state = {
            "user_input": "test",
            "conversation_history": ["test"],
            "errors": [],
            "warnings": [],
            "completed_stages": [],
        }

        result = secops_finops_agent(state)

        assert result["current_agent"] == "secops_finops"
        assert "secops_finops_analysis" in result

    def test_handles_errors(self):
        """Should handle execution errors gracefully."""
        from src.iac_agents.agents.nodes.secops_finops import secops_finops_agent

        result = secops_finops_agent({})

        assert "errors" in result
        assert result["current_agent"] == "secops_finops"


class TestTerraformAgent:
    """Test terraform consultant agent basics."""

    @patch("src.iac_agents.agents.nodes.terraform_consultant.make_llm_call")
    @patch("src.iac_agents.agents.nodes.terraform_consultant.template_manager")
    def test_executes_successfully(self, mock_template, mock_llm):
        """Should execute and return valid state."""
        from src.iac_agents.agents.nodes.terraform_consultant import (
            terraform_consultant_agent,
        )

        mock_template.get_prompt.return_value = "prompt"
        mock_llm.return_value = "guidance"

        state = {
            "user_input": "test",
            "conversation_history": ["test"],
            "errors": [],
            "warnings": [],
            "completed_stages": [],
        }

        result = terraform_consultant_agent(state)

        assert result["current_agent"] == "terraform_consultant"
        assert "terraform_guidance" in result

    def test_handles_errors(self):
        """Should handle execution errors gracefully."""
        from src.iac_agents.agents.nodes.terraform_consultant import (
            terraform_consultant_agent,
        )

        result = terraform_consultant_agent({})

        assert "errors" in result
        assert result["current_agent"] == "terraform_consultant"


class TestCloudEngineerAgent:
    """Test cloud engineer agent basics."""

    @patch("src.iac_agents.agents.nodes.cloud_engineer.make_llm_call")
    @patch("src.iac_agents.agents.nodes.cloud_engineer.template_manager")
    def test_sets_terraform_lookup_flag(self, mock_template, mock_llm):
        """Should set terraform lookup flag based on response."""
        from src.iac_agents.agents.nodes.cloud_engineer import cloud_engineer_agent

        mock_template.get_prompt.return_value = "prompt"
        mock_llm.return_value = "need terraform help"

        state = {
            "user_input": "complex infrastructure",
            "conversation_history": ["test"],
            "cloud_architect_analysis": "analysis",
            "errors": [],
            "warnings": [],
            "completed_stages": [],
        }

        result = cloud_engineer_agent(state)

        assert result["current_agent"] == "cloud_engineer"
        assert "needs_terraform_lookup" in result


class TestDevopsAgent:
    """Test devops agent basics."""

    @patch("src.iac_agents.agents.nodes.devops.make_llm_call")
    @patch("src.iac_agents.agents.nodes.devops.template_manager")
    def test_executes_with_template(self, mock_template, mock_llm):
        """Should execute with terraform template."""
        from src.iac_agents.agents.nodes.devops import devops_agent

        mock_template.get_prompt.return_value = "prompt"
        mock_llm.return_value = "deployed"

        state = {
            "user_input": "deploy",
            "conversation_history": ["test"],
            "final_template": "terraform content",
            "approval_received": True,
            "errors": [],
            "warnings": [],
            "completed_stages": [],
        }

        result = devops_agent(state)

        assert result["current_agent"] == "devops"
        assert "devops_response" in result
