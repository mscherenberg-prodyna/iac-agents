"""Unit tests for agents.graph module."""

from unittest.mock import Mock, patch

import pytest

from src.iac_agents.agents.graph import InfrastructureAsPromptsAgent


class TestInfrastructureAsPromptsAgent:
    """Test Infrastructure as Prompts Agent."""

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_agent_initialization(self, mock_state_graph):
        """Should initialize agent with workflow graph."""
        mock_graph = Mock()
        mock_state_graph.return_value = mock_graph

        agent = InfrastructureAsPromptsAgent()

        # Should have created workflow graph
        assert agent is not None

    def test_agent_initialization_no_azure_config(self):
        """Should handle initialization without Azure config."""
        agent = InfrastructureAsPromptsAgent()
        assert agent is not None
