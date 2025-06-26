"""Additional tests for coverage improvement."""

import pytest

from src.iac_agents.agents.terraform_utils import TerraformVariableManager


class TestAdditionalTerraformUtils:
    """Additional terraform utility tests."""

    def test_extract_property_with_quotes(self):
        """Should extract property with quotes."""
        var_block = 'description = "Test description"'
        result = TerraformVariableManager._extract_property(var_block, "description")
        assert result == "Test description"

    def test_extract_property_not_found(self):
        """Should return None when property not found."""
        var_block = "type = string"
        result = TerraformVariableManager._extract_property(var_block, "description")
        assert result is None

    def test_generate_vars_file_empty(self):
        """Should generate vars file with header only for empty variables."""
        result = TerraformVariableManager.generate_terraform_vars_file({})
        assert "# Auto-generated variable values" in result
        assert len(result.split("\n")) == 1


class TestAdditionalStateCoverage:
    """Additional state coverage tests."""

    def test_stage_result_with_errors_and_warnings(self):
        """Should handle StageResult with errors and warnings."""
        from src.iac_agents.agents.state import StageResult

        result = StageResult(
            status="failed", errors=["Error 1", "Error 2"], warnings=["Warning 1"]
        )
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert result.status == "failed"


class TestAdditionalConfigCoverage:
    """Additional configuration coverage tests."""

    def test_config_dataclass_fields(self):
        """Should verify all config dataclass fields exist."""
        from src.iac_agents.config.settings import WorkflowSettings

        settings = WorkflowSettings()
        assert hasattr(settings, "max_workflow_stages")
        assert hasattr(settings, "stage_timeout")
        assert hasattr(settings, "max_template_regeneration_attempts")
