"""GUI for the Infrastructure as Code AI Agent - Modular Interface."""

from iac_agents.streamlit.main_interface import main

# For backward compatibility, we simply delegate to the new main interface
if __name__ == "__main__":
    main()

# Export the main function for external use
__all__ = ["main"]
