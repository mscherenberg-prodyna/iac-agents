"""Tests for state management utilities."""

import pytest

from iac_agents.agents.utils import add_error_to_state


class TestAddErrorToState:
    """Test suite for add_error_to_state function."""

    def test_add_error_to_empty_state(self):
        """Test adding error to empty state."""
        state = {}
        errors = add_error_to_state(state, "Test error")

        assert errors == ["Test error"]
        assert state.get("errors", []) == []

    def test_add_error_to_state_with_existing_errors(self):
        """Test adding error to state with existing errors."""
        state = {"errors": ["Existing error"]}
        errors = add_error_to_state(state, "New error")

        assert errors == ["Existing error", "New error"]

    def test_add_duplicate_error_prevention(self):
        """Test adding duplicate error is prevented."""
        state = {"errors": ["Existing error"]}
        errors = add_error_to_state(state, "Existing error")

        assert errors == ["Existing error"]
        assert len(errors) == 1

    def test_add_error_with_none_errors(self):
        """Test adding error when errors is None."""
        state = {"errors": None}
        errors = add_error_to_state(state, "Test error")

        assert errors == ["Test error"]

    def test_add_multiple_unique_errors(self):
        """Test adding multiple unique errors."""
        state = {"errors": ["First error"]}

        errors1 = add_error_to_state(state, "Second error")
        state["errors"] = errors1

        errors2 = add_error_to_state(state, "Third error")

        assert errors2 == ["First error", "Second error", "Third error"]

    def test_add_error_with_empty_string(self):
        """Test adding empty string error."""
        state = {}
        errors = add_error_to_state(state, "")

        assert errors == [""]

    def test_add_error_preserves_original_state(self):
        """Test that original state is not modified."""
        original_state = {"errors": ["Original error"]}
        state_copy = {"errors": original_state["errors"].copy()}

        errors = add_error_to_state(state_copy, "New error")

        assert original_state == {"errors": ["Original error"]}
        assert errors == ["Original error", "New error"]
