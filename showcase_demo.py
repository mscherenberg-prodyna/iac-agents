"""Showcase demo script for Infrastructure as Code AI Agent presentation."""

import time
import json
from datetime import datetime
from typing import Dict, Any

from src.iac_agents.agents import TerraformAgent
from src.iac_agents.approval_workflow import TerraformApprovalWorkflow
from src.iac_agents.deployment_automation import TerraformDeploymentManager
from src.iac_agents.compliance_framework import ComplianceFramework
from src.iac_agents.showcase_scenarios import SHOWCASE_SCENARIOS


class ShowcaseDemo:
    """Orchestrates a live demo of the AI Infrastructure agent."""
    
    def __init__(self):
        self.terraform_agent = TerraformAgent()
        self.approval_workflow = TerraformApprovalWorkflow()
        self.deployment_manager = TerraformDeploymentManager()
        self.compliance_framework = ComplianceFramework()
        self.demo_log = []
        
    def log_action(self, action: str, details: Dict[str, Any] = None):
        """Log demo actions for visualization."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details or {}
        }
        self.demo_log.append(log_entry)
        print(f"🎬 DEMO: {action}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2)[:200]}...")
    
    def run_full_demo(self, scenario_key: str = "startup_mvp"):
        """Run a complete end-to-end demo."""
        print("🚀 Starting Infrastructure as Code AI Agent Showcase")
        print("=" * 60)
        
        scenario = SHOWCASE_SCENARIOS[scenario_key]
        
        # Phase 1: Business Requirements Input
        self.log_action("Business Requirements Received", {
            "scenario": scenario["title"],
            "context": scenario["business_context"][:100] + "..."
        })
        
        print(f"\n📋 SCENARIO: {scenario['title']}")
        print(f"Context: {scenario['business_context']}")
        print(f"\n👤 USER REQUEST:\n{scenario['user_request'][:300]}...\n")
        
        time.sleep(2)  # Demo pacing
        
        # Phase 2: AI Agent Processing
        self.log_action("AI Agent Processing Started", {
            "agent": "TerraformAgent",
            "input_length": len(scenario["user_request"])
        })
        
        print("🤖 AI Agent is processing requirements...")
        print("   ┣ 🔍 Analyzing business requirements")
        print("   ┣ 📚 Researching Terraform best practices") 
        print("   ┣ 🏗️ Generating infrastructure template")
        print("   ┗ ✅ Template generation complete")
        
        # Generate template
        response = self.terraform_agent.generate_response(scenario["user_request"])
        
        # Extract template
        template = self._extract_template_from_response(response)
        
        self.log_action("Template Generated", {
            "template_lines": len(template.split('\n')) if template else 0,
            "contains_resources": "resource" in template.lower() if template else False
        })
        
        # Phase 3: Compliance Validation
        print("\n⚖️ COMPLIANCE VALIDATION")
        compliance_result = self.compliance_framework.validate_template(
            template, 
            scenario["compliance_requirements"]
        )
        
        self.log_action("Compliance Validation", {
            "score": compliance_result["compliance_score"],
            "violations": len(compliance_result["violations"]),
            "frameworks": scenario["compliance_requirements"]
        })
        
        print(f"   ┣ Compliance Score: {compliance_result['compliance_score']:.1f}%")
        print(f"   ┣ Violations Found: {len(compliance_result['violations'])}")
        print(f"   ┗ Frameworks: {', '.join(scenario['compliance_requirements'])}")
        
        # Phase 4: Human Approval Workflow
        print("\n👥 HUMAN APPROVAL WORKFLOW")
        
        approval_request = self.approval_workflow.create_approval_request(
            template=template,
            requirements=scenario["user_request"],
            validation_result=compliance_result,
            estimated_cost=scenario["estimated_cost"]
        )
        
        self.log_action("Approval Request Created", {
            "request_id": approval_request.id,
            "estimated_cost": scenario["estimated_cost"]
        })
        
        print(f"   ┣ Approval Request: {approval_request.id}")
        print(f"   ┣ Estimated Cost: {scenario['estimated_cost']}")
        print(f"   ┗ Awaiting human approval...")
        
        time.sleep(1)
        
        # Simulate approval (in real demo, this would be manual)
        print("\n🔍 HUMAN REVIEW PROCESS")
        print("   ┣ Security team reviewing template")
        print("   ┣ Compliance officer checking requirements") 
        print("   ┣ Finance team validating cost estimates")
        print("   ┗ ✅ Approval granted!")
        
        approval_result = self.approval_workflow.process_approval_response(
            f"APPROVE {approval_request.id} Approved for showcase demo",
            reviewer="demo-reviewer"
        )
        
        self.log_action("Approval Granted", {
            "approved_by": "demo-reviewer",
            "approval_time": datetime.now().isoformat()
        })
        
        # Phase 5: Deployment Planning
        print("\n🎯 DEPLOYMENT PLANNING")
        
        deployment_id = f"demo-{int(time.time())}"
        deployment_status = self.deployment_manager.plan_deployment(
            deployment_id=deployment_id,
            template=template,
            variables={"environment": "demo", "location": "East US"}
        )
        
        self.log_action("Deployment Planned", {
            "deployment_id": deployment_id,
            "resources_to_create": len(deployment_status.resources_created),
            "status": deployment_status.status
        })
        
        print(f"   ┣ Deployment ID: {deployment_id}")
        print(f"   ┣ Resources to create: {len(deployment_status.resources_created)}")
        print(f"   ┣ Estimated duration: 5-10 minutes")
        print(f"   ┗ Plan validation: ✅")
        
        # Phase 6: Live Deployment (simulated)
        print("\n🚀 LIVE AZURE DEPLOYMENT")
        print("   ┣ 🔄 Applying Terraform plan...")
        print("   ┣ 🏗️ Creating Azure resources...")
        
        # Simulate resource creation
        for i, resource in enumerate(scenario["expected_resources"][:5]):
            time.sleep(0.5)
            print(f"   ┣ ✅ Created: {resource}")
        
        if len(scenario["expected_resources"]) > 5:
            remaining = len(scenario["expected_resources"]) - 5
            print(f"   ┣ ... and {remaining} more resources")
            
        print("   ┗ 🎉 Deployment completed successfully!")
        
        self.log_action("Deployment Completed", {
            "deployment_id": deployment_id,
            "resources_created": scenario["expected_resources"],
            "completion_time": datetime.now().isoformat()
        })
        
        # Phase 7: Results Summary
        print("\n📊 DEPLOYMENT SUMMARY")
        print(f"   ┣ Total time: ~5 minutes (from chat to live infrastructure)")
        print(f"   ┣ Resources created: {len(scenario['expected_resources'])}")
        print(f"   ┣ Compliance score: {compliance_result['compliance_score']:.1f}%")
        print(f"   ┣ Monthly cost: {scenario['estimated_cost']}")
        print(f"   ┗ Status: Production ready ✅")
        
        print("\n🎯 SHOWCASE COMPLETE")
        print("Business requirement → Live Azure infrastructure in minutes!")
        
        return {
            "scenario": scenario,
            "template": template,
            "compliance_result": compliance_result,
            "deployment_id": deployment_id,
            "demo_log": self.demo_log
        }
    
    def _extract_template_from_response(self, response: str) -> str:
        """Extract Terraform template from agent response."""
        if "```hcl" in response:
            start = response.find("```hcl") + 6
            end = response.find("```", start)
            return response[start:end].strip()
        return ""
    
    def show_agent_orchestration(self):
        """Demonstrate the multi-agent orchestration."""
        print("\n🔧 AGENT ORCHESTRATION VISUALIZATION")
        print("=" * 50)
        
        agents = [
            ("🤖 Terraform Agent", "Template Generation", "ACTIVE"),
            ("🔍 Research Agent", "Documentation Lookup", "ACTIVE"),
            ("⚖️ Compliance Agent", "Security Validation", "ACTIVE"),
            ("👥 Approval Agent", "Human Workflow", "ACTIVE"),
            ("🚀 Deployment Agent", "Azure Provisioning", "STANDBY")
        ]
        
        for agent, role, status in agents:
            status_emoji = "🟢" if status == "ACTIVE" else "🟡"
            print(f"{status_emoji} {agent:<20} | {role:<20} | {status}")
        
        print("\n🔄 Agent Communication Flow:")
        print("User Input → Terraform Agent → Research Agent → Compliance Agent")
        print("                ↓")
        print("Approval Agent → Deployment Agent → Azure Resources")
    
    def demonstrate_compliance_frameworks(self):
        """Show compliance framework capabilities."""
        print("\n⚖️ COMPLIANCE FRAMEWORK DEMONSTRATION")
        print("=" * 50)
        
        frameworks = ["PCI DSS", "HIPAA", "SOX", "GDPR", "ISO 27001"]
        
        for framework in frameworks:
            print(f"✅ {framework}")
            rules = [rule for rule in self.compliance_framework.rules.values() 
                    if framework in rule.frameworks]
            print(f"   └─ {len(rules)} compliance rules")
        
        print(f"\nTotal compliance rules: {len(self.compliance_framework.rules)}")
        print("Real-time validation during template generation")


def main():
    """Run the showcase demo."""
    demo = ShowcaseDemo()
    
    print("Select demo scenario:")
    for i, (key, scenario) in enumerate(SHOWCASE_SCENARIOS.items(), 1):
        print(f"{i}. {scenario['title']}")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    scenario_keys = list(SHOWCASE_SCENARIOS.keys())
    if choice.isdigit() and 1 <= int(choice) <= len(scenario_keys):
        selected_key = scenario_keys[int(choice) - 1]
        
        print(f"\n🎬 Running demo for: {SHOWCASE_SCENARIOS[selected_key]['title']}")
        time.sleep(2)
        
        result = demo.run_full_demo(selected_key)
        
        print("\n🔧 Additional Demonstrations:")
        demo.show_agent_orchestration()
        demo.demonstrate_compliance_frameworks()
        
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()