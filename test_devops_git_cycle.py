#!/usr/bin/env python3
"""
Test script for DevOps git commit and push cycle.
Simulates the workflow from deployment_140575737112256.
"""

import os
import tempfile
from pathlib import Path

from src.iac_agents.agents.git_utils import git_tool_executor


def test_devops_git_cycle():
    """Test the complete devops git cycle using the actual implementation."""
    
    # Test configuration
    thread_id = "140575737112256"
    repo_name = f"iap_deployment_{thread_id}"
    repo_url = f"https://github.com/mscherenberg-prodyna/{repo_name}.git"
    
    # Use the actual deployment directory structure
    deployment_dir = f"/home/mscherenberg/iac-agents/terraform_deployments/deployment_{thread_id}"
    
    print(f"🧪 Testing DevOps Git Cycle for thread {thread_id}")
    print(f"📁 Working directory: {deployment_dir}")
    print(f"🔗 Repository URL: {repo_url}")
    print()
    
    # Ensure the directory exists with some test content
    os.makedirs(deployment_dir, exist_ok=True)
    
    # Create a test main.tf file if it doesn't exist
    main_tf_path = Path(deployment_dir) / "main.tf"
    if not main_tf_path.exists():
        with open(main_tf_path, "w") as f:
            f.write("""# Test Terraform configuration for deployment
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
  name     = "rg-test-deployment"
  location = "East US"
}
""")
        print(f"📝 Created test main.tf file")
    
    print("=" * 60)
    print("🚀 Starting Git Operations")
    print("=" * 60)
    
    # Step 1: Initialize git repository
    print("\n1️⃣ Initializing git repository...")
    result = git_tool_executor('git_cli_git_init', {'directory': deployment_dir})
    print(f"   Result: {result}")
    
    # Step 2: Get global git config (user.name)
    print("\n2️⃣ Getting global user.name...")
    result = git_tool_executor('git_cli_git_config', {'args': '--global user.name'})
    print(f"   Global user.name: {result}")
    global_name = result if not result.startswith("Error:") else "DevOps Agent"
    
    # Step 3: Get global git config (user.email)
    print("\n3️⃣ Getting global user.email...")
    result = git_tool_executor('git_cli_git_config', {'args': '--global user.email'})
    print(f"   Global user.email: {result}")
    global_email = result if not result.startswith("Error:") else "devops@deployment.local"
    
    # Step 4: Set local user.name
    print(f"\n4️⃣ Setting local user.name to '{global_name}'...")
    result = git_tool_executor('git_cli_git_config', {
        'args': f'--local user.name "{global_name}"',
        'directory': deployment_dir
    })
    print(f"   Result: {result}")
    
    # Step 5: Set local user.email
    print(f"\n5️⃣ Setting local user.email to '{global_email}'...")
    result = git_tool_executor('git_cli_git_config', {
        'args': f'--local user.email "{global_email}"',
        'directory': deployment_dir
    })
    print(f"   Result: {result}")
    
    # Step 6: Add all files
    print("\n6️⃣ Adding all files...")
    result = git_tool_executor('git_cli_git_add', {
        'filepattern': '.',
        'directory': deployment_dir
    })
    print(f"   Result: {result}")
    
    # Step 7: Check status
    print("\n7️⃣ Checking git status...")
    result = git_tool_executor('git_cli_git_status', {'directory': deployment_dir})
    print(f"   Status: {result}")
    
    # Step 8: Commit changes
    print(f"\n8️⃣ Committing changes...")
    commit_message = f"Initial commit for deployment {thread_id}"
    result = git_tool_executor('git_cli_git_commit', {
        'message': commit_message,
        'directory': deployment_dir
    })
    print(f"   Result: {result}")
    
    # Step 9: Add remote origin
    print(f"\n9️⃣ Adding remote origin...")
    result = git_tool_executor('git_cli_git_remote', {
        'args': f'add origin {repo_url}',
        'directory': deployment_dir
    })
    print(f"   Result: {result}")
    
    # Step 10: Push to remote (this will likely fail without proper auth, but we test the command building)
    print(f"\n🔟 Attempting to push to remote...")
    result = git_tool_executor('git_cli_git_push', {
        'repository': 'origin',
        'refspec': 'main',
        'set_upstream': True,
        'directory': deployment_dir
    })
    print(f"   Result: {result}")
    
    print("\n" + "=" * 60)
    print("✅ Git cycle test completed!")
    print("=" * 60)
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   - Thread ID: {thread_id}")
    print(f"   - Repository: {repo_name}")
    print(f"   - Working Directory: {deployment_dir}")
    print(f"   - Remote URL: {repo_url}")
    
    # Show final status
    print(f"\n📋 Final git status:")
    result = git_tool_executor('git_cli_git_status', {'directory': deployment_dir})
    print(f"   {result}")


if __name__ == "__main__":
    test_devops_git_cycle()
