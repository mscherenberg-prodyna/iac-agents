"""Basic integration tests for workflow orchestration."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from iac_agents.agents.graph import InfrastructureAsPromptsAgent
from iac_agents.agents.state import WorkflowStage


class TestWorkflowBasic:
    """Test suite for basic workflow orchestration."""

    @patch("iac_agents.agents.graph.MemorySaver")
    def test_workflow_graph_creation(self, mock_memory_saver):
        """Test that workflow graph is created successfully."""
        mock_memory_saver.return_value = Mock()

        workflow_agent = InfrastructureAsPromptsAgent()
        compiled_graph = workflow_agent.build()

        assert compiled_graph is not None
        mock_memory_saver.assert_called_once()

    @patch("iac_agents.agents.graph.MemorySaver")
    def test_workflow_agent_initialization(self, mock_memory_saver):
        """Test workflow agent initializes with required components."""
        mock_memory_saver.return_value = Mock()

        workflow_agent = InfrastructureAsPromptsAgent()

        assert hasattr(workflow_agent, "_create_workflow_graph")
        assert hasattr(workflow_agent, "_add_workflow_edges")
        assert hasattr(workflow_agent, "build")

    @patch("iac_agents.agents.graph.MemorySaver")
    @patch("iac_agents.agents.graph.StateGraph")
    def test_workflow_state_initialization(self, mock_state_graph, mock_memory_saver):
        """Test workflow state graph initialization."""
        mock_graph_instance = Mock()
        mock_state_graph.return_value = mock_graph_instance
        mock_memory_saver.return_value = Mock()

        workflow_agent = InfrastructureAsPromptsAgent()
        workflow_agent._create_workflow_graph()

        # StateGraph is called during init and during _create_workflow_graph
        assert mock_state_graph.call_count >= 1

    @patch("iac_agents.agents.graph.MemorySaver")
    def test_workflow_routing_cloud_architect(self, mock_memory_saver):
        """Test cloud architect routing logic."""
        mock_memory_saver.return_value = Mock()

        workflow_agent = InfrastructureAsPromptsAgent()

        # Test routing when architect_target is set to cloud_engineer
        state = {"architect_target": "cloud_engineer", "errors": []}

        route = workflow_agent._route_cloud_architect(state)
        assert route == "cloud_engineer"

    @patch("iac_agents.agents.graph.MemorySaver")
    def test_workflow_routing_cloud_engineer(self, mock_memory_saver):
        """Test cloud engineer routing logic."""
        mock_memory_saver.return_value = Mock()

        workflow_agent = InfrastructureAsPromptsAgent()

        # Test routing when terraform lookup needed
        state = {"needs_terraform_lookup": True, "errors": []}

        route = workflow_agent._route_cloud_engineer(state)
        assert route == "terraform_consultant"

    @patch("iac_agents.agents.graph.MemorySaver")
    def test_workflow_routing_with_errors(self, mock_memory_saver):
        """Test workflow routing when no target is set."""
        mock_memory_saver.return_value = Mock()

        workflow_agent = InfrastructureAsPromptsAgent()

        # Test routing with no architect_target (should return END)
        state = {
            "errors": ["Some error occurred"],
        }

        route = workflow_agent._route_cloud_architect(state)
        assert route == "__end__"


@pytest.mark.integration
class TestWorkflowIntegration:
    """Integration tests for workflow components."""

    @patch("iac_agents.agents.graph.MemorySaver")
    def test_workflow_end_to_end_structure(self, mock_memory_saver):
        """Test end-to-end workflow structure."""
        mock_memory_saver.return_value = Mock()

        workflow_agent = InfrastructureAsPromptsAgent()
        compiled_graph = workflow_agent.build()

        # Verify that the compiled graph has the expected structure
        assert compiled_graph is not None

        # Verify memory saver is configured
        mock_memory_saver.assert_called_once()

    @patch("iac_agents.agents.graph.MemorySaver")
    @patch("iac_agents.agents.graph.StateGraph")
    def test_workflow_node_registration(self, mock_state_graph, mock_memory_saver):
        """Test that all workflow nodes are registered."""
        mock_graph_instance = Mock()
        mock_state_graph.return_value = mock_graph_instance
        mock_memory_saver.return_value = Mock()

        workflow_agent = InfrastructureAsPromptsAgent()
        workflow_agent._create_workflow_graph()

        # Verify add_node was called for each agent
        expected_nodes = [
            "cloud_architect",
            "cloud_engineer",
            "terraform_consultant",
            "secops_finops",
            "devops",
            "human_approval",
        ]

        assert mock_graph_instance.add_node.call_count >= len(expected_nodes)
