"""Test template generation with the improved system."""

from src.iac_agents.agents.supervisor_agent import SupervisorAgent
from src.iac_agents.logging_system import log_user_update


def test_document_storage_request():
    """Test the specific request that was failing."""
    log_user_update("🧪 Testing document storage request")
    
    supervisor = SupervisorAgent()
    
    # The exact request that was failing
    failing_request = "I have a number of documents that I need to keep for legal reasons. What would be a good way to do this with Azure infrastructure?"
    
    print(f"📝 Processing request: {failing_request}")
    print("🔍 Watch console for enhanced debugging...")
    print()
    
    try:
        response = supervisor.process_user_request(failing_request)
        
        print("\n" + "="*60)
        print("✅ Request processed successfully!")
        print(f"Response length: {len(response)} characters")
        
        # Check if template is in response
        if "```hcl" in response:
            print("✅ HCL template found in response")
            # Extract and show template
            start = response.find("```hcl") + 6
            end = response.find("```", start)
            template = response[start:end].strip()
            print(f"Template length: {len(template)} characters")
            print(f"Template lines: {len(template.split('\n'))}")
        elif "terraform" in response.lower():
            print("⚠️ Response contains 'terraform' but no HCL code block")
        else:
            print("❌ No Terraform content found in response")
        
        # Show partial response
        print("\n📋 Response Preview:")
        print(response[:500] + "..." if len(response) > 500 else response)
            
    except Exception as e:
        print(f"❌ Error processing request: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🔧 Testing Enhanced Template Generation")
    print("=" * 50)
    test_document_storage_request()