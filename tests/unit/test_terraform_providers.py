"""Tests for parse_terraform_providers function."""

from pathlib import Path

import pytest

from iac_agents.agents.terraform_utils import parse_terraform_providers


class TestParseTerraformProviders:
    """Test suite for parse_terraform_providers function."""

    def test_successful_provider_parsing(self):
        """Test successful provider parsing from init output."""
        test_data_path = Path(__file__).parent.parent / "test_data"
        with open(test_data_path / "terraform_init_output.txt", "r") as f:
            stdout_content = f.read()

        init_result = {
            "success": True,
            "stdout": stdout_content,
            "stderr": "",
            "returncode": 0,
        }

        providers = parse_terraform_providers(init_result)

        assert providers["aws"] == "5.31.0"
        assert providers["random"] == "3.6.0"
        assert providers["null"] == "3.2.1"
        assert providers["local"] == "2.4.0"

    def test_failed_init_result(self):
        """Test parsing when init failed."""
        init_result = {
            "success": False,
            "stdout": "",
            "stderr": "Error occurred",
            "returncode": 1,
        }

        providers = parse_terraform_providers(init_result)

        assert providers == {}

    def test_no_providers_found(self):
        """Test parsing when no providers are found."""
        init_result = {
            "success": True,
            "stdout": "No providers found in output",
            "stderr": "",
            "returncode": 0,
        }

        providers = parse_terraform_providers(init_result)

        assert providers == {}

    def test_various_provider_patterns(self):
        """Test different provider output patterns."""
        init_result = {
            "success": True,
            "stdout": "- Installing registry.terraform.io/hashicorp/aws v5.31.0...\n"
            "- Using previously-installed local/custom v1.0.0...\n"
            "- Downloading custom v2.0.0-beta1...",
            "stderr": "",
            "returncode": 0,
        }

        providers = parse_terraform_providers(init_result)

        assert providers["aws"] == "5.31.0"
        assert providers["custom"] == "2.0.0-beta1"

    def test_empty_stdout_handling(self):
        """Test parsing with empty stdout."""
        init_result = {"success": True, "stdout": "", "stderr": "", "returncode": 0}

        providers = parse_terraform_providers(init_result)

        assert providers == {}

    def test_missing_stdout_key(self):
        """Test parsing when stdout key is missing."""
        init_result = {"success": True, "stderr": "", "returncode": 0}

        providers = parse_terraform_providers(init_result)

        assert providers == {}
