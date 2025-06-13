"""Test script to demonstrate the enhanced agent system with console logging."""

import time
from src.iac_agents.agents.supervisor_agent import SupervisorAgent
from src.iac_agents.logging_system import log_user_update


def test_enhanced_system():
    """Test the enhanced system with console logging."""
    print("🎬 Testing Enhanced Infrastructure as Code AI Agent")
    print("=" * 60)
    print()
    
    log_user_update("Starting enhanced system test")
    
    # Initialize supervisor agent
    supervisor = SupervisorAgent()
    
    # Test simple request
    test_request = """
    I need a simple web application deployment for a startup:
    - React frontend 
    - Node.js backend API
    - PostgreSQL database
    - Basic security and SSL
    - Auto-scaling capability
    - Estimated budget: $200/month
    """
    
    print("🤖 Processing test request...")
    print(f"Request: {test_request.strip()}")
    print()
    
    # Process request (this will show console logging)
    response = supervisor.process_user_request(test_request)
    
    print()
    print("✅ Test completed!")
    print()
    print("📋 Response received:")
    print("=" * 40)
    print(response[:500] + "..." if len(response) > 500 else response)


if __name__ == "__main__":
    test_enhanced_system()