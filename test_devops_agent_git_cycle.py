#!/usr/bin/env python3
"""
Test script for DevOps agent commit and push cycle using the actual agentic implementation.
Simulates the workflow from the devops.py agent for thread ID 140575737112256.
"""

import asyncio
import json
import os
from pathlib import Path

from src.iac_agents.agents.git_utils import get_git_tools, git_tool_executor
from src.iac_agents.agents.mcp_utils import MultiMCPClient
from src.iac_agents.agents.react_agent import agent_react_step
from src.iac_agents.agents.utils import get_github_token, load_agent_response_schema
from src.iac_agents.templates import template_manager


async def test_devops_agent_git_cycle():
    """Test the DevOps agent git cycle using the actual agentic implementation."""
    
    # Test configuration - matching the logs you provided
    thread_id = "140575737112256"
    repo_name = f"iap_deployment_{thread_id}"
    repo_url = f"https://github.com/mscherenberg-prodyna/{repo_name}.git"
    
    # Use the actual deployment directory structure
    deployment_dir = Path("/home/mscherenberg/iac-agents/terraform_deployments") / f"deployment_{thread_id}"
    
    print(f"🤖 Testing DevOps Agent Git Cycle (Agentic Implementation)")
    print(f"📁 Working directory: {deployment_dir}")
    print(f"🔗 Repository URL: {repo_url}")
    print()
    
    # Ensure the directory exists with terraform content
    deployment_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a test main.tf file similar to what would be deployed
    main_tf_path = deployment_dir / "main.tf"
    if not main_tf_path.exists():
        terraform_content = """# Terraform deployment for secure business report storage and automated email notification
terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = "rg-iap-demo"
  location = "East US"
  
  tags = {
    Environment = "Demo"
    Purpose     = "IAP Deployment"
  }
}

resource "azurerm_storage_account" "reports" {
  name                     = "storageacct${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                = azurerm_resource_group.main.location
  account_tier            = "Standard"
  account_replication_type = "LRS"
  
  tags = azurerm_resource_group.main.tags
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}
"""
        with open(main_tf_path, "w") as f:
            f.write(terraform_content)
        print("📝 Created test main.tf file with infrastructure content")
    
    # Get GitHub token
    github_token = get_github_token()
    if not github_token:
        print("⚠️  Warning: GITHUB_TOKEN not set, using placeholder")
        github_token = "placeholder_token"
    
    # Set up MCP client like in devops.py
    mcp_client = MultiMCPClient()
    mcp_client.add_server(
        "github",
        [
            "run",
            "-i", 
            "--rm",
            "-v",
            f"{os.getcwd()}:/workspace",
            "-w",
            "/workspace",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server",
        ],
        {"GITHUB_PERSONAL_ACCESS_TOKEN": github_token},
    )
    mcp_client.add_custom_tools("git_cli", get_git_tools(), git_tool_executor)
    
    print("🔧 MCP client configured with GitHub and Git tools")
    print()
    
    try:
        # Get tools description within session context (like devops.py does)
        async with mcp_client.session() as session:
            tools_list = await mcp_client.list_tools(session)
        
        # Format tools for consistency
        tools_description = "\\n".join(
            [f"- {tool['name']}: {tool['description']}" for tool in tools_list]
        )
        
        # Load response schema
        schema = load_agent_response_schema()
        
        # Get system prompt using template manager (like devops.py)
        system_prompt = template_manager.get_prompt(
            "devops",
            tools_description=tools_description,
            working_dir=str(deployment_dir),
            response_schema=json.dumps(schema, indent=2),
        )
        
        print("📋 System prompt loaded from template")
        
        # Create conversation history simulating successful deployment
        conversation_history = [
            "Cloud Architect: Infrastructure deployment request for secure business report storage",
            "DevOps Engineer: Infrastructure has been deployed successfully. Now proceeding with Git repository setup."
        ]
        
        # Simulate the git workflow instructions that would come after successful deployment
        git_workflow_instruction = f"""
The infrastructure has been deployed successfully. Please:

1. Create a GitHub repository named '{repo_name}'
2. Initialize the deployment directory as a git repository: {deployment_dir}
3. Set up local git configuration (user.name and user.email)
4. Add all files and commit with message: "Initial commit for deployment {thread_id}"
5. Add the remote origin: {repo_url}
6. Push to the GitHub repository with upstream tracking

The deployment is ready for version control.
"""
        
        conversation_history.append(f"System: {git_workflow_instruction}")
        
        print("🎯 Running DevOps agent ReAct workflow...")
        print("=" * 60)
        
        # Run the actual ReAct workflow (like devops.py does)
        response, _ = await agent_react_step(
            mcp_client,
            system_prompt,
            conversation_history,
            "devops",
            schema,
        )
        
        print("=" * 60)
        print("✅ DevOps Agent Response:")
        print(response)
        print("=" * 60)
        
        # Check final state
        print("\\n📊 Final Repository State:")
        
        # Check if git repo was initialized
        git_dir = deployment_dir / ".git"
        if git_dir.exists():
            print("   ✅ Git repository initialized")
        else:
            print("   ❌ Git repository not found")
        
        # Check if files were added
        if main_tf_path.exists():
            print("   ✅ Terraform files present")
        else:
            print("   ❌ Terraform files missing")
        
        # Try to get git status
        try:
            result = git_tool_executor('git_cli_git_status', {'directory': str(deployment_dir)})
            print(f"   📄 Git Status: {result[:100]}...")
        except Exception as e:
            print(f"   ⚠️  Could not get git status: {e}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error during agent workflow: {e}")
        raise
    finally:
        print("\\n🔄 Cleaning up MCP client...")


def run_test():
    """Synchronous wrapper for the async test."""
    return asyncio.run(test_devops_agent_git_cycle())


if __name__ == "__main__":
    print("🚀 Starting DevOps Agent Git Cycle Test")
    print("=" * 60)
    
    try:
        response = run_test()
        print("\\n🎉 Test completed successfully!")
    except Exception as e:
        print(f"\\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
