"""Run example scenarios for the Terraform AI agent."""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from examples.simple_vm import main as simple_vm_example
from examples.web_app_stack import main as web_app_example


def main():
    """Run example scenarios."""
    print("🚀 Terraform AI Agent Examples")
    print("=" * 40)
    print("1. Simple VM Deployment")
    print("2. Web Application Stack")
    print("3. Both Examples")
    print("0. Exit")
    
    choice = input("\nSelect example to run (0-3): ").strip()
    
    if choice == "1":
        simple_vm_example()
    elif choice == "2":
        web_app_example()
    elif choice == "3":
        print("\n🔄 Running Simple VM Example:")
        simple_vm_example()
        print("\n" + "="*60 + "\n")
        print("🔄 Running Web App Stack Example:")
        web_app_example()
    elif choice == "0":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()