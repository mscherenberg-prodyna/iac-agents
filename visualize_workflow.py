#!/usr/bin/env python3
"""Visualize the Infrastructure as Prompts Agent LangGraph workflow."""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from iac_agents.agents.graph import InfrastructureAsPromptsAgent


def visualize_workflow():
    """Generate and display the LangGraph workflow visualization."""
    print("🎨 Generating Infrastructure as Prompts Agent Workflow Visualization")
    print("=" * 70)
    
    try:
        # Initialize the agent
        agent = InfrastructureAsPromptsAgent()
        compiled_graph = agent.build()
        
        print("✅ Agent graph compiled successfully")
        
        # Generate visualization
        print("🔄 Generating workflow diagram...")
        
        # Try to get the graph visualization
        try:
            # Method 1: Try using get_graph().draw_mermaid() if available
            if hasattr(compiled_graph, 'get_graph'):
                graph = compiled_graph.get_graph()
                if hasattr(graph, 'draw_mermaid'):
                    mermaid_diagram = graph.draw_mermaid()
                    print("✅ Mermaid diagram generated")
                    
                    # Save to file
                    output_file = Path("workflow_diagram.mmd")
                    with open(output_file, "w") as f:
                        f.write(mermaid_diagram)
                    
                    print(f"📄 Mermaid diagram saved to: {output_file}")
                    print("\n🌐 To view the diagram:")
                    print("   1. Copy the content of workflow_diagram.mmd")
                    print("   2. Paste it into https://mermaid.live/")
                    print("   3. Or use a Mermaid-compatible viewer")
                    
                    return True
        except Exception as e:
            print(f"⚠️  Mermaid generation failed: {e}")
        
        # Method 2: Try using Graphviz if available
        try:
            from graphviz import Digraph
            
            print("🔄 Generating Graphviz diagram...")
            
            # Create a manual visualization of the workflow
            dot = Digraph(comment='Infrastructure as Prompts Agent Workflow')
            dot.attr(rankdir='TB', size='12,8')
            dot.attr('node', shape='box', style='filled', fillcolor='lightblue')
            
            # Add nodes
            nodes = [
                ('start', 'START', 'lightgreen'),
                ('cloud_architect', 'Cloud Architect\\n(Orchestrates workflow)', 'lightblue'),
                ('cloud_engineer', 'Cloud Engineer\\n(Generates templates)', 'lightcoral'),
                ('terraform_consultant', 'Terraform Consultant\\n(Azure AI guidance)', 'lightyellow'),
                ('secops_finops', 'SecOps/FinOps\\n(Compliance & Cost)', 'lightpink'),
                ('human_approval', 'Human Approval\\n(Review & approve)', 'lightgray'),
                ('devops', 'DevOps\\n(Azure deployment)', 'lightgreen'),
                ('end', 'END', 'lightgray')
            ]
            
            for node_id, label, color in nodes:
                dot.node(node_id, label, fillcolor=color)
            
            # Add edges with labels
            edges = [
                ('start', 'cloud_architect', 'Entry Point'),
                ('cloud_architect', 'cloud_engineer', 'Planning Phase'),
                ('cloud_engineer', 'terraform_consultant', 'If consultation needed'),
                ('terraform_consultant', 'cloud_engineer', 'Guidance provided'),
                ('cloud_architect', 'secops_finops', 'Validation Phase'),
                ('secops_finops', 'terraform_consultant', 'If pricing lookup needed'),
                ('terraform_consultant', 'secops_finops', 'Pricing data'),
                ('cloud_architect', 'human_approval', 'If approval required'),
                ('human_approval', 'devops', 'If approved'),
                ('devops', 'cloud_architect', 'Deployment feedback'),
                ('cloud_architect', 'end', 'Workflow complete'),
                ('secops_finops', 'cloud_architect', 'Back to orchestrator'),
                ('cloud_engineer', 'cloud_architect', 'Back to orchestrator'),
            ]
            
            for src, dst, label in edges:
                dot.edge(src, dst, label=label, fontsize='10')
            
            # Save as SVG and PDF
            output_base = "workflow_diagram"
            
            try:
                dot.render(output_base, format='svg', cleanup=True)
                print(f"✅ SVG diagram saved to: {output_base}.svg")
            except Exception as e:
                print(f"⚠️  SVG generation failed: {e}")
            
            try:
                dot.render(output_base, format='png', cleanup=True)
                print(f"✅ PNG diagram saved to: {output_base}.png")
            except Exception as e:
                print(f"⚠️  PNG generation failed: {e}")
            
            # Also save the DOT source
            with open(f"{output_base}.dot", "w") as f:
                f.write(dot.source)
            print(f"✅ DOT source saved to: {output_base}.dot")
            
            print("\n🖼️  Visualization files created!")
            print("📁 Check the current directory for:")
            print("   • workflow_diagram.svg (vector graphic)")
            print("   • workflow_diagram.png (image)")
            print("   • workflow_diagram.dot (Graphviz source)")
            
            return True
            
        except ImportError:
            print("❌ Graphviz Python package not available")
            return False
        except Exception as e:
            print(f"❌ Graphviz visualization failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Workflow visualization failed: {e}")
        return False


def print_workflow_text():
    """Print a text-based representation of the workflow."""
    print("\n📋 Text-Based Workflow Representation")
    print("=" * 50)
    
    workflow_text = """
┌─────────────────────────────────────────────────────────────────┐
│                   Infrastructure as Prompts Agent               │
│                        LangGraph Workflow                       │
└─────────────────────────────────────────────────────────────────┘

                           ┌─────────────┐
                           │    START    │
                           └──────┬──────┘
                                  │
                           ┌──────▼──────┐
                           │    Cloud    │◄──────────────┐
                           │  Architect  │               │
                           │(Orchestrator)│               │
                           └──┬─────┬────┘               │
                              │     │                    │
                    ┌─────────▼─┐   │                    │
                    │   Cloud   │   │                    │
                    │ Engineer  │   │                    │
                    └─────┬─────┘   │                    │
                          │         │                    │
                  ┌───────▼───────┐ │                    │
                  │   Terraform   │ │                    │
                  │  Consultant   │ │                    │
                  │ (Azure AI)    │ │                    │
                  └───────────────┘ │                    │
                                    │                    │
                              ┌─────▼─────┐              │
                              │ SecOps/   │              │
                              │ FinOps    │──────────────┘
                              └─────┬─────┘
                                    │
                              ┌─────▼─────┐
                              │   Human   │
                              │ Approval  │
                              └─────┬─────┘
                                    │
                              ┌─────▼─────┐
                              │  DevOps   │
                              │(Deployment)│
                              └─────┬─────┘
                                    │
                              ┌─────▼─────┐
                              │    END    │
                              └───────────┘

Key Features:
• Multi-agent collaboration with LangGraph
• Azure OpenAI integration for all agents
• Azure AI Foundry for Terraform guidance
• Structured output for deterministic routing
• Real Azure infrastructure deployment
• Compliance validation (PCI DSS, HIPAA, etc.)
• Cost estimation and optimization
"""
    
    print(workflow_text)


if __name__ == "__main__":
    print("Infrastructure as Prompts Agent - Workflow Visualizer")
    print("=" * 60)
    
    # Generate visual diagrams
    success = visualize_workflow()
    
    # Always show text representation
    print_workflow_text()
    
    print("=" * 60)
    if success:
        print("🎉 Workflow visualization completed successfully!")
    else:
        print("⚠️  Visual diagram generation had issues, but text representation is available")
    
    sys.exit(0 if success else 1)