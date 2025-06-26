"""Unit tests for state management utilities in agents.utils module."""

import pytest

from src.iac_agents.agents.utils import add_error_to_state, mark_stage_completed


class TestAddErrorToState:
    """Test add_error_to_state function."""

    def test_add_error_to_empty_state(self):
        """Test adding error to state with no existing errors."""
        state = {}
        result = add_error_to_state(state, "Test error")
        assert result == ["Test error"]

    def test_add_error_to_existing_errors(self):
        """Test adding error to state with existing errors."""
        state = {"errors": ["Existing error"]}
        result = add_error_to_state(state, "New error")
        assert result == ["Existing error", "New error"]

    def test_add_duplicate_error(self):
        """Test adding duplicate error to state."""
        state = {"errors": ["Test error"]}
        result = add_error_to_state(state, "Test error")
        assert result == ["Test error"]  # Should not duplicate

    def test_add_error_preserves_other_state(self):
        """Test that adding error doesn't modify other state properties."""
        state = {"other_key": "other_value", "errors": ["Existing error"]}
        result = add_error_to_state(state, "New error")
        assert result == ["Existing error", "New error"]
        assert state["other_key"] == "other_value"  # Should be preserved


class TestMarkStageCompleted:
    """Test mark_stage_completed function."""

    def test_mark_stage_in_empty_state(self):
        """Test marking stage completed in empty state."""
        state = {}
        result = mark_stage_completed(state, "template_generation")
        assert result == ["template_generation"]

    def test_mark_stage_with_existing_stages(self):
        """Test marking stage completed with existing completed stages."""
        state = {"completed_stages": ["requirements_analysis"]}
        result = mark_stage_completed(state, "template_generation")
        assert result == ["requirements_analysis", "template_generation"]

    def test_mark_already_completed_stage(self):
        """Test marking already completed stage."""
        state = {"completed_stages": ["template_generation"]}
        result = mark_stage_completed(state, "template_generation")
        assert result == ["template_generation"]  # Should not duplicate

    def test_mark_stage_preserves_other_state(self):
        """Test that marking stage doesn't modify other state properties."""
        state = {
            "other_key": "other_value",
            "completed_stages": ["requirements_analysis"],
        }
        result = mark_stage_completed(state, "template_generation")
        assert result == ["requirements_analysis", "template_generation"]
        assert state["other_key"] == "other_value"  # Should be preserved

    def test_mark_multiple_stages(self):
        """Test marking multiple stages in sequence."""
        state = {}

        result1 = mark_stage_completed(state, "requirements_analysis")
        state["completed_stages"] = result1

        result2 = mark_stage_completed(state, "template_generation")
        state["completed_stages"] = result2

        result3 = mark_stage_completed(state, "validation_and_compliance")

        assert result3 == [
            "requirements_analysis",
            "template_generation",
            "validation_and_compliance",
        ]
