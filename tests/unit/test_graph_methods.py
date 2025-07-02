"""Tests for remaining graph methods to boost coverage."""

from unittest.mock import Mock, patch

from src.iac_agents.agents.graph import InfrastructureAsPromptsAgent


class TestGraphMethods:
    """Test remaining graph methods for coverage."""

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_route_secops_finops_needs_terraform(self, mock_graph):
        """Test secops finops routing when terraform needed."""
        agent = InfrastructureAsPromptsAgent()

        state = {"needs_terraform_lookup": True}
        result = agent._route_secops_finops(state)

        assert result == "terraform_consultant"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_route_secops_finops_no_terraform(self, mock_graph):
        """Test secops finops routing when no terraform needed."""
        agent = InfrastructureAsPromptsAgent()

        state = {"needs_terraform_lookup": False}
        result = agent._route_secops_finops(state)

        assert result == "cloud_architect"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_route_human_approval_approved(self, mock_graph):
        """Test human approval routing when approved."""
        agent = InfrastructureAsPromptsAgent()

        state = {"approval_received": True}
        result = agent._route_human_approval(state)

        assert result == "devops"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_route_human_approval_not_approved(self, mock_graph):
        """Test human approval routing when not approved."""
        agent = InfrastructureAsPromptsAgent()

        state = {"approval_received": False}
        result = agent._route_human_approval(state)

        assert result == "cloud_architect"

    @patch("src.iac_agents.agents.graph.StateGraph")
    @patch("src.iac_agents.agents.graph.interrupt")
    def test_human_approval_node(self, mock_interrupt, mock_graph):
        """Test human approval node execution."""
        agent = InfrastructureAsPromptsAgent()

        state = {"user_input": "Deploy infrastructure"}
        result = agent._human_approval_node(state)

        # Should call interrupt and return state
        mock_interrupt.assert_called_once()
        assert result == state

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_build_method(self, mock_graph):
        """Test build method compilation."""
        mock_workflow = Mock()
        mock_compiled = Mock()
        mock_workflow.compile.return_value = mock_compiled
        mock_graph.return_value = mock_workflow

        agent = InfrastructureAsPromptsAgent()
        result = agent.build()

        mock_workflow.compile.assert_called_once()
        assert result == mock_compiled

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_build_with_checkpointer(self, mock_graph):
        """Test build method with memory checkpointer."""
        mock_workflow = Mock()
        mock_compiled = Mock()
        mock_workflow.compile.return_value = mock_compiled
        mock_graph.return_value = mock_workflow

        agent = InfrastructureAsPromptsAgent()

        with patch("src.iac_agents.agents.graph.MemorySaver") as mock_memory:
            mock_checkpointer = Mock()
            mock_memory.return_value = mock_checkpointer

            result = agent.build()

            # Should compile with checkpointer
            mock_workflow.compile.assert_called_once()

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_run_method(self, mock_graph):
        """Test run method execution."""
        mock_workflow = Mock()
        mock_compiled = Mock()
        mock_workflow.compile.return_value = mock_compiled
        mock_graph.return_value = mock_workflow

        # Mock the invoke method
        mock_compiled.invoke.return_value = {"final_response": "Done"}

        agent = InfrastructureAsPromptsAgent()

        input_state = {"user_input": "Create web app"}
        result = agent.run(input_state)

        mock_compiled.invoke.assert_called_once_with(input_state)
        assert result == {"final_response": "Done"}

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_stream_method(self, mock_graph):
        """Test stream method execution."""
        mock_workflow = Mock()
        mock_compiled = Mock()
        mock_workflow.compile.return_value = mock_compiled
        mock_graph.return_value = mock_workflow

        # Mock the stream method
        mock_compiled.stream.return_value = [{"step": 1}, {"step": 2}]

        agent = InfrastructureAsPromptsAgent()

        input_state = {"user_input": "Create web app"}
        result = list(agent.stream(input_state))

        mock_compiled.stream.assert_called_once_with(input_state)
        assert len(result) == 2
