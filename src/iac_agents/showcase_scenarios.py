"""Showcase scenarios for demonstrating AI-driven infrastructure deployment."""

SHOWCASE_SCENARIOS = {
    "startup_mvp": {
        "title": "🚀 Startup MVP Environment",
        "business_context": "A startup needs to quickly deploy their MVP to validate product-market fit",
        "user_request": """
We're a fintech startup launching our MVP. We need:

Business Requirements:
- Secure web application for 1000+ concurrent users
- PCI DSS compliance for payment processing
- 99.9% uptime SLA
- Auto-scaling for traffic spikes
- Separate dev/staging/prod environments

Technical Needs:
- React frontend with global CDN
- Node.js API with load balancing
- PostgreSQL database with encryption
- Redis for session management
- Application monitoring and alerts
- CI/CD pipeline integration

Budget: $500/month initially, scalable to $2000/month

Timeline: Production ready in 3 days
        """,
        "expected_resources": [
            "Azure App Service (Premium tier)",
            "Azure Database for PostgreSQL (Flexible Server)",
            "Azure Redis Cache",
            "Azure Application Gateway with WAF",
            "Azure CDN",
            "Azure Key Vault",
            "Application Insights",
            "Azure DevOps integration"
        ],
        "compliance_requirements": ["PCI DSS", "GDPR", "SOC 2"],
        "estimated_cost": "$450-750/month"
    },
    
    "enterprise_migration": {
        "title": "🏢 Enterprise Application Migration",
        "business_context": "Large enterprise migrating legacy on-premises application to Azure",
        "user_request": """
Enterprise Migration Project:

Current State:
- Legacy .NET application on Windows Server 2012
- SQL Server 2016 database (500GB)
- 50,000 daily active users
- 24/7 operations requirement
- Complex AD integration

Migration Requirements:
- Zero-downtime migration strategy
- Enhanced security and compliance
- Cost optimization (target 30% reduction)
- Disaster recovery across regions
- Advanced monitoring and analytics

Governance:
- Must comply with SOX, HIPAA, ISO 27001
- Approved vendor list constraints
- Network isolation requirements
- Audit trail for all changes

Go-live date: 6 weeks
        """,
        "expected_resources": [
            "Azure Virtual Machines (multiple tiers)",
            "Azure SQL Database (Premium)",
            "Azure Active Directory Premium",
            "Azure Site Recovery",
            "Azure Backup",
            "Network Security Groups",
            "Azure Firewall",
            "Log Analytics Workspace",
            "Azure Monitor",
            "Azure Policy"
        ],
        "compliance_requirements": ["SOX", "HIPAA", "ISO 27001", "PCI DSS"],
        "estimated_cost": "$3,500-5,000/month"
    },
    
    "ai_ml_platform": {
        "title": "🤖 AI/ML Research Platform",
        "business_context": "Research team needs scalable ML infrastructure for model training and inference",
        "user_request": """
AI Research Platform Requirements:

Research Needs:
- Large language model training (up to 100B parameters)
- Computer vision model development
- Multi-GPU training capabilities
- Jupyter notebook environment
- Data lake for 10TB+ datasets

Infrastructure:
- GPU clusters (V100/A100)
- High-performance storage
- Container orchestration
- Model versioning and registry
- Automated ML pipelines

Collaboration:
- Multi-tenant access for 20+ researchers
- Resource quotas and billing tracking
- Integration with popular ML frameworks
- Experiment tracking and visualization

Security:
- Sensitive research data protection
- IP compliance and access controls
- Secure data sharing capabilities
        """,
        "expected_resources": [
            "Azure Machine Learning",
            "Azure Kubernetes Service with GPU nodes",
            "Azure Data Lake Storage Gen2",
            "Azure Container Registry",
            "Azure Databricks",
            "Azure Cognitive Services",
            "Azure Storage (Premium SSD)",
            "Azure Virtual Network",
            "Azure Active Directory B2B"
        ],
        "compliance_requirements": ["ISO 27001", "Research Data Protection"],
        "estimated_cost": "$8,000-15,000/month"
    },
    
    "ecommerce_scale": {
        "title": "🛒 E-commerce Black Friday Preparation",
        "business_context": "E-commerce company preparing for 10x traffic surge during Black Friday",
        "user_request": """
Black Friday Infrastructure Scaling:

Current Baseline:
- 10,000 concurrent users normal load
- $2M monthly revenue
- Existing Azure App Service setup

Black Friday Projections:
- 100,000+ concurrent users expected
- 50x increase in transaction volume
- Payment processing must never fail
- Image/video content delivery globally

Requirements:
- Auto-scaling from 10 to 1000+ instances
- Global load distribution
- Database read replicas
- CDN for static content
- Real-time inventory management
- Fraud detection integration

Business Critical:
- Zero downtime during peak hours
- Sub-second page load times globally
- PCI DSS compliance for payments
- Real-time analytics dashboard

Duration: Scale up 1 week before, scale down 1 week after
        """,
        "expected_resources": [
            "Azure App Service (Premium/Isolated tiers)",
            "Azure Database for MySQL (Hyperscale)",
            "Azure Redis Cache (Premium)",
            "Azure CDN Premium",
            "Azure Traffic Manager",
            "Azure Application Gateway",
            "Azure Functions for serverless scaling",
            "Azure Event Grid",
            "Azure Cosmos DB",
            "Azure Monitor with custom metrics"
        ],
        "compliance_requirements": ["PCI DSS", "GDPR"],
        "estimated_cost": "$15,000-25,000/month during peak"
    }
}

def get_scenario_by_title(title: str):
    """Get scenario by title for demo purposes."""
    for key, scenario in SHOWCASE_SCENARIOS.items():
        if title.lower() in scenario["title"].lower():
            return scenario
    return None

def get_all_scenario_titles():
    """Get list of all scenario titles for UI selection."""
    return [scenario["title"] for scenario in SHOWCASE_SCENARIOS.values()]