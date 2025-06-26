"""Unit tests for cloud architect agent."""

from unittest.mock import Mock, patch

import pytest

from src.iac_agents.agents.nodes.cloud_architect import (
    AGENT_NAME,
    _determine_workflow_phase,
    _should_generate_user_response,
)


class TestDetermineWorkflowPhase:
    """Test workflow phase determination logic."""

    def test_initial_phase(self):
        """Should return planning for initial state."""
        state = {"completed_stages": []}
        phase = _determine_workflow_phase(state)
        assert phase == "planning"

    def test_template_generated_moves_to_validation(self):
        """Should move to validation after template generation."""
        state = {"completed_stages": ["template_generation"]}
        phase = _determine_workflow_phase(state)
        assert phase == "validation"

    def test_validation_complete_moves_to_approval(self):
        """Should move to approval after validation."""
        state = {
            "completed_stages": ["template_generation", "validation_and_compliance"],
            "requires_approval": True,
            "approval_received": False,
        }
        phase = _determine_workflow_phase(state)
        assert phase == "approval"

    def test_approval_received_moves_to_deployment(self):
        """Should move to deployment after approval."""
        state = {
            "completed_stages": ["validation_and_compliance"],
            "approval_received": True,
        }
        phase = _determine_workflow_phase(state)
        assert phase == "deployment"

    def test_loop_detection_forces_progression(self):
        """Should force progression if stuck in same phase."""
        state = {
            "completed_stages": [],
            "workflow_phase": "planning",
            "phase_iterations": {"planning": 4},  # More than 3
        }
        phase = _determine_workflow_phase(state)
        assert phase == "validation"  # Should force progression


class TestShouldGenerateUserResponse:
    """Test user response determination logic."""

    def test_errors_trigger_user_response(self):
        """Should respond to user when there are errors."""
        state = {"errors": ["Some error occurred"]}
        assert _should_generate_user_response(state, "content") is True

    def test_approval_phase_triggers_user_response(self):
        """Should respond to user in approval phase."""
        state = {"workflow_phase": "approval", "errors": []}
        assert _should_generate_user_response(state, "content") is True

    def test_deployment_complete_triggers_user_response(self):
        """Should respond to user when deployment is complete."""
        state = {
            "workflow_phase": "deployment",
            "deployment_status": "completed",
            "errors": [],
        }
        assert _should_generate_user_response(state, "content") is True

    def test_clarification_required_triggers_user_response(self):
        """Should respond to user when clarification is needed."""
        state = {"errors": []}
        response_content = "CLARIFICATION_REQUIRED: Please provide more details"
        assert _should_generate_user_response(state, response_content) is True

    def test_internal_coordination_no_user_response(self):
        """Should not respond to user for internal coordination."""
        state = {"workflow_phase": "planning", "errors": []}
        response_content = "Internal analysis complete"
        assert _should_generate_user_response(state, response_content) is False
