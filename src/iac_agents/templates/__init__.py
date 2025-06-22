"""Templates module for IAC Agents."""

from .template_loader import TemplateLoader, template_loader
from .template_manager import TemplateManager, template_manager
from .ui_loader import UIStyleLoader, ui_loader

__all__ = [
    "template_manager",
    "TemplateManager",
    "template_loader",
    "TemplateLoader",
    "ui_loader",
    "UIStyleLoader",
]
