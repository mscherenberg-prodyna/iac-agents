"""Tests for cloud_engineer agent node."""

from datetime import date
from unittest.mock import MagicMock, Mock, patch

import pytest

from iac_agents.agents.nodes.cloud_engineer import cloud_engineer_agent
from iac_agents.agents.state import WorkflowStage


class TestCloudEngineerAgent:
    """Test suite for cloud engineer agent node."""

    @patch("iac_agents.agents.nodes.cloud_engineer.make_llm_call")
    @patch("iac_agents.agents.nodes.cloud_engineer.extract_terraform_template")
    @patch("iac_agents.agents.nodes.cloud_engineer.template_manager")
    def test_cloud_engineer_agent_basic_flow(
        self, mock_template_manager, mock_extract_terraform, mock_make_llm_call
    ):
        """Test basic cloud engineer agent flow."""
        mock_template_manager.get_prompt.return_value = "system prompt"
        mock_make_llm_call.return_value = "Generated terraform template"
        mock_extract_terraform.return_value = 'resource "aws_instance" "test" {}'

        state = {
            "conversation_history": ["User: Deploy web app"],
            "subscription_info": {
                "default_subscription_name": "test-sub",
                "default_subscription_id": "sub-123",
            },
        }

        result = cloud_engineer_agent(state)

        assert result["current_stage"] == WorkflowStage.TEMPLATE_GENERATION.value
        assert result["cloud_engineer_response"] == "Generated terraform template"
        assert 'resource "aws_instance" "test"' in result["final_template"]
        assert result["needs_terraform_lookup"] is False

    @patch("iac_agents.agents.nodes.cloud_engineer.make_llm_call")
    @patch("iac_agents.agents.nodes.cloud_engineer.extract_terraform_template")
    @patch("iac_agents.agents.nodes.cloud_engineer.template_manager")
    def test_cloud_engineer_agent_with_consultation(
        self, mock_template_manager, mock_extract_terraform, mock_make_llm_call
    ):
        """Test cloud engineer agent with terraform consultation needed."""
        mock_template_manager.get_prompt.return_value = "system prompt"
        mock_make_llm_call.return_value = (
            "TERRAFORM_CONSULTATION_NEEDED for complex setup"
        )
        mock_extract_terraform.return_value = ""

        state = {
            "conversation_history": ["User: Deploy complex app"],
            "subscription_info": {
                "default_subscription_name": "test-sub",
                "default_subscription_id": "sub-123",
            },
        }

        result = cloud_engineer_agent(state)

        assert result["needs_terraform_lookup"] is True
        assert "TERRAFORM_CONSULTATION_NEEDED" in result["cloud_engineer_response"]

    @patch("iac_agents.agents.nodes.cloud_engineer.make_llm_call")
    @patch("iac_agents.agents.nodes.cloud_engineer.extract_terraform_template")
    @patch("iac_agents.agents.nodes.cloud_engineer.template_manager")
    def test_cloud_engineer_agent_with_validation_failure(
        self, mock_template_manager, mock_extract_terraform, mock_make_llm_call
    ):
        """Test cloud engineer agent with validation failure from previous attempt."""
        mock_template_manager.get_prompt.return_value = "system prompt"
        mock_make_llm_call.return_value = "Revised terraform template"
        mock_extract_terraform.return_value = 'resource "aws_instance" "revised" {}'

        state = {
            "conversation_history": ["User: Deploy web app"],
            "subscription_info": {
                "default_subscription_name": "test-sub",
                "default_subscription_id": "sub-123",
            },
            "template_validation_result": {
                "valid": False,
                "error": "Invalid resource configuration",
            },
        }

        result = cloud_engineer_agent(state)

        assert result["cloud_engineer_response"] == "Revised terraform template"
        assert 'resource "aws_instance" "revised"' in result["final_template"]

        # Check that template_manager was called with validation error
        mock_template_manager.get_prompt.assert_called_once()
        call_args = mock_template_manager.get_prompt.call_args
        assert call_args[1]["validation_error"] == "Invalid resource configuration"

    @patch("iac_agents.agents.nodes.cloud_engineer.make_llm_call")
    @patch("iac_agents.agents.nodes.cloud_engineer.extract_terraform_template")
    @patch("iac_agents.agents.nodes.cloud_engineer.template_manager")
    def test_cloud_engineer_agent_with_consultation_and_validation_failure(
        self, mock_template_manager, mock_extract_terraform, mock_make_llm_call
    ):
        """Test cloud engineer agent with both consultation needed and validation failure."""
        mock_template_manager.get_prompt.return_value = "system prompt"
        mock_make_llm_call.return_value = (
            "TERRAFORM_CONSULTATION_NEEDED after validation failure"
        )
        mock_extract_terraform.return_value = ""

        state = {
            "conversation_history": ["User: Deploy complex app"],
            "subscription_info": {
                "default_subscription_name": "test-sub",
                "default_subscription_id": "sub-123",
            },
            "template_validation_result": {
                "valid": False,
                "error": "Complex validation error",
            },
        }

        result = cloud_engineer_agent(state)

        assert result["needs_terraform_lookup"] is True
        assert result["template_validation_result"] is None  # Reset validation result

    @patch("iac_agents.agents.nodes.cloud_engineer.make_llm_call")
    @patch("iac_agents.agents.nodes.cloud_engineer.template_manager")
    @patch("iac_agents.agents.nodes.cloud_engineer.add_error_to_state")
    def test_cloud_engineer_agent_exception_handling(
        self, mock_add_error, mock_template_manager, mock_make_llm_call
    ):
        """Test cloud engineer agent exception handling."""
        mock_template_manager.get_prompt.return_value = "system prompt"
        mock_make_llm_call.side_effect = Exception("LLM call failed")
        mock_add_error.return_value = {
            "conversation_history": ["User: Deploy web app"],
            "subscription_info": {
                "default_subscription_name": "test-sub",
                "default_subscription_id": "sub-123",
            },
            "errors": ["Cloud Engineer error: LLM call failed"],
        }

        state = {
            "conversation_history": ["User: Deploy web app"],
            "subscription_info": {
                "default_subscription_name": "test-sub",
                "default_subscription_id": "sub-123",
            },
            "errors": [],
        }

        result = cloud_engineer_agent(state)

        mock_add_error.assert_called_once_with(
            state, "Cloud Engineer error: LLM call failed"
        )
        assert "errors" in result

    @patch("iac_agents.agents.nodes.cloud_engineer.make_llm_call")
    @patch("iac_agents.agents.nodes.cloud_engineer.extract_terraform_template")
    @patch("iac_agents.agents.nodes.cloud_engineer.template_manager")
    def test_cloud_engineer_agent_conversation_history_update(
        self, mock_template_manager, mock_extract_terraform, mock_make_llm_call
    ):
        """Test that conversation history is properly updated."""
        mock_template_manager.get_prompt.return_value = "system prompt"
        mock_make_llm_call.return_value = "Generated response"
        mock_extract_terraform.return_value = ""

        state = {
            "conversation_history": ["User: Deploy web app"],
            "subscription_info": {
                "default_subscription_name": "test-sub",
                "default_subscription_id": "sub-123",
            },
        }

        result = cloud_engineer_agent(state)

        assert len(result["conversation_history"]) == 2
        assert result["conversation_history"][0] == "User: Deploy web app"
        assert result["conversation_history"][1] == "Cloud Engineer: Generated response"

    @patch("iac_agents.agents.nodes.cloud_engineer.make_llm_call")
    @patch("iac_agents.agents.nodes.cloud_engineer.extract_terraform_template")
    @patch("iac_agents.agents.nodes.cloud_engineer.template_manager")
    def test_cloud_engineer_agent_current_date_passed(
        self, mock_template_manager, mock_extract_terraform, mock_make_llm_call
    ):
        """Test that current date is passed to template manager."""
        mock_template_manager.get_prompt.return_value = "system prompt"
        mock_make_llm_call.return_value = "Generated response"
        mock_extract_terraform.return_value = ""

        state = {
            "conversation_history": ["User: Deploy web app"],
            "subscription_info": {
                "default_subscription_name": "test-sub",
                "default_subscription_id": "sub-123",
            },
        }

        result = cloud_engineer_agent(state)

        # Check that current date was passed to template manager
        mock_template_manager.get_prompt.assert_called_once()
        call_args = mock_template_manager.get_prompt.call_args
        assert call_args[1]["current_date"] == str(date.today())
