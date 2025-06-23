#!/usr/bin/env python3
"""Test script for Infrastructure as Prompts Agent workflow."""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from iac_agents.agents.graph import InfrastructureAsPromptsAgent


def test_basic_workflow():
    """Test basic workflow functionality."""
    print("🔧 Testing Infrastructure as Prompts Agent...")
    
    try:
        # Initialize the agent
        agent = InfrastructureAsPromptsAgent()
        print("✅ Agent initialized successfully")
        
        # Build the compiled agent
        compiled_agent = agent.build()
        print("✅ Agent compiled successfully")
        
        # Test with a simple request
        test_request = "Deploy a simple web application with Azure App Service"
        print(f"\n🚀 Testing with request: {test_request}")
        
        # Create initial state for LangGraph
        initial_state = {
            "user_input": test_request,
            "compliance_settings": {},
            "current_stage": None,
            "completed_stages": [],
            "workflow_plan": None,
            "requirements_analysis_result": None,
            "research_data_result": None,
            "template_generation_result": None,
            "compliance_validation_result": None,
            "cost_estimation_result": None,
            "approval_preparation_result": None,
            "quality_gate_passed": False,
            "compliance_score": 0.0,
            "violations_found": [],
            "final_template": None,
            "final_response": None,
            "errors": [],
            "warnings": [],
            "requires_approval": True,
            "approval_request_id": None,
            "human_feedback": None,
            "current_agent": "cloud_architect",
            "workflow_phase": "planning",
            "needs_terraform_lookup": False,
            "needs_pricing_lookup": False,
            "approval_received": False,
            "cloud_architect_analysis": None,
        }
        
        config = {"configurable": {"thread_id": f"test_{hash(test_request)}"}}
        result = compiled_agent.invoke(initial_state, config)
        
        print(f"✅ Workflow completed")
        print(f"📊 Result keys: {list(result.keys())}")
        
        if result.get("errors"):
            print(f"⚠️  Errors found: {result['errors']}")
        
        if result.get("final_template"):
            print("✅ Template generated")
        else:
            print("ℹ️  No template generated")
            
        if result.get("cloud_architect_analysis"):
            print("✅ Cloud Architect analysis generated")
            print(f"Analysis: {result['cloud_architect_analysis'][:200]}...")
        else:
            print("ℹ️  No Cloud Architect analysis")
            
        # Print workflow info
        print(f"Current agent: {result.get('current_agent')}")
        print(f"Workflow phase: {result.get('workflow_phase')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_basic_workflow()
    sys.exit(0 if success else 1)