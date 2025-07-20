"""Simple script to push changes to a git repository using a GitHub agent."""

from iac_agents.agents.nodes.github_agent import github_agent
from iac_agents.agents.state import InfrastructureStateDict


def main():
    """Main function to run the GitHub agent."""
    state = InfrastructureStateDict(
        conversation_history=[
            "USER: Push the main branch to the GitHub repository. Do not make any changes to the repository, just push the current state.",
        ]
    )
    state = github_agent(state)

    return state.get("conversation_history", ["No response from agent"])[-1]


if __name__ == "__main__":
    result = main()
    print(f"GitHub Agent Response: {result}")
