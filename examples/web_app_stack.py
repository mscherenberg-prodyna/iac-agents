"""Example usage - Complete web application stack deployment."""

from src.iac_agents.agents import TerraformAgent
from src.iac_agents.approval_workflow import TerraformApprovalWorkflow


def main():
    """Demonstrate web application stack deployment."""
    print("🌐 Terraform AI Agent - Web App Stack Example")
    print("=" * 50)
    
    agent = TerraformAgent("Terraform Generator")
    approval_workflow = TerraformApprovalWorkflow()
    
    # Complex infrastructure request
    user_request = """
    I need a complete web application stack on Azure:
    
    Frontend:
    - Azure App Service for React frontend
    - Custom domain support
    - SSL certificate
    
    Backend:
    - Azure App Service for Node.js API
    - Application Insights for monitoring
    
    Database:
    - Azure Database for PostgreSQL
    - Encrypted at rest
    - Automated backups
    
    Security:
    - Application Gateway with WAF
    - Key Vault for secrets management
    - Network security groups
    
    Networking:
    - Virtual Network with proper subnets
    - Service endpoints for database
    
    Please use best practices for production deployment.
    """
    
    print(f"👤 User Request:\n{user_request}\n")
    
    # Generate template with research
    print("🔍 Generating template with documentation research...")
    response = agent.generate_response(user_request)
    print(f"🤖 Agent Response:\n{response}\n")
    
    # Process approval workflow
    if "```hcl" in response:
        template_start = response.find("```hcl") + 6
        template_end = response.find("```", template_start)
        template = response[template_start:template_end].strip()
        
        if template:
            validation_result = agent._validate_template(template)
            approval_request = approval_workflow.create_approval_request(
                template=template,
                requirements=user_request,
                validation_result=validation_result,
                estimated_cost="Estimated: $200-400/month depending on usage"
            )
            
            approval_summary = approval_workflow.get_approval_summary(approval_request.id)
            print("📝 Approval Request:")
            print("=" * 50)
            print(approval_summary)
            
            # Show pending requests
            pending = approval_workflow.get_pending_requests()
            print(f"\n📊 Pending Requests: {len(pending)}")
            
            # Demonstrate rejection workflow
            print("\n🔄 Simulating rejection for security review...")
            rejection_response = f"REJECT {approval_request.id} Requires security team review for production deployment"
            result = approval_workflow.process_approval_response(rejection_response, reviewer="security-team")
            print(result)


if __name__ == "__main__":
    main()