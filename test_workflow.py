#!/usr/bin/env python3
"""Test script for Infrastructure as Prompts Agent workflow."""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from iac_agents.agents import InfrastructureAsPromptsAgent
from iac_agents.logging_system import agent_logger


def test_basic_workflow():
    """Test basic workflow functionality."""
    print("🔧 Testing Infrastructure as Prompts Agent with Real-time Logging...")
    
    # Clear previous logs
    agent_logger.clear_logs()
    
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
        
        # Create initial state matching current interface
        initial_state = {
            "user_input": test_request,
            "conversation_history": [],
            "compliance_settings": {
                "enforce_compliance": True,
                "selected_frameworks": ["ISO27001"]
            },
            "requires_approval": False,  # Skip approval for test
            "current_agent": "cloud_architect",
            "workflow_phase": "planning", 
            "completed_stages": [],
            "errors": [],
            "needs_terraform_lookup": False,
            "needs_pricing_lookup": False,
            "approval_received": False,
            "phase_iterations": {},
            "terraform_consultant_caller": None,
        }
        
        config = {"configurable": {"thread_id": f"test_{hash(test_request)}"}}
        result = compiled_agent.invoke(initial_state, config)
        
        print(f"✅ Workflow completed")
        print(f"📊 Result keys: {list(result.keys())}")
        
        if result.get("errors"):
            print(f"⚠️  Errors found: {result['errors']}")
        
        if result.get("cloud_architect_analysis"):
            print("✅ Cloud Architect analysis generated")
            print(f"Analysis: {result['cloud_architect_analysis'][:200]}...")
        else:
            print("ℹ️  No Cloud Architect analysis")
            
        # Print workflow info
        print(f"Current agent: {result.get('current_agent')}")
        print(f"Workflow phase: {result.get('workflow_phase')}")
        
        # Show logging activity
        print("\n📋 Real-time Activity Log:")
        print("-" * 40)
        recent_logs = agent_logger.get_recent_logs(15)
        for log_entry in recent_logs:
            timestamp = log_entry.timestamp.strftime("%H:%M:%S")
            level_emoji = {"AGENT_START": "🚀", "AGENT_COMPLETE": "✅", "INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌"}.get(log_entry.level.value, "•")
            print(f"[{timestamp}] {level_emoji} {log_entry.agent_name}: {log_entry.activity}")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_basic_workflow()
    sys.exit(0 if success else 1)