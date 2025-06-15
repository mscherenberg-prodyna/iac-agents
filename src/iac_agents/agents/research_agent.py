"""Research Agent for querying Terraform documentation and best practices."""

import os
from typing import Any, Dict, List

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI, ChatOpenAI

try:
    from langchain_community.tools import DuckDuckGoSearchRun
except ImportError:
    DuckDuckGoSearchRun = None
from dotenv import load_dotenv

load_dotenv()


class TerraformResearchAgent:
    """Agent specialized in researching Terraform documentation."""

    def __init__(self):
        self.llm = self._initialize_llm()
        self.search_tool = DuckDuckGoSearchRun() if DuckDuckGoSearchRun else None

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
                temperature=0.1,
            )
        else:
            return ChatOpenAI(model="gpt-4", temperature=0.1)

    def research_terraform_docs(self, query: str) -> str:
        """Research Terraform documentation based on user query."""
        # Create targeted search queries
        search_queries = self._generate_search_queries(query)

        # Search for relevant documentation with rate limiting protection
        search_results = []
        if self.search_tool:
            for i, search_query in enumerate(search_queries):
                try:
                    result = self.search_tool.run(search_query)
                    search_results.append(result)
                    # Add delay to avoid rate limiting
                    if i < len(search_queries) - 1:  # Don't delay after last query
                        import time

                        time.sleep(2)
                except Exception as e:
                    print(f"Search failed for query '{search_query}': {e}")
                    # Continue to next query on failure
                    continue
        else:
            print("Search tool not available, using general guidance")

        # Synthesize the research findings
        if search_results:
            research_summary = self._synthesize_research(query, search_results)
        else:
            # Provide intelligent fallback based on query content
            research_summary = self._generate_fallback_guidance(query)

        return research_summary

    def _generate_search_queries(self, user_query: str) -> List[str]:
        """Generate targeted search queries for Terraform documentation."""
        base_queries = [
            f"site:registry.terraform.io {user_query}",
            f"site:terraform.io {user_query} documentation",
            f"terraform {user_query} best practices",
            f"terraform {user_query} example",
        ]

        # Add cloud provider specific searches if mentioned
        cloud_providers = ["azure", "aws", "gcp", "google cloud"]
        for provider in cloud_providers:
            if provider in user_query.lower():
                query = f"terraform {provider} {user_query} " "official documentation"
                base_queries.append(query)
                break

        return base_queries[:3]  # Limit to 3 searches to avoid rate limits

    def _synthesize_research(
        self, original_query: str, search_results: List[str]
    ) -> str:
        """Synthesize research results into actionable guidance."""
        system_prompt = """You are a Terraform documentation expert.
Analyze the search results and provide concise, actionable guidance
for implementing the user's requirements.

Focus on:
1. Current best practices
2. Security considerations
3. Resource configuration patterns
4. Common pitfalls to avoid

Keep your response concise and practical."""

        combined_results = "\n\n".join(search_results)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"""
Original query: {original_query}

Search results:
{combined_results}

Provide concise guidance for implementing this Terraform configuration."""
            ),
        ]

        response = self.llm.invoke(messages)
        return response.content

    def _generate_fallback_guidance(self, query: str) -> str:
        """Generate fallback guidance when search fails."""
        query_lower = query.lower()

        # Document storage guidance
        if any(
            keyword in query_lower
            for keyword in ["document", "file", "storage", "legal", "compliance"]
        ):
            return """
            For document storage and legal compliance in Azure:

            **Recommended Approach:**
            - Use Azure Blob Storage with immutable storage policies
            - Enable versioning and soft delete for data protection
            - Configure lifecycle management for automated archiving
            - Implement Azure Policy for compliance enforcement
            - Use Azure Backup for additional protection

            **Key Terraform Resources:**
            - azurerm_storage_account with proper security settings
            - azurerm_storage_management_policy for lifecycle rules
            - azurerm_storage_container with appropriate access levels
            - azurerm_backup_vault for long-term retention

            **Compliance Features:**
            - WORM (Write Once, Read Many) capabilities
            - Legal hold functionality
            - Audit logging and monitoring
            - Encryption at rest and in transit
            """

        # General infrastructure guidance
        elif any(keyword in query_lower for keyword in ["web", "app", "application"]):
            return """
            For web applications in Azure:

            **Recommended Architecture:**
            - Azure App Service for hosting
            - Azure Application Gateway with WAF
            - Azure Database for data persistence
            - Azure Key Vault for secrets management

            **Best Practices:**
            - Use managed identities for authentication
            - Enable HTTPS-only access
            - Implement proper network segmentation
            - Configure monitoring and alerting
            """

        else:
            return """
            General Azure infrastructure best practices:

            **Security:**
            - Use Azure Key Vault for secrets
            - Enable encryption at rest and in transit
            - Implement network security groups
            - Use managed identities where possible

            **Reliability:**
            - Deploy across availability zones
            - Implement backup strategies
            - Use Azure Monitor for observability
            - Plan for disaster recovery

            **Cost Optimization:**
            - Right-size resources based on workload
            - Use reserved instances for predictable workloads
            - Implement auto-scaling policies
            - Regular cost review and optimization
            """

    def get_provider_best_practices(
        self, provider: str = "azurerm"
    ) -> Dict[str, List[str]]:
        """Get best practices for specific Terraform providers."""
        best_practices = {
            "azurerm": [
                "Use azurerm provider version constraints",
                "Configure backend for state management",
                "Use Azure Key Vault for secrets",
                "Implement proper resource tagging",
                "Use managed identities when possible",
                "Follow Azure naming conventions",
            ],
            "aws": [
                "Use aws provider version constraints",
                "Configure S3 backend for state",
                "Use AWS Secrets Manager for sensitive data",
                "Implement least privilege IAM policies",
                "Use AWS resource tagging standards",
                "Configure proper VPC and security groups",
            ],
            "google": [
                "Use google provider version constraints",
                "Configure GCS backend for state",
                "Use Google Secret Manager",
                "Implement IAM best practices",
                "Use proper resource labeling",
                "Configure VPC and firewall rules properly",
            ],
        }

        return {
            "general": [
                "Use version constraints for all providers",
                "Implement remote state management",
                "Use variables for reusable values",
                "Add meaningful resource descriptions",
                "Implement proper error handling",
                "Use modules for reusable components",
            ],
            "provider_specific": best_practices.get(provider, []),
        }

    def validate_terraform_syntax(self, template: str) -> Dict[str, any]:
        """Basic validation of Terraform template syntax."""
        validation_result = {"syntax_valid": True, "issues": [], "suggestions": []}

        # Check for basic HCL structure
        required_blocks = ["terraform", "provider", "resource"]
        missing_blocks = []

        for block in required_blocks:
            if block not in template.lower():
                missing_blocks.append(block)

        if missing_blocks:
            validation_result["issues"].extend(
                [f"Missing {block} block" for block in missing_blocks]
            )

        # Check for common syntax issues
        if template.count("{") != template.count("}"):
            validation_result["syntax_valid"] = False
            validation_result["issues"].append("Mismatched braces")

        # Check for security best practices
        if "password" in template.lower() and "random_password" not in template.lower():
            validation_result["suggestions"].append(
                "Consider using random_password resource for passwords"
            )

        if "admin" in template.lower():
            validation_result["suggestions"].append(
                "Review admin access configurations for security"
            )

        return validation_result

    def estimate_azure_costs(self, template: str) -> Dict[str, Any]:
        """Estimate Azure infrastructure costs based on Terraform template."""
        cost_estimate = {
            "total_monthly_usd": 0,
            "breakdown": {},
            "summary": "",
            "confidence": "medium",
        }

        try:
            # Extract Azure resources from template
            resources = self._extract_azure_resources(template)

            monthly_cost = 0
            breakdown = {}

            for resource_type, instances in resources.items():
                resource_cost = self._estimate_resource_cost(resource_type, instances)
                breakdown[resource_type] = resource_cost
                monthly_cost += resource_cost["monthly_usd"]

            cost_estimate.update(
                {
                    "total_monthly_usd": monthly_cost,
                    "breakdown": breakdown,
                    "summary": self._generate_cost_summary(monthly_cost, breakdown),
                    "confidence": self._assess_cost_confidence(resources),
                }
            )

        except Exception as e:
            cost_estimate["summary"] = f"Cost estimation failed: {str(e)}"
            cost_estimate["confidence"] = "low"

        return cost_estimate

    def _extract_azure_resources(
        self, template: str
    ) -> Dict[str, List[Dict[str, str]]]:
        """Extract Azure resources from Terraform template."""
        import re

        resources = {}

        # Resource patterns for different Azure services
        resource_patterns = {
            "azurerm_app_service": r'resource\s+"azurerm_app_service"\s+"([^"]+)"',
            "azurerm_app_service_plan": r'resource\s+"azurerm_app_service_plan"\s+"([^"]+)"',
            "azurerm_sql_database": r'resource\s+"azurerm_sql_database"\s+"([^"]+)"',
            "azurerm_sql_server": r'resource\s+"azurerm_sql_server"\s+"([^"]+)"',
            "azurerm_storage_account": r'resource\s+"azurerm_storage_account"\s+"([^"]+)"',
            "azurerm_virtual_machine": r'resource\s+"azurerm_virtual_machine"\s+"([^"]+)"',
            "azurerm_kubernetes_cluster": r'resource\s+"azurerm_kubernetes_cluster"\s+"([^"]+)"',
            "azurerm_cosmosdb_account": r'resource\s+"azurerm_cosmosdb_account"\s+"([^"]+)"',
            "azurerm_redis_cache": r'resource\s+"azurerm_redis_cache"\s+"([^"]+)"',
            "azurerm_application_gateway": r'resource\s+"azurerm_application_gateway"\s+"([^"]+)"',
        }

        for resource_type, pattern in resource_patterns.items():
            matches = re.findall(pattern, template, re.IGNORECASE)
            if matches:
                resources[resource_type] = [{"name": match} for match in matches]

        return resources

    def _estimate_resource_cost(
        self, resource_type: str, instances: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Estimate cost for a specific Azure resource type."""
        # Simplified cost estimation based on typical Azure pricing
        # In production, this would use the Azure Pricing API

        cost_data = {
            "azurerm_app_service_plan": {
                "basic": {
                    "monthly_usd": 13.87,
                    "description": "Basic B1 (1 Core, 1.75 GB RAM)",
                },
                "standard": {
                    "monthly_usd": 55.48,
                    "description": "Standard S1 (1 Core, 1.75 GB RAM)",
                },
                "premium": {
                    "monthly_usd": 166.44,
                    "description": "Premium P1v2 (1 Core, 3.5 GB RAM)",
                },
            },
            "azurerm_app_service": {
                "basic": {
                    "monthly_usd": 0,
                    "description": "Included with App Service Plan",
                },
            },
            "azurerm_sql_database": {
                "basic": {"monthly_usd": 5.88, "description": "Basic DTU"},
                "standard": {
                    "monthly_usd": 29.40,
                    "description": "Standard S1 (20 DTUs)",
                },
                "premium": {"monthly_usd": 441, "description": "Premium P1 (125 DTUs)"},
            },
            "azurerm_sql_server": {
                "basic": {
                    "monthly_usd": 0,
                    "description": "No additional cost for logical server",
                }
            },
            "azurerm_storage_account": {
                "basic": {"monthly_usd": 20.48, "description": "Standard LRS (100 GB)"},
                "premium": {
                    "monthly_usd": 102.40,
                    "description": "Premium LRS (100 GB)",
                },
            },
            "azurerm_virtual_machine": {
                "small": {
                    "monthly_usd": 60.74,
                    "description": "Standard B2s (2 vCPUs, 4 GB RAM)",
                },
                "medium": {
                    "monthly_usd": 175.20,
                    "description": "Standard D4s v3 (4 vCPUs, 16 GB RAM)",
                },
                "large": {
                    "monthly_usd": 350.40,
                    "description": "Standard D8s v3 (8 vCPUs, 32 GB RAM)",
                },
            },
            "azurerm_kubernetes_cluster": {
                "basic": {
                    "monthly_usd": 73.00,
                    "description": "Managed Kubernetes + 2 Standard B2s nodes",
                },
                "standard": {
                    "monthly_usd": 219.00,
                    "description": "Managed Kubernetes + 3 Standard D4s v3 nodes",
                },
            },
            "azurerm_cosmosdb_account": {
                "basic": {
                    "monthly_usd": 24.63,
                    "description": "400 RU/s provisioned throughput",
                },
                "standard": {
                    "monthly_usd": 58.71,
                    "description": "1000 RU/s provisioned throughput",
                },
            },
            "azurerm_redis_cache": {
                "basic": {"monthly_usd": 16.06, "description": "Basic C1 (250 MB)"},
                "standard": {"monthly_usd": 40.15, "description": "Standard C2 (1 GB)"},
            },
            "azurerm_application_gateway": {
                "basic": {"monthly_usd": 19.71, "description": "Standard v2 (small)"},
                "waf": {"monthly_usd": 32.85, "description": "WAF v2 (small)"},
            },
        }

        if resource_type not in cost_data:
            return {
                "monthly_usd": 50,  # Default estimate
                "tier": "unknown",
                "description": f"Estimated cost for {resource_type}",
                "instances": len(instances),
            }

        # Default to "standard" tier for most resources
        tier = (
            "standard"
            if "standard" in cost_data[resource_type]
            else list(cost_data[resource_type].keys())[0]
        )
        tier_data = cost_data[resource_type][tier]

        total_monthly = tier_data["monthly_usd"] * len(instances)

        return {
            "monthly_usd": total_monthly,
            "tier": tier,
            "description": tier_data["description"],
            "instances": len(instances),
        }

    def _generate_cost_summary(
        self, total_monthly: float, breakdown: Dict[str, Any]
    ) -> str:
        """Generate a human-readable cost summary."""
        if total_monthly == 0:
            return "Cost estimation not available for this template."

        summary = f"**Estimated Monthly Cost: ${total_monthly:.2f}**\n\n"

        if breakdown:
            summary += "**Cost Breakdown:**\n"
            for resource_type, cost_data in breakdown.items():
                resource_name = (
                    resource_type.replace("azurerm_", "").replace("_", " ").title()
                )
                monthly_cost = cost_data["monthly_usd"]
                instances = cost_data["instances"]

                if monthly_cost > 0:
                    instance_text = f" x{instances}" if instances > 1 else ""
                    summary += (
                        f"- {resource_name}{instance_text}: ${monthly_cost:.2f}/month\n"
                    )

        summary += "\n💡 **Note:** Costs may vary based on actual usage, region, and specific configurations."
        return summary

    def _assess_cost_confidence(
        self, resources: Dict[str, List[Dict[str, str]]]
    ) -> str:
        """Assess confidence level of cost estimation."""
        if not resources:
            return "low"

        # More resources = lower confidence due to complexity
        total_resources = sum(len(instances) for instances in resources.values())

        if total_resources <= 3:
            return "high"
        elif total_resources <= 8:
            return "medium"
        else:
            return "low"
