#!/usr/bin/env python3
"""Test script for the complete Infrastructure as Prompts Agent workflow."""

import os
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from iac_agents.agents.graph import InfrastructureAsPromptsAgent


def test_workflow():
    """Test the complete workflow with a sample infrastructure request."""
    print("🚀 Testing Infrastructure as Prompts Agent Workflow")
    print("=" * 60)
    
    # Initialize the agent
    try:
        agent = InfrastructureAsPromptsAgent()
        compiled_graph = agent.build()
        print("✅ Agent initialized and graph compiled successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return False
    
    # Test input
    test_request = """
    I need to deploy a web application on Azure with the following requirements:
    - High availability with load balancing
    - PostgreSQL database with backup
    - Redis cache for session management
    - Must comply with PCI DSS standards
    - Budget limit: $500/month
    - Deploy in East US region
    """
    
    initial_state = {
        "user_input": test_request,
        "workflow_phase": "planning",
        "compliance_settings": {
            "required_frameworks": ["PCI DSS"],
            "budget_limit": 500,
            "region": "East US"
        },
        "requires_approval": True,
        "current_stage": "planning",
        "completed_stages": [],
        "errors": []
    }
    
    print(f"📝 Test Request: {test_request.strip()}")
    print("=" * 60)
    
    try:
        # Run the workflow
        print("🔄 Starting workflow execution...")
        config = {"configurable": {"thread_id": "test-workflow-1"}, "recursion_limit": 50}
        result = compiled_graph.invoke(initial_state, config=config)
        
        print("✅ Workflow completed successfully!")
        print("=" * 60)
        
        # Display results
        print("📊 WORKFLOW RESULTS:")
        print(f"Final Agent: {result.get('current_agent', 'unknown')}")
        print(f"Workflow Phase: {result.get('workflow_phase', 'unknown')}")
        print(f"Deployment Status: {result.get('deployment_status', 'unknown')}")
        
        if result.get("errors"):
            print(f"⚠️  Errors encountered: {len(result['errors'])}")
            for i, error in enumerate(result["errors"][:3], 1):  # Show first 3 errors
                print(f"   {i}. {error}")
        
        if result.get("cloud_architect_analysis"):
            print("🏗️  Cloud Architect Analysis: Available")
        
        if result.get("cloud_engineer_response"):
            print("🔧 Cloud Engineer Response: Available")
            print(f"   Content length: {len(str(result.get('cloud_engineer_response', '')))}")
            if result.get("needs_terraform_lookup"):
                print("   ⚠️  Terraform lookup was required")
        
        if result.get("final_template"):
            print("📋 Infrastructure Template: Generated")
        
        if result.get("secops_finops_analysis"):
            print("🔒 Security & Cost Analysis: Completed")
        
        if result.get("devops_response"):
            deployment_status = result.get("deployment_status", "unknown")
            if deployment_status == "deployed":
                print("🚀 Infrastructure Deployed: Successfully to Azure")
                if result.get("terraform_workspace"):
                    print(f"   Terraform workspace: {result['terraform_workspace']}")
            elif deployment_status == "planned":
                print("🚀 Deployment Plan: Ready")
            else:
                print(f"🚀 Deployment Status: {deployment_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Infrastructure as Prompts Agent - Complete Workflow Test")
    print("=" * 60)
    
    # Check environment
    print("🔧 Environment Check:")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY") 
    
    if not azure_endpoint or not azure_key:
        print("⚠️  Azure OpenAI credentials not found in environment")
        print("   Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
        print("   The test will continue but LLM calls may fail")
    else:
        print("✅ Azure OpenAI credentials found")
    
    print("=" * 60)
    
    success = test_workflow()
    
    print("=" * 60)
    if success:
        print("🎉 Complete workflow test PASSED")
    else:
        print("💥 Complete workflow test FAILED")
    
    sys.exit(0 if success else 1)