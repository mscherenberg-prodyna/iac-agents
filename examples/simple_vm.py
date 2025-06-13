"""Example usage of the Terraform AI agent - Simple Azure VM deployment."""

from src.iac_agents.agents import TerraformAgent
from src.iac_agents.approval_workflow import TerraformApprovalWorkflow


def main():
    """Demonstrate simple VM deployment workflow."""
    print("🤖 Terraform AI Agent - Simple VM Example")
    print("=" * 50)
    
    # Initialize the agent and approval workflow
    agent = TerraformAgent("Terraform Generator")
    approval_workflow = TerraformApprovalWorkflow()
    
    # Example infrastructure request
    user_request = """
    I need a simple Azure virtual machine for development work:
    - Ubuntu 20.04 LTS
    - Standard_B2s size (2 vCPUs, 4GB RAM)
    - SSH key authentication (no passwords)
    - Located in East US region
    - Include a basic network security group
    - Add storage for development tools
    """
    
    print(f"👤 User Request:\n{user_request}\n")
    
    # Generate Terraform template
    print("🔄 Generating Terraform template...")
    response = agent.generate_response(user_request)
    print(f"🤖 Agent Response:\n{response}\n")
    
    # Extract template from response (simplified)
    if "```hcl" in response:
        template_start = response.find("```hcl") + 6
        template_end = response.find("```", template_start)
        template = response[template_start:template_end].strip()
        
        if template:
            print("📋 Creating approval request...")
            
            # Create approval request
            validation_result = agent._validate_template(template)
            approval_request = approval_workflow.create_approval_request(
                template=template,
                requirements=user_request,
                validation_result=validation_result,
                estimated_cost="Estimated: $30-50/month for Standard_B2s VM"
            )
            
            # Display approval summary
            print("📝 Approval Request Summary:")
            print("=" * 50)
            approval_summary = approval_workflow.get_approval_summary(approval_request.id)
            print(approval_summary)
            
            # Simulate approval workflow
            print("\n🔄 Simulating approval workflow...")
            
            # Example: Auto-approve for demo (in real usage, human would review)
            approval_response = f"APPROVE {approval_request.id} Looks good for development environment"
            result = approval_workflow.process_approval_response(approval_response, reviewer="demo-user")
            
            print("✅ Approval Result:")
            print(result)
    
    else:
        print("❌ No Terraform template found in response")


if __name__ == "__main__":
    main()