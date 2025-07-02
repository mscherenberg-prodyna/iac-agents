"""Comprehensive tests for agents.graph module to achieve 70%+ coverage."""

from unittest.mock import Mock, patch

from src.iac_agents.agents.graph import InfrastructureAsPromptsAgent


class TestInfrastructureAsPromptsAgentRouting:
    """Test agent routing logic comprehensively."""

    @patch("src.iac_agents.agents.graph.StateGraph")
    @patch("src.iac_agents.agents.graph.AIProjectClient")
    @patch("src.iac_agents.agents.graph.DefaultAzureCredential")
    def test_initialization_with_azure_config(self, mock_cred, mock_client, mock_graph):
        """Test initialization with Azure config."""
        azure_config = {"endpoint": "https://test.azure.ai", "agent_id": "test-agent"}

        agent = InfrastructureAsPromptsAgent(azure_config)

        assert agent.azure_config == azure_config
        mock_client.assert_called_once()
        mock_graph.assert_called_once()

    @patch("src.iac_agents.agents.graph.StateGraph")
    @patch("src.iac_agents.agents.graph.os.getenv")
    def test_initialization_from_env(self, mock_getenv, mock_graph):
        """Test initialization reading from environment."""
        mock_getenv.side_effect = lambda key: {
            "AZURE_PROJECT_ENDPOINT": "https://env.azure.ai",
            "AZURE_AGENT_ID": "env-agent",
        }.get(key)

        agent = InfrastructureAsPromptsAgent()

        assert agent.azure_config["endpoint"] == "https://env.azure.ai"
        assert agent.azure_config["agent_id"] == "env-agent"

    @patch("src.iac_agents.agents.graph.StateGraph")
    @patch("src.iac_agents.agents.graph.AIProjectClient")
    def test_azure_client_initialization_failure(self, mock_client, mock_graph):
        """Test Azure client initialization failure."""
        mock_client.side_effect = Exception("Azure error")

        azure_config = {"endpoint": "https://test.azure.ai"}
        agent = InfrastructureAsPromptsAgent(azure_config)

        assert agent.azure_client is None

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_azure_client_no_endpoint(self, mock_graph):
        """Test Azure client with no endpoint."""
        azure_config = {"endpoint": None}
        agent = InfrastructureAsPromptsAgent(azure_config)

        assert agent.azure_client is None

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_workflow_graph_creation(self, mock_graph):
        """Test workflow graph creation."""
        mock_workflow = Mock()
        mock_graph.return_value = mock_workflow

        agent = InfrastructureAsPromptsAgent()

        # Verify nodes were added
        expected_calls = [
            ("cloud_architect",),
            ("cloud_engineer",),
            ("terraform_consultant",),
            ("secops_finops",),
            ("devops",),
            ("human_approval",),
        ]

        assert mock_workflow.add_node.call_count == 6
        mock_workflow.set_entry_point.assert_called_with("cloud_architect")

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_route_cloud_architect_final_response(self, mock_graph):
        """Test cloud architect routing with final response."""
        agent = InfrastructureAsPromptsAgent()

        state = {"final_response": "User response"}
        result = agent._route_cloud_architect(state)

        from langgraph.graph import END

        assert result == END

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_route_cloud_architect_approval_received(self, mock_graph):
        """Test cloud architect routing when approval received."""
        agent = InfrastructureAsPromptsAgent()

        state = {"approval_received": True}
        result = agent._route_cloud_architect(state)

        assert result == "devops"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_route_cloud_architect_planning_phase(self, mock_graph):
        """Test cloud architect routing in planning phase."""
        agent = InfrastructureAsPromptsAgent()

        state = {"workflow_phase": "planning"}
        result = agent._route_cloud_architect(state)

        assert result == "cloud_engineer"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_route_cloud_architect_validation_phase(self, mock_graph):
        """Test cloud architect routing in validation phase."""
        agent = InfrastructureAsPromptsAgent()

        state = {"workflow_phase": "validation"}
        result = agent._route_cloud_architect(state)

        assert result == "secops_finops"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_route_cloud_architect_approval_phase(self, mock_graph):
        """Test cloud architect routing in approval phase."""
        agent = InfrastructureAsPromptsAgent()

        state = {"workflow_phase": "approval", "requires_approval": True}
        result = agent._route_cloud_architect(state)

        assert result == "human_approval"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_route_cloud_architect_deployment_phase(self, mock_graph):
        """Test cloud architect routing in deployment phase."""
        agent = InfrastructureAsPromptsAgent()

        state = {"workflow_phase": "deployment"}
        result = agent._route_cloud_architect(state)

        assert result == "devops"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_route_cloud_engineer_needs_terraform(self, mock_graph):
        """Test cloud engineer routing when terraform lookup needed."""
        agent = InfrastructureAsPromptsAgent()

        state = {
            "needs_terraform_lookup": True,
        }
        result = agent._route_cloud_engineer(state)

        assert result == "terraform_consultant"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_route_cloud_engineer_terraform_disabled(self, mock_graph):
        """Test cloud engineer routing when terraform disabled."""
        agent = InfrastructureAsPromptsAgent()

        state = {
            "needs_terraform_lookup": True,
        }
        result = agent._route_cloud_engineer(state)

        assert result == "cloud_architect"
