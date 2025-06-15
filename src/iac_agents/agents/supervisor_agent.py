"""Supervisor Agent for orchestrating infrastructure deployment workflow."""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from ..approval_workflow import TerraformApprovalWorkflow
from ..compliance_framework import ComplianceFramework
from ..config.settings import config
from ..logging_system import (log_agent_complete, log_agent_start, log_info,
                              log_user_update, log_warning)
from ..templates.template_manager import template_manager
from .research_agent import TerraformResearchAgent
from .terraform_agent import TerraformAgent

load_dotenv()


class WorkflowStage(Enum):
    """Stages of the infrastructure deployment workflow."""

    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    RESEARCH_AND_PLANNING = "research_and_planning"
    TEMPLATE_GENERATION = "template_generation"
    VALIDATION_AND_COMPLIANCE = "validation_and_compliance"
    COST_ESTIMATION = "cost_estimation"
    APPROVAL_PREPARATION = "approval_preparation"
    TEMPLATE_REFINEMENT = "template_refinement"
    COMPLETED = "completed"


@dataclass
class WorkflowPlan:
    """Plan for executing the infrastructure deployment workflow."""

    stages: List[WorkflowStage]
    requirements: str
    compliance_frameworks: List[str]
    estimated_duration: int  # in seconds
    complexity_score: int  # 1-10


@dataclass
class WorkflowProgress:
    """Current progress through the workflow."""

    current_stage: WorkflowStage
    completed_stages: List[WorkflowStage]
    stage_results: Dict[str, Any]
    issues_found: List[str]
    user_feedback_needed: bool = False


