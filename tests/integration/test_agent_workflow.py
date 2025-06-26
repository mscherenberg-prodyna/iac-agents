"""Integration tests for agent workflow."""

from unittest.mock import patch

from src.iac_agents.agents.nodes.cloud_architect import cloud_architect_agent


class TestAgentWorkflowIntegration:
    """Test agent workflow integration."""

    @patch("src.iac_agents.agents.nodes.cloud_architect.make_llm_call")
    @patch("src.iac_agents.agents.nodes.cloud_architect.get_azure_subscription_info")
    @patch("src.iac_agents.agents.nodes.cloud_architect.template_manager")
    def test_cloud_architect_basic_flow(
        self, mock_template_manager, mock_azure_info, mock_llm_call
    ):
        """Test basic cloud architect agent flow."""
        # Setup mocks
        mock_azure_info.return_value = {
            "default_subscription_name": "Test Subscription",
            "available_subscriptions": ["Test Subscription"],
        }
        mock_template_manager.get_prompt.return_value = "Test prompt"
        mock_llm_call.return_value = "Cloud architect response"

        # Create test state
        state = {
            "user_input": "Create a web app",
            "conversation_history": ["User: Create a web app"],
            "compliance_settings": {},
            "completed_stages": [],
            "errors": [],
            "warnings": [],
            "requires_approval": True,
            "approval_received": False,
            "current_stage": None,
            "subscription_info": None,
            "needs_terraform_lookup": False,
            "needs_pricing_lookup": False,
            # Add all required fields from InfrastructureStateDict
            "deployment_config": None,
            "phase_iterations": None,
            "requirements_analysis_result": None,
            "research_data_result": None,
            "template_generation_result": None,
            "compliance_validation_result": None,
            "template_validation_result": None,
            "cost_estimation_result": None,
            "approval_preparation_result": None,
            "final_template": None,
            "final_response": None,
            "approval_request_id": None,
            "current_agent": None,
            "workflow_phase": None,
            "cloud_architect_analysis": None,
            "cloud_engineer_response": None,
            "secops_finops_analysis": None,
            "terraform_guidance": None,
            "terraform_pricing_query": None,
            "devops_response": None,
            "deployment_status": None,
            "deployment_details": None,
            "resource_deployment_plan": None,
            "terraform_workspace": None,
            "terraform_consultant_caller": None,
        }

        # Call the agent
        result = cloud_architect_agent(state)

        # Verify basic functionality
        assert result["current_agent"] == "cloud_architect"
        assert "Cloud architect response" in result["conversation_history"]
        assert result["workflow_phase"] == "planning"
        assert result["cloud_architect_analysis"] == "Cloud architect response"

    @patch("src.iac_agents.agents.nodes.cloud_architect.get_azure_subscription_info")
    def test_cloud_architect_error_handling(self, mock_azure_info):
        """Test cloud architect agent error handling."""
        # Setup mock to avoid external dependencies
        mock_azure_info.return_value = {"default_subscription_name": "Test"}

        # Create minimal state with missing conversation_history to trigger KeyError
        state = {
            "user_input": "test",
            "errors": [],
            "warnings": [],
            "completed_stages": [],
            # Missing conversation_history to trigger error
        }

        result = cloud_architect_agent(state)

        # Should handle error gracefully
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert result["current_agent"] == "cloud_architect"
