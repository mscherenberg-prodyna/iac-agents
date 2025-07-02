"""Test graph routing logic for coverage."""

from unittest.mock import patch

from src.iac_agents.agents.graph import InfrastructureAsPromptsAgent


class TestCloudArchitectRouting:
    """Test cloud architect routing decisions."""

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_routes_to_end_with_final_response(self, mock_graph):
        """Should route to END when final_response exists."""
        agent = InfrastructureAsPromptsAgent()
        state = {"final_response": "Done"}

        from langgraph.graph import END

        assert agent._route_cloud_architect(state) == END

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_routes_to_devops_when_approved(self, mock_graph):
        """Should route to devops when approval received."""
        agent = InfrastructureAsPromptsAgent()
        state = {"approval_received": True}

        assert agent._route_cloud_architect(state) == "devops"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_routes_to_engineer_in_planning(self, mock_graph):
        """Should route to cloud_engineer in planning phase."""
        agent = InfrastructureAsPromptsAgent()
        state = {"workflow_phase": "planning"}

        assert agent._route_cloud_architect(state) == "cloud_engineer"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_routes_to_secops_in_validation(self, mock_graph):
        """Should route to secops_finops in validation phase."""
        agent = InfrastructureAsPromptsAgent()
        state = {"workflow_phase": "validation"}

        assert agent._route_cloud_architect(state) == "secops_finops"


class TestEngineerRouting:
    """Test cloud engineer routing decisions."""

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_routes_to_terraform_when_needed(self, mock_graph):
        """Should route to terraform consultant when lookup needed."""
        agent = InfrastructureAsPromptsAgent()
        state = {
            "needs_terraform_lookup": True,
        }

        assert agent._route_cloud_engineer(state) == "terraform_consultant"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_routes_to_architect_when_terraform_disabled(self, mock_graph):
        """Should route to architect when terraform disabled."""
        agent = InfrastructureAsPromptsAgent()
        state = {
            "needs_terraform_lookup": True,
        }

        assert agent._route_cloud_engineer(state) == "cloud_architect"


class TestSecopsRouting:
    """Test secops finops routing decisions."""

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_routes_to_terraform_when_needed(self, mock_graph):
        """Should route to terraform when lookup needed."""
        agent = InfrastructureAsPromptsAgent()
        state = {"needs_terraform_lookup": True}

        assert agent._route_secops_finops(state) == "terraform_consultant"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_routes_to_architect_when_done(self, mock_graph):
        """Should route to architect when no terraform needed."""
        agent = InfrastructureAsPromptsAgent()
        state = {"needs_terraform_lookup": False}

        assert agent._route_secops_finops(state) == "cloud_architect"


class TestApprovalRouting:
    """Test human approval routing decisions."""

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_routes_to_devops_when_approved(self, mock_graph):
        """Should route to devops when approved."""
        agent = InfrastructureAsPromptsAgent()
        state = {"approval_received": True}

        assert agent._route_human_approval(state) == "devops"

    @patch("src.iac_agents.agents.graph.StateGraph")
    def test_routes_to_architect_when_rejected(self, mock_graph):
        """Should route to architect when not approved."""
        agent = InfrastructureAsPromptsAgent()
        state = {"approval_received": False}

        assert agent._route_human_approval(state) == "cloud_architect"
