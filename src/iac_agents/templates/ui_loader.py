"""UI template and style loader."""

from .template_loader import template_loader


class UIStyleLoader:
    """Load UI styles and templates."""

    def __init__(self):
        self._loader = template_loader

    def get_main_css(self) -> str:
        """Get the main CSS styles wrapped in HTML style tags."""
        css_content = self._loader.load_css_file("main_styles")
        return f"<style>\n{css_content}\n</style>"

    def get_activity_entry_template(self) -> str:
        """Get the activity entry HTML template."""
        return self._loader.load_html_template("activity_entry")

    def format_activity_entry(
        self, timestamp: str, agent_name: str, activity_message: str
    ) -> str:
        """Format an activity log entry."""
        template = self.get_activity_entry_template()
        return template.format(
            timestamp=timestamp,
            agent_name=agent_name,
            activity_message=activity_message,
        )


# Global UI style loader instance
ui_loader = UIStyleLoader()
