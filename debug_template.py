"""Debug the template extraction to see what we're getting."""

from src.iac_agents.agents.terraform_agent import TerraformAgent


def test_terraform_agent_directly():
    """Test the Terraform agent directly to see its output."""
    agent = TerraformAgent()
    
    request = "I have a number of documents that I need to keep for legal reasons. What would be a good way to do this with Azure infrastructure?"
    
    print("🔍 Testing Terraform Agent directly...")
    print(f"Request: {request}")
    print()
    
    response = agent.generate_response(request)
    
    print("📋 Full Response:")
    print("=" * 60)
    print(response)
    print("=" * 60)
    
    # Check what gets extracted
    if "```hcl" in response:
        start = response.find("```hcl") + 6
        end = response.find("```", start)
        template = response[start:end].strip()
        
        print(f"\n🔍 Extracted Template ({len(template)} characters):")
        print("-" * 40)
        print(template)
        print("-" * 40)
    else:
        print("❌ No HCL code block found")


if __name__ == "__main__":
    test_terraform_agent_directly()