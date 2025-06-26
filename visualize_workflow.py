#!/usr/bin/env python3
"""Visualize the Infrastructure as Prompts Agent LangGraph workflow."""

import sys
from pathlib import Path

from iac_agents.agents.graph import InfrastructureAsPromptsAgent

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def visualize_workflow():
    """Generate and display the LangGraph workflow visualization."""
    print("🎨 Generating Infrastructure as Prompts Agent Workflow Visualization")
    print("=" * 70)

    # Initialize the agent
    agent = InfrastructureAsPromptsAgent()
    compiled_graph = agent.build()

    print("✅ Agent graph compiled successfully")

    # Generate visualization
    print("🔄 Generating workflow diagram...")

    # Try to get the graph visualization
    try:
        # Method 1: Try using get_graph().draw_mermaid() if available
        if hasattr(compiled_graph, "get_graph"):
            graph = compiled_graph.get_graph()
            if hasattr(graph, "draw_mermaid"):
                mermaid_diagram = graph.draw_mermaid()
                print("✅ Mermaid diagram generated")

                # Save to file
                output_file = Path("workflow_diagram.mmd")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(mermaid_diagram)

                print(f"📄 Mermaid diagram saved to: {output_file}")
                print("\n🌐 To view the diagram:")
                print("   1. Copy the content of workflow_diagram.mmd")
                print("   2. Paste it into https://mermaid.live/")
                print("   3. Or use a Mermaid-compatible viewer")

                return True
    except Exception as e:
        print(f"⚠️  Mermaid generation failed: {e}")
        return False
    return False


if __name__ == "__main__":
    print("Infrastructure as Prompts Agent - Workflow Visualizer")
    print("=" * 60)

    # Generate visual diagrams
    SUCCESS = visualize_workflow()

    print("=" * 60)
    if SUCCESS:
        print("🎉 Workflow visualization completed successfully!")
    else:
        print(
            "⚠️  Visual diagram generation had issues, but text representation is available"
        )

    sys.exit(0 if SUCCESS else 1)
