"""Test graph initialization for coverage."""

from unittest.mock import Mock, patch

import pytest

from src.iac_agents.agents.graph import InfrastructureAsPromptsAgent


class TestAgentInit:
    """Test agent initialization scenarios."""

    @patch("src.iac_agents.agents.graph.StateGraph")
    @patch("src.iac_agents.agents.graph.AIProjectClient")
    def test_init_with_azure_config(self, mock_client, mock_graph):
        """Should initialize with provided azure config."""
        config = {"endpoint": "https://test.ai", "agent_id": "123"}
        agent = InfrastructureAsPromptsAgent(config)

        assert agent.azure_config == config
        mock_client.assert_called_once()

    @patch("src.iac_agents.agents.graph.StateGraph")
    @patch("src.iac_agents.agents.graph.os.getenv")
    def test_init_from_env(self, mock_getenv, mock_graph):
        """Should read config from environment."""
        mock_getenv.side_effect = lambda k: {
            "AZURE_PROJECT_ENDPOINT": "env-endpoint"
        }.get(k)

        agent = InfrastructureAsPromptsAgent()

        assert agent.azure_config["endpoint"] == "env-endpoint"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_init_no_azure_endpoint(self, mock_graph):
        """Should handle missing azure endpoint."""
        agent = InfrastructureAsPromptsAgent({"endpoint": None})

        assert agent.azure_client is None

    @patch("src.iac_agents.agents.graph.StateGraph")
    @patch("src.iac_agents.agents.graph.AIProjectClient")
    def test_init_azure_client_fails(self, mock_client, mock_graph):
        """Should handle azure client initialization failure."""
        mock_client.side_effect = Exception("Azure failed")

        agent = InfrastructureAsPromptsAgent({"endpoint": "test"})

        assert agent.azure_client is None


class TestWorkflowBuild:
    """Test workflow building and execution."""

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_build_compiles_graph(self, mock_graph):
        """Should compile the workflow graph."""
        mock_workflow = Mock()
        mock_graph.return_value = mock_workflow

        agent = InfrastructureAsPromptsAgent()
        result = agent.build()

        mock_workflow.compile.assert_called_once()
        assert result == mock_workflow.compile.return_value

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_run_invokes_graph(self, mock_graph):
        """Should invoke the compiled graph."""
        mock_workflow = Mock()
        mock_compiled = Mock()
        mock_workflow.compile.return_value = mock_compiled
        mock_graph.return_value = mock_workflow

        agent = InfrastructureAsPromptsAgent()
        input_state = {"user_input": "test"}
        result = agent.run(input_state)

        mock_compiled.invoke.assert_called_once_with(input_state)

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_stream_streams_graph(self, mock_graph):
        """Should stream from the compiled graph."""
        mock_workflow = Mock()
        mock_compiled = Mock()
        mock_workflow.compile.return_value = mock_compiled
        mock_compiled.stream.return_value = [{"step": 1}]
        mock_graph.return_value = mock_workflow

        agent = InfrastructureAsPromptsAgent()
        result = list(agent.stream({"user_input": "test"}))

        assert len(result) == 1


class TestHumanApproval:
    """Test human approval node."""

    @patch("src.iac_agents.agents.graph.StateGraph")
    @patch("src.iac_agents.agents.graph.interrupt")
    def test_approval_node_interrupts(self, mock_interrupt, mock_graph):
        """Should call interrupt for human approval."""
        agent = InfrastructureAsPromptsAgent()
        state = {"user_input": "test"}

        result = agent._human_approval_node(state)

        mock_interrupt.assert_called_once_with(
            "Please review and approve the deployment plan"
        )
        assert result == state