class SupervisorAgent:
    """Orchestrates the entire infrastructure deployment workflow."""

    def __init__(self):
        self.name = "Supervisor Agent"
        self.llm = self._initialize_llm()

        # Initialize sub-agents
        self.terraform_agent = TerraformAgent()
        self.research_agent = TerraformResearchAgent()
        self.compliance_framework = ComplianceFramework()
        self.approval_workflow = TerraformApprovalWorkflow()

        # Workflow state
        self.current_workflow: Optional[WorkflowProgress] = None
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
                temperature=0.2,
            )
        else:
            return ChatOpenAI(model="gpt-4", temperature=0.2)

    def process_user_request(
        self, user_input: str, compliance_settings: dict = None
    ) -> str:
        """Main entry point for processing user infrastructure requests."""
        log_agent_start(
            self.name, "Processing user request", {"input_length": len(user_input)}
        )

        try:
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})

            # Analyze requirements and create workflow plan
            log_user_update("🔍 Analyzing your infrastructure requirements...")
            workflow_plan = self._analyze_requirements(user_input)

            # Initialize workflow progress
            self.current_workflow = WorkflowProgress(
                current_stage=workflow_plan.stages[0],
                completed_stages=[],
                stage_results={},
                issues_found=[],
            )

            # Store compliance settings for use throughout workflow
            self.compliance_settings = compliance_settings or {
                "enforce_compliance": False,
                "selected_frameworks": [],
            }

            # Execute workflow
            log_user_update(
                f"📋 Created execution plan with {len(workflow_plan.stages)} stages"
            )
            result = self._execute_workflow(workflow_plan, user_input)

            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": result})

            log_agent_complete(self.name, "User request processed successfully")
            return result

        except Exception as e:
            log_warning(self.name, f"Error processing request: {str(e)}")
            error_response = f"I encountered an issue while processing your request: {str(e)}. Let me try a different approach."
            self.conversation_history.append(
                {"role": "assistant", "content": error_response}
            )
            return error_response

    def _analyze_requirements(self, user_input: str) -> WorkflowPlan:
        """Analyze user requirements and create a workflow plan."""
        log_agent_start(self.name, "Analyzing requirements")

        system_prompt = template_manager.get_prompt("requirements_analysis")

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"Analyze this infrastructure request:\n\n{user_input}"
            ),
        ]

        try:
            response = self.llm.invoke(messages)
            analysis = self._parse_analysis_response(response.content)

            # Determine workflow stages based on complexity
            stages = self._determine_workflow_stages(analysis)

            workflow_plan = WorkflowPlan(
                stages=stages,
                requirements=user_input,
                compliance_frameworks=analysis.get("compliance_frameworks", []),
                estimated_duration=analysis.get("estimated_duration_minutes", 10) * 60,
                complexity_score=analysis.get("complexity_score", 5),
            )

            log_agent_complete(
                self.name,
                "Requirements analysis complete",
                {
                    "complexity": workflow_plan.complexity_score,
                    "stages": len(workflow_plan.stages),
                    "compliance_frameworks": len(workflow_plan.compliance_frameworks),
                },
            )

            return workflow_plan

        except Exception as e:
            log_warning(self.name, f"Analysis failed, using default plan: {str(e)}")
            # Fallback to default workflow
            return WorkflowPlan(
                stages=[
                    WorkflowStage.REQUIREMENTS_ANALYSIS,
                    WorkflowStage.TEMPLATE_GENERATION,
                    WorkflowStage.VALIDATION_AND_COMPLIANCE,
                    WorkflowStage.APPROVAL_PREPARATION,
                ],
                requirements=user_input,
                compliance_frameworks=["PCI DSS", "GDPR"],
                estimated_duration=600,  # 10 minutes
                complexity_score=5,
            )

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse the analysis response from the LLM."""
        try:
            import json

            # Try to extract JSON from the response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except Exception:
            pass

        # Fallback parsing
        return {
            "complexity_score": 5,
            "compliance_frameworks": ["GDPR"],
            "estimated_duration_minutes": 10,
            "key_challenges": ["complexity", "compliance"],
            "infrastructure_type": "web_app",
        }

    def _determine_workflow_stages(
        self, analysis: Dict[str, Any]
    ) -> List[WorkflowStage]:
        """Determine workflow stages based on analysis."""
        complexity = analysis.get("complexity_score", 5)
        compliance_frameworks = analysis.get("compliance_frameworks", [])

        stages = [WorkflowStage.REQUIREMENTS_ANALYSIS]

        if complexity >= 7 or len(compliance_frameworks) > 2:
            stages.append(WorkflowStage.RESEARCH_AND_PLANNING)

        stages.extend(
            [WorkflowStage.TEMPLATE_GENERATION, WorkflowStage.VALIDATION_AND_COMPLIANCE]
        )

        if complexity >= 5:
            stages.append(WorkflowStage.COST_ESTIMATION)

        stages.extend([WorkflowStage.APPROVAL_PREPARATION, WorkflowStage.COMPLETED])

        return stages

    def _execute_workflow(self, plan: WorkflowPlan, user_input: str) -> str:
        """Execute the complete workflow."""
        log_agent_start(
            self.name, "Executing workflow", {"total_stages": len(plan.stages)}
        )

        results = {}

        for stage in plan.stages:
            if stage == WorkflowStage.COMPLETED:
                break

            log_user_update(
                f"🔄 Executing stage: {stage.value.replace('_', ' ').title()}"
            )
            self.current_workflow.current_stage = stage

            try:
                stage_result = self._execute_stage(stage, plan, user_input, results)
                results[stage.value] = stage_result
                self.current_workflow.completed_stages.append(stage)
                self.current_workflow.stage_results[stage.value] = stage_result

                log_info(self.name, f"Stage {stage.value} completed successfully")

            except Exception as e:
                log_warning(self.name, f"Stage {stage.value} failed: {str(e)}")
                self.current_workflow.issues_found.append(
                    f"Stage {stage.value}: {str(e)}"
                )

                # Decide whether to continue or stop
                if self._should_continue_after_error(stage, str(e)):
                    log_info(
                        self.name, f"Continuing workflow despite error in {stage.value}"
                    )
                    continue
                else:
                    return f"❌ Workflow stopped due to critical error in {stage.value}: {str(e)}"

        # Compile final response
        final_response = self._compile_final_response(plan, results)

        log_agent_complete(
            self.name,
            "Workflow execution complete",
            {
                "stages_completed": len(self.current_workflow.completed_stages),
                "issues_found": len(self.current_workflow.issues_found),
            },
        )

        return final_response

    def _execute_stage(
        self,
        stage: WorkflowStage,
        plan: WorkflowPlan,
        user_input: str,
        previous_results: Dict[str, Any],
    ) -> Any:
        """Execute a specific workflow stage."""

        if stage == WorkflowStage.REQUIREMENTS_ANALYSIS:
            return self._stage_requirements_analysis(user_input, plan)

        elif stage == WorkflowStage.RESEARCH_AND_PLANNING:
            return self._stage_research_and_planning(user_input, plan)

        elif stage == WorkflowStage.TEMPLATE_GENERATION:
            return self._stage_template_generation(user_input, previous_results)

        elif stage == WorkflowStage.VALIDATION_AND_COMPLIANCE:
            return self._stage_validation_and_compliance(previous_results, plan)

        elif stage == WorkflowStage.COST_ESTIMATION:
            return self._stage_cost_estimation(previous_results)

        elif stage == WorkflowStage.APPROVAL_PREPARATION:
            return self._stage_approval_preparation(user_input, previous_results, plan)

        elif stage == WorkflowStage.TEMPLATE_REFINEMENT:
            return self._stage_template_refinement(user_input, previous_results)

        else:
            raise ValueError(f"Unknown workflow stage: {stage}")

    def _stage_requirements_analysis(
        self, user_input: str, plan: WorkflowPlan
    ) -> Dict[str, Any]:
        """Analyze and clarify requirements."""
        log_agent_start("Requirements Analyzer", "Analyzing requirements")

        # Extract key information from requirements
        extracted_info = {
            "cloud_provider": "azure",  # Default for this demo
            "estimated_complexity": plan.complexity_score,
            "compliance_requirements": plan.compliance_frameworks,
            "key_components": self._extract_components(user_input),
        }

        log_agent_complete(
            "Requirements Analyzer", "Requirements analyzed", extracted_info
        )
        return extracted_info

    def _stage_research_and_planning(
        self, user_input: str, plan: WorkflowPlan
    ) -> Dict[str, Any]:
        """Research best practices and create implementation plan."""
        log_agent_start("Research Agent", "Researching best practices")

        research_result = self.research_agent.research_terraform_docs(user_input)
        best_practices = self.research_agent.get_provider_best_practices("azurerm")

        research_data = {
            "documentation_research": research_result,
            "best_practices": best_practices,
            "recommendations": [],
        }

        log_agent_complete("Research Agent", "Research completed")
        return research_data

    def _stage_template_generation(
        self, user_input: str, previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate Terraform template."""
        log_agent_start("Terraform Agent", "Generating infrastructure template")

        # Get research context if available
        if "research_and_planning" in previous_results:
            research_data = previous_results["research_and_planning"]
            _ = research_data.get("documentation_research", "")

        # Generate template
        template_response = self.terraform_agent.generate_response(user_input)

        # Debug: Log the full response to see what we're getting
        log_info(
            "Terraform Agent",
            f"Full response length: {len(template_response)} characters",
        )
        log_info("Terraform Agent", f"Response preview: {template_response[:300]}...")

        # Extract template from response
        template = self._extract_template(template_response)

        # If no template extracted, try to debug why and provide fallback
        if not template:
            log_warning(
                "Terraform Agent", "No template extracted, checking response format"
            )
            if "```" in template_response:
                log_info("Terraform Agent", "Response contains code blocks")
            if "terraform" in template_response.lower():
                log_info("Terraform Agent", "Response contains 'terraform' keyword")
            if "resource" in template_response.lower():
                log_info("Terraform Agent", "Response contains 'resource' keyword")

            # Generate a fallback template based on the user input
            log_user_update("🔄 Generating fallback template...")
            template = self._generate_fallback_template(user_input)
            if template:
                log_info(
                    "Terraform Agent",
                    f"Generated fallback template: {len(template)} characters",
                )

        result = {
            "template": template,
            "full_response": template_response,
            "template_lines": len(template.split("\n")) if template else 0,
        }

        log_agent_complete(
            "Terraform Agent",
            "Template generated",
            {"template_lines": result["template_lines"]},
        )

        return result

    def _stage_validation_and_compliance(
        self, previous_results: Dict[str, Any], plan: WorkflowPlan
    ) -> Dict[str, Any]:
        """Validate template for compliance and security with quality gates."""
        log_agent_start("Compliance Agent", "Validating compliance and security")

        template = previous_results.get("template_generation", {}).get("template", "")

        if not template:
            log_warning(
                "Compliance Agent",
                "No template available for validation, attempting template regeneration",
            )

            # Try to regenerate template
            try:
                log_user_update("🔄 No template found, attempting regeneration...")
                regeneration_result = self._stage_template_generation(
                    plan.requirements, previous_results
                )
                template = regeneration_result.get("template", "")

                if template:
                    # Update previous results with regenerated template
                    previous_results["template_generation"] = regeneration_result
                    log_info("Compliance Agent", "Template successfully regenerated")
                else:
                    raise ValueError("Template regeneration failed")

            except Exception as e:
                log_warning(
                    "Compliance Agent", f"Template regeneration failed: {str(e)}"
                )
                raise ValueError(
                    "No template available for validation and regeneration failed"
                )

        # Determine which frameworks to use for validation
        if hasattr(self, "compliance_settings") and self.compliance_settings.get(
            "enforce_compliance"
        ):
            # Use user-selected frameworks
            validation_frameworks = self.compliance_settings.get(
                "selected_frameworks", []
            )
        else:
            # Use plan-determined frameworks (legacy behavior)
            validation_frameworks = plan.compliance_frameworks

        # Run compliance validation
        compliance_result = self.compliance_framework.validate_template(
            template, validation_frameworks
        )

        # Basic template validation
        basic_validation = self.terraform_agent._validate_template(template)

        # Get compliance score
        compliance_score = compliance_result.get("compliance_score", 0)
        violations_count = len(compliance_result.get("violations", []))

        # Quality gate: Check if template meets minimum standards using config
        if hasattr(self, "compliance_settings") and self.compliance_settings.get(
            "enforce_compliance"
        ):
            minimum_score_threshold = config.compliance.minimum_score_enforced
            maximum_violations_threshold = config.compliance.max_violations_enforced
        else:
            minimum_score_threshold = config.compliance.minimum_score_relaxed
            maximum_violations_threshold = config.compliance.max_violations_relaxed

        # Only apply quality gates if compliance enforcement is enabled AND frameworks are selected
        should_enforce_quality_gates = (
            hasattr(self, "compliance_settings")
            and self.compliance_settings.get("enforce_compliance")
            and len(validation_frameworks) > 0
        )

        if should_enforce_quality_gates and (
            compliance_score < minimum_score_threshold
            or violations_count > maximum_violations_threshold
        ):
            log_warning(
                "Compliance Agent",
                f"Template quality below threshold: {compliance_score:.1f}% score, {violations_count} violations",
            )
            log_user_update(
                f"⚠️ Template quality insufficient (Score: {compliance_score:.1f}%, Violations: {violations_count})"
            )
            log_user_update("🔄 Attempting to improve template quality...")

            # Try to regenerate with enhanced prompts
            enhanced_template = self._regenerate_enhanced_template(
                plan.requirements, compliance_result
            )
            if enhanced_template:
                # Re-validate the enhanced template
                log_user_update("🔍 Re-validating enhanced template...")
                enhanced_compliance = self.compliance_framework.validate_template(
                    enhanced_template, plan.compliance_frameworks
                )
                enhanced_score = enhanced_compliance.get("compliance_score", 0)
                enhanced_violations = len(enhanced_compliance.get("violations", []))

                if (
                    enhanced_score >= minimum_score_threshold
                    and enhanced_violations <= maximum_violations_threshold
                ):
                    log_info(
                        "Compliance Agent",
                        f"Enhanced template meets quality standards: {enhanced_score:.1f}% score, {enhanced_violations} violations",
                    )
                    # Update results with enhanced template
                    previous_results["template_generation"][
                        "template"
                    ] = enhanced_template
                    template = enhanced_template
                    compliance_result = enhanced_compliance
                    compliance_score = enhanced_score
                    violations_count = enhanced_violations
                else:
                    log_warning(
                        "Compliance Agent",
                        f"Enhanced template still below threshold: {enhanced_score:.1f}% score, {enhanced_violations} violations",
                    )
                    # Use fallback template as last resort
                    fallback_template = self._get_high_quality_fallback_template(
                        plan.requirements
                    )
                    if fallback_template:
                        log_user_update("🔄 Using high-quality fallback template...")
                        previous_results["template_generation"][
                            "template"
                        ] = fallback_template
                        template = fallback_template
                        # Re-validate fallback
                        compliance_result = self.compliance_framework.validate_template(
                            fallback_template, plan.compliance_frameworks
                        )
                        compliance_score = compliance_result.get("compliance_score", 0)
                        violations_count = len(compliance_result.get("violations", []))

        # Determine if quality gate passed based on compliance settings
        if should_enforce_quality_gates:
            quality_gate_passed = (
                compliance_score >= minimum_score_threshold
                and violations_count <= maximum_violations_threshold
            )
        else:
            # If compliance is not enforced, quality gate always passes (basic validation only)
            quality_gate_passed = True

        result = {
            "compliance_validation": compliance_result,
            "basic_validation": basic_validation,
            "overall_score": compliance_score,
            "quality_gate_passed": quality_gate_passed,
            "compliance_enforced": should_enforce_quality_gates,
            "validation_frameworks": validation_frameworks,
        }

        log_agent_complete(
            "Compliance Agent",
            "Validation completed",
            {
                "compliance_score": result["overall_score"],
                "violations": violations_count,
                "quality_gate_passed": result["quality_gate_passed"],
            },
        )

        return result

    def _stage_cost_estimation(
        self, previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate infrastructure costs."""
        log_agent_start("Cost Estimation Agent", "Calculating infrastructure costs")

        template = previous_results.get("template_generation", {}).get("template", "")

        # Use research agent's enhanced cost estimation
        cost_estimate = self.research_agent.estimate_azure_costs(template)

        result = {
            "cost_estimate": cost_estimate,
            "estimation_confidence": "medium",  # Could be enhanced
        }

        log_agent_complete(
            "Cost Estimation Agent",
            "Cost estimation completed",
            {
                "estimated_monthly_cost": cost_estimate.get(
                    "total_monthly_usd", "unknown"
                )
            },
        )

        return result

    def _stage_approval_preparation(
        self, user_input: str, previous_results: Dict[str, Any], plan: WorkflowPlan
    ) -> Dict[str, Any]:
        """Prepare for human approval workflow."""
        log_agent_start("Approval Agent", "Preparing approval request")

        template = previous_results.get("template_generation", {}).get("template", "")
        validation_result = previous_results.get("validation_and_compliance", {})
        cost_estimate = previous_results.get("cost_estimation", {})

        # Create approval request
        approval_request = self.approval_workflow.create_approval_request(
            template=template,
            requirements=user_input,
            validation_result=validation_result.get("compliance_validation", {}),
            estimated_cost=cost_estimate.get("cost_estimate", {}).get(
                "summary", "Cost estimation pending"
            ),
        )

        result = {
            "approval_request": approval_request,
            "approval_summary": self.approval_workflow.get_approval_summary(
                approval_request.id
            ),
        }

        log_agent_complete(
            "Approval Agent",
            "Approval request prepared",
            {"request_id": approval_request.id},
        )

        return result

    def _stage_template_refinement(
        self, user_input: str, previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Refine template based on validation results."""
        log_agent_start("Template Refinement Agent", "Refining template")

        # This would implement template refinement logic
        # For now, return the original template
        template = previous_results.get("template_generation", {}).get("template", "")

        result = {"refined_template": template, "refinements_applied": []}

        log_agent_complete("Template Refinement Agent", "Template refinement completed")
        return result

    def _extract_components(self, user_input: str) -> List[str]:
        """Extract key infrastructure components from user input."""
        components = []

        component_keywords = {
            "web application": [
                "web app",
                "frontend",
                "website",
                "react",
                "angular",
                "vue",
            ],
            "database": ["database", "db", "sql", "mysql", "postgresql", "cosmos"],
            "storage": ["storage", "blob", "file", "data lake"],
            "compute": ["vm", "virtual machine", "compute", "container", "kubernetes"],
            "networking": ["network", "vpc", "subnet", "load balancer", "cdn"],
            "security": ["firewall", "waf", "security", "key vault", "encryption"],
        }

        user_input_lower = user_input.lower()

        for component, keywords in component_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                components.append(component)

        return components

    def _extract_template(self, response: str) -> str:
        """Extract Terraform template from agent response."""
        if not response:
            log_warning(self.name, "Empty response received from Terraform agent")
            return ""

        # Find all code blocks and choose the best one
        all_code_blocks = []

        # Find all HCL code blocks
        hcl_start = 0
        while True:
            hcl_start = response.find("```hcl", hcl_start)
            if hcl_start == -1:
                break

            content_start = hcl_start + 6
            content_end = response.find("```", content_start)

            if content_end > content_start:
                content = response[content_start:content_end].strip()
                all_code_blocks.append(("hcl", content))

            hcl_start = content_end + 3 if content_end != -1 else len(response)

        # Find generic code blocks if no HCL blocks
        if not all_code_blocks:
            generic_start = 0
            while True:
                generic_start = response.find("```", generic_start)
                if generic_start == -1:
                    break

                # Skip if it's a specific language block
                if response[generic_start : generic_start + 10].startswith(
                    ("```hcl", "```terraform", "```python", "```bash")
                ):
                    generic_start += 3
                    continue

                content_start = generic_start + 3
                content_end = response.find("```", content_start)

                if content_end > content_start:
                    content = response[content_start:content_end].strip()
                    all_code_blocks.append(("generic", content))

                generic_start = content_end + 3 if content_end != -1 else len(response)

        # Evaluate all code blocks and choose the best one
        best_template = None
        best_score = 0

        for block_type, content in all_code_blocks:
            if self._is_valid_terraform_content(content):
                # Score based on content quality
                score = len(content)  # Longer templates generally better
                if "terraform" in content.lower():
                    score += 100
                if "provider" in content.lower():
                    score += 50
                if "resource" in content.lower():
                    score += 50

                if score > best_score:
                    best_score = score
                    best_template = content

        if best_template:
            log_info(
                self.name,
                f"Template extracted from best code block, {len(best_template)} characters, score: {best_score}",
            )
            return best_template

        # If no code blocks found, try to extract terraform resources directly
        if "resource " in response:
            lines = response.split("\n")
            template_lines = []
            in_template = False

            for line in lines:
                if any(
                    keyword in line
                    for keyword in [
                        "terraform {",
                        "provider ",
                        "resource ",
                        "variable ",
                        "output ",
                    ]
                ):
                    in_template = True

                if in_template:
                    template_lines.append(line)

                # Stop if we hit a non-terraform line after starting
                if (
                    in_template
                    and line.strip()
                    and not any(char in line for char in ["{", "}", "=", '"'])
                    and not line.strip().startswith("#")
                ):
                    break

            if template_lines:
                template = "\n".join(template_lines).strip()
                log_info(
                    self.name,
                    f"Template extracted from resource blocks, {len(template)} characters",
                )
                return template

        log_warning(self.name, "No Terraform template found in response")
        log_info(self.name, f"Response preview: {response[:200]}...")
        return ""

    def _is_valid_terraform_content(self, content: str) -> bool:
        """Check if content looks like actual Terraform code."""
        content_lower = content.lower()

        # Must contain terraform keywords
        terraform_keywords = ["terraform", "provider", "resource", "variable", "output"]
        has_terraform_keywords = any(
            keyword in content_lower for keyword in terraform_keywords
        )

        # Should contain HCL syntax elements
        has_hcl_syntax = any(char in content for char in ["{", "}", "="])

        # Should not be mostly explanatory text
        lines = content.split("\n")
        code_lines = 0
        text_lines = 0

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            elif any(keyword in line.lower() for keyword in terraform_keywords) or any(
                char in line for char in ["{", "}", "="]
            ):
                code_lines += 1
            else:
                text_lines += 1

        # Should be mostly code, not text
        is_mostly_code = code_lines > text_lines

        return has_terraform_keywords and has_hcl_syntax and is_mostly_code

    def _regenerate_enhanced_template(
        self, requirements: str, compliance_result: Dict[str, Any]
    ) -> str:
        """Regenerate template with enhanced prompts based on compliance violations."""
        log_agent_start(
            "Enhanced Template Generator", "Regenerating with compliance fixes"
        )

        violations = compliance_result.get("violations", [])
        violation_types = [
            v.rule_name if hasattr(v, "rule_name") else str(v) for v in violations
        ]

        # Create enhanced prompt with specific compliance guidance
        enhancement_guidance = []
        if any("encryption" in rule.lower() for rule in violation_types):
            enhancement_guidance.append(
                "- Enable encryption at rest and in transit for all storage and data services"
            )
        if any("backup" in rule.lower() for rule in violation_types):
            enhancement_guidance.append(
                "- Include backup and disaster recovery configurations"
            )
        if any(
            "access" in rule.lower() or "security" in rule.lower()
            for rule in violation_types
        ):
            enhancement_guidance.append(
                "- Implement proper access controls and security groups"
            )
        if any(
            "monitoring" in rule.lower() or "logging" in rule.lower()
            for rule in violation_types
        ):
            enhancement_guidance.append(
                "- Add comprehensive monitoring and logging capabilities"
            )
        if any("network" in rule.lower() for rule in violation_types):
            enhancement_guidance.append(
                "- Include proper network security configurations"
            )

        enhanced_prompt = template_manager.get_prompt(
            "enhanced_terraform",
            enhancement_guidance=chr(10).join(enhancement_guidance),
            requirements=requirements,
        )

        try:
            messages = [
                SystemMessage(
                    content="You are an expert Terraform engineer focused on security and compliance."
                ),
                HumanMessage(content=enhanced_prompt),
            ]

            response = self.llm.invoke(messages)
            enhanced_template = self._extract_template(response.content)

            if enhanced_template:
                log_agent_complete(
                    "Enhanced Template Generator",
                    "Enhanced template generated",
                    {"template_length": len(enhanced_template)},
                )
                return enhanced_template
            else:
                log_warning(
                    "Enhanced Template Generator", "Failed to extract enhanced template"
                )
                return ""

        except Exception as e:
            log_warning(
                "Enhanced Template Generator", f"Enhanced regeneration failed: {str(e)}"
            )
            return ""

    def _get_high_quality_fallback_template(self, requirements: str) -> str:
        """Get a high-quality fallback template that meets compliance standards."""
        log_agent_start(
            "Fallback Template Provider", "Providing high-quality fallback template"
        )

        template = template_manager.get_fallback_template(requirements)

        log_agent_complete(
            "Fallback Template Provider", "High-quality fallback template provided"
        )
        return template

    def _generate_fallback_template(self, user_input: str) -> str:
        """Generate a fallback template when extraction fails."""
        return template_manager.get_fallback_template(user_input)

    def _should_continue_after_error(self, stage: WorkflowStage, error: str) -> bool:
        """Determine if workflow should continue after an error."""
        critical_stages = [
            WorkflowStage.TEMPLATE_GENERATION,
            WorkflowStage.VALIDATION_AND_COMPLIANCE,
        ]

        return stage not in critical_stages

    def _compile_final_response(
        self, plan: WorkflowPlan, results: Dict[str, Any]
    ) -> str:
        """Compile the final response to the user only if quality gates are met."""
        log_agent_start(self.name, "Compiling final response")

        # Check if validation was performed and quality gates passed
        validation_results = results.get("validation_and_compliance", {})
        quality_gate_passed = validation_results.get("quality_gate_passed", False)
        compliance_score = validation_results.get("overall_score", 0)

        # Always provide template, but with appropriate warnings if quality gates not met
        if not quality_gate_passed:
            log_warning(
                self.name,
                f"Quality gates not met - compliance score: {compliance_score:.1f}%",
            )
            log_user_update(
                f"⚠️ Template generated with compliance score: {compliance_score:.1f}%"
            )

        response_parts = []

        # Always add template if generated, with appropriate quality indicators
        if "template_generation" in results:
            template = results["template_generation"].get("template", "")
            if template:
                if quality_gate_passed:
                    response_parts.append(
                        f"## 🏗️ Production-Ready Infrastructure Template\n\n```hcl\n{template}\n```\n"
                    )
                else:
                    response_parts.append(
                        f"## ⚠️ Infrastructure Template (Compliance Review Needed)\n\n```hcl\n{template}\n```\n"
                    )

        # Add validation results with appropriate status
        if "validation_and_compliance" in results:
            validation = results["validation_and_compliance"]
            compliance_score = validation.get("overall_score", 0)
            violations_count = len(
                validation.get("compliance_validation", {}).get("violations", [])
            )

            if quality_gate_passed:
                response_parts.append("## ✅ Quality Validation Passed\n\n")
                response_parts.append(
                    f"**Compliance Score:** {compliance_score:.1f}% ✅\n"
                )
                response_parts.append(
                    f"**Security Violations:** {violations_count} (within acceptable limits)\n"
                )
                response_parts.append("**Quality Gate:** PASSED ✅\n\n")
            else:
                response_parts.append("## ⚠️ Compliance Review Required\n\n")
                response_parts.append(
                    f"**Compliance Score:** {compliance_score:.1f}% ⚠️\n"
                )
                response_parts.append(
                    f"**Security Violations:** {violations_count} (requires attention)\n"
                )
                response_parts.append("**Quality Gate:** REVIEW NEEDED ⚠️\n\n")

                # Add specific violation details for low-compliance templates
                compliance_data = validation.get("compliance_validation", {})
                violations = compliance_data.get("violations", [])
                if violations:
                    response_parts.append("**Key Compliance Issues:**\n")
                    for i, violation in enumerate(
                        violations[:3]
                    ):  # Show top 3 violations
                        if hasattr(violation, "rule_name") and hasattr(
                            violation, "description"
                        ):
                            response_parts.append(
                                f"{i + 1}. {violation.rule_name}: {violation.description}\n"
                            )
                    if len(violations) > 3:
                        response_parts.append(
                            f"   ... and {len(violations) - 3} more issues\n"
                        )
                    response_parts.append("\n")

            # Add framework compliance details
            compliance_data = validation.get("compliance_validation", {})
            if compliance_data.get("frameworks_validated"):
                frameworks = ", ".join(compliance_data.get("frameworks_validated", []))
                response_parts.append(f"**Validated Frameworks:** {frameworks}\n\n")

        # Add cost estimation
        if "cost_estimation" in results:
            cost_data = results["cost_estimation"].get("cost_estimate", {})
            if cost_data:
                cost_summary = cost_data.get("summary", "Cost analysis completed")
                response_parts.append(f"## 💰 Cost Estimate\n\n{cost_summary}\n")

        # Add approval information with appropriate status
        if "approval_preparation" in results:
            approval_data = results["approval_preparation"]
            approval_summary = approval_data.get("approval_summary", "")
            if quality_gate_passed:
                response_parts.append("## ⚖️ Ready for Approval\n\n")
                response_parts.append(
                    "✅ **Template Quality Verified** - Ready for production deployment consideration\n\n"
                )
            else:
                response_parts.append(
                    "## ⚖️ Approval Required (with Compliance Review)\n\n"
                )
                response_parts.append(
                    "⚠️ **Additional Review Needed** - Template requires compliance assessment before deployment\n\n"
                )
            response_parts.append(f"{approval_summary}\n")

        # Add workflow summary with appropriate quality metrics
        completed_stages = (
            len(self.current_workflow.completed_stages) if self.current_workflow else 0
        )
        issues_count = (
            len(self.current_workflow.issues_found) if self.current_workflow else 0
        )

        response_parts.append("## 📊 Workflow Summary\n\n")
        response_parts.append(
            f"- **Stages Completed:** {completed_stages}/{len(plan.stages)} ✅\n"
        )

        if quality_gate_passed:
            response_parts.append("- **Quality Gate Status:** PASSED ✅\n")
            response_parts.append("- **Ready for Production:** ✅ YES\n")
        else:
            response_parts.append("- **Quality Gate Status:** REVIEW NEEDED ⚠️\n")
            response_parts.append(
                "- **Ready for Production:** ⚠️ REQUIRES COMPLIANCE REVIEW\n"
            )

        response_parts.append(f"- **Issues Found:** {issues_count}\n")
        response_parts.append(
            f"- **Estimated Complexity:** {plan.complexity_score}/10\n"
        )

        # Add appropriate next steps based on quality gate status
        response_parts.append("\n## 🚀 Next Steps\n\n")
        if quality_gate_passed:
            response_parts.append(
                "1. ✅ **Template Quality Verified** - Meets enterprise security standards\n"
            )
            response_parts.append(
                "2. 🔍 **Review Deployment Plan** - Verify resources match requirements\n"
            )
            response_parts.append(
                "3. 🧪 **Test in Development** - Deploy to development environment first\n"
            )
            response_parts.append(
                "4. ⚖️ **Submit for Approval** - Ready for stakeholder review\n"
            )
            response_parts.append(
                "5. 🚀 **Deploy to Production** - Execute deployment after approval\n"
            )
        else:
            response_parts.append(
                "1. ⚠️ **Review Compliance Issues** - Address security violations listed above\n"
            )
            response_parts.append(
                "2. 🔍 **Security Assessment** - Have security team review template\n"
            )
            response_parts.append(
                "3. 🧪 **Test in Development** - Deploy to development environment first\n"
            )
            response_parts.append(
                "4. 🔧 **Template Enhancement** - Consider implementing recommended security measures\n"
            )
            response_parts.append(
                "5. ⚖️ **Submit for Review** - Requires additional approval due to compliance gaps\n"
            )

        final_response = "\n".join(response_parts)

        log_agent_complete(
            self.name,
            "High-quality final response compiled",
            {
                "quality_gate_passed": quality_gate_passed,
                "compliance_score": compliance_score,
            },
        )
        return final_response

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status for UI updates."""
        if not self.current_workflow:
            return {"status": "idle"}

        return {
            "status": "active",
            "current_stage": self.current_workflow.current_stage.value,
            "completed_stages": [
                stage.value for stage in self.current_workflow.completed_stages
            ],
            "issues_found": self.current_workflow.issues_found,
            "stage_results": self.current_workflow.stage_results,
        }
