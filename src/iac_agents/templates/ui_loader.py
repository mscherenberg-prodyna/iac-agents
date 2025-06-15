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

    def get_sidebar_section_template(self) -> str:
        """Get the sidebar section HTML template."""
        return self._loader.load_html_template("sidebar_section")

    def get_agent_status_template(self) -> str:
        """Get the agent status HTML template."""
        return self._loader.load_html_template("agent_status")

    def get_activity_entry_template(self) -> str:
        """Get the activity entry HTML template."""
        return self._loader.load_html_template("activity_entry")

    def get_metric_container_template(self) -> str:
        """Get the metric container HTML template."""
        return self._loader.load_html_template("metric_container")

    def format_sidebar_section(self, title: str, content: str) -> str:
        """Format a sidebar section with given title and content."""
        template = self.get_sidebar_section_template()
        return template.format(title=title, content=content)

    def format_agent_status(
        self,
        emoji: str,
        agent_name: str,
        status_class: str,
        status_text: str,
        subtext: str,
    ) -> str:
        """Format an agent status display."""
        template = self.get_agent_status_template()
        return template.format(
            emoji=emoji,
            agent_name=agent_name,
            status_class=status_class,
            status_text=status_text,
            subtext=subtext,
        )

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

    def format_metric_container(self, label: str, value: str) -> str:
        """Format a metric display container."""
        template = self.get_metric_container_template()
        return template.format(label=label, value=value)


# Global UI style loader instance
ui_loader = UIStyleLoader()
