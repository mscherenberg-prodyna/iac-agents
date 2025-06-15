"""Main Terraform Agent for generating Infrastructure as Code templates."""

import os
from typing import Dict, List, Any
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv
from .research_agent import TerraformResearchAgent
from ..config.settings import config
from ..templates.template_manager import template_manager

load_dotenv()


class TerraformAgent:
    """AI Agent for generating Terraform templates from natural language requirements."""
    
    def __init__(self, name: str = "Terraform Generator"):
        self.name = name
        self.llm = self._initialize_llm()
        self.research_agent = TerraformResearchAgent()
        self.conversation_history: List[Dict[str, str]] = []
    
    def _initialize_llm(self):
        """Initialize LLM with Azure OpenAI if configured, otherwise OpenAI."""
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        
        if azure_endpoint and azure_key and azure_deployment:
            return AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_key,
                azure_deployment=azure_deployment,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                temperature=config.agents.terraform_agent_temperature
            )
        else:
            return ChatOpenAI(model="gpt-4", temperature=config.agents.terraform_agent_temperature)
        
    def generate_response(self, user_input: str) -> str:
        """Generate a response to user infrastructure requirements."""
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Analyze the request to determine if research is needed
        if self._needs_research(user_input):
            research_context = self.research_agent.research_terraform_docs(user_input)
        else:
            research_context = ""
            
        # Generate Terraform template
        terraform_template = self._generate_terraform_template(user_input, research_context)
        
        # Validate the template
        validation_result = self._validate_template(terraform_template)
        
        # Create response with template and validation
        response = self._format_response(terraform_template, validation_result)
        
        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def _needs_research(self, user_input: str) -> bool:
        """Determine if the request requires Terraform documentation research."""
        research_keywords = [
            "latest", "new", "current", "updated", "recent",
            "documentation", "docs", "how to", "best practice"
        ]
        return any(keyword in user_input.lower() for keyword in research_keywords)
    
    def _generate_terraform_template(self, requirements: str, research_context: str = "") -> str:
        """Generate Terraform template based on requirements and optional research context."""
        system_prompt = template_manager.get_prompt("terraform_system")

        if research_context:
            system_prompt += f"\n\nAdditional context from Terraform documentation:\n{research_context}"
            
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Generate a Terraform template for: {requirements}")
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def _validate_template(self, template: str) -> Dict[str, Any]:
        """Validate the generated Terraform template."""
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "security_notes": []
        }
        
        # Basic syntax validation
        if not template.strip():
            validation_result["is_valid"] = False
            validation_result["errors"].append("Empty template generated")
            return validation_result
            
        # Check for required elements
        required_elements = ["provider", "resource"]
        for element in required_elements:
            if element not in template.lower():
                validation_result["warnings"].append(f"Missing {element} configuration")
        
        # Security checks
        if "password" in template.lower() and "var." not in template.lower():
            validation_result["security_notes"].append("Consider using variables for sensitive data")
            
        if "admin" in template.lower():
            validation_result["security_notes"].append("Review admin access configurations")
            
        return validation_result
    
    def _format_response(self, template: str, validation: Dict[str, Any]) -> str:
        """Format the response with template and validation information."""
        response = f"## Generated Terraform Template\n\n```hcl\n{template}\n```\n\n"
        
        response += "## Validation Results\n\n"
        
        if validation["is_valid"]:
            response += "✅ **Template validation passed**\n\n"
        else:
            response += "❌ **Template validation failed**\n\n"
            
        if validation["errors"]:
            response += "### Errors:\n"
            for error in validation["errors"]:
                response += f"- {error}\n"
            response += "\n"
            
        if validation["warnings"]:
            response += "### Warnings:\n"
            for warning in validation["warnings"]:
                response += f"- {warning}\n"
            response += "\n"
            
        if validation["security_notes"]:
            response += "### Security Notes:\n"
            for note in validation["security_notes"]:
                response += f"- {note}\n"
            response += "\n"
            
        response += "## Next Steps\n\n"
        response += "⚠️ **HUMAN APPROVAL REQUIRED** ⚠️\n\n"
        response += "1. Review the generated template carefully\n"
        response += "2. Verify all resource configurations meet your requirements\n"
        response += "3. Check security settings and access permissions\n"
        response += "4. Test in a development environment first\n"
        response += "5. Only proceed to deployment after thorough review\n"
        
        return response
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self.conversation_history.copy()
    
    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history.clear()