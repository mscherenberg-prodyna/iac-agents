"""Showcase scenario loader."""

from typing import Any, Dict, List, Optional

from .template_loader import template_loader


class ScenarioLoader:
    """Load and manage showcase scenarios."""

    def __init__(self):
        self._loader = template_loader
        self._scenarios = None

    def _load_scenarios(self) -> Dict[str, Any]:
        """Load scenarios from JSON file."""
        if self._scenarios is None:
            self._scenarios = self._loader.load_showcase_scenarios()
        return self._scenarios

    def get_all_scenarios(self) -> Dict[str, Any]:
        """Get all showcase scenarios."""
        return self._load_scenarios()

    def get_scenario_by_key(self, scenario_key: str) -> Optional[Dict[str, Any]]:
        """Get a specific scenario by its key."""
        scenarios = self._load_scenarios()
        return scenarios.get(scenario_key)

    def get_scenario_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Get scenario by title for demo purposes."""
        scenarios = self._load_scenarios()

        for scenario in scenarios.values():
            if title.lower() in scenario["title"].lower():
                return scenario
        return None

    def get_all_scenario_titles(self) -> List[str]:
        """Get list of all scenario titles for UI selection."""
        scenarios = self._load_scenarios()
        return [scenario["title"] for scenario in scenarios.values()]

    def get_scenario_keys(self) -> List[str]:
        """Get list of all scenario keys."""
        scenarios = self._load_scenarios()
        return list(scenarios.keys())

    def reload_scenarios(self):
        """Reload scenarios from file."""
        self._scenarios = None


# Global scenario loader instance
scenario_loader = ScenarioLoader()
