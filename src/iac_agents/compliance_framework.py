"""Compliance and governance validation framework for infrastructure deployments."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class ComplianceLevel(Enum):
    """Compliance requirement levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ComplianceRule:
    """A compliance rule definition."""

    id: str
    name: str
    description: str
    level: ComplianceLevel
    frameworks: List[str]  # e.g., ["SOX", "HIPAA", "PCI DSS"]
    pattern: str  # Regex pattern to match in templates
    negative_pattern: str = None  # Pattern that should NOT be present
    recommendation: str = ""


@dataclass
class ComplianceViolation:
    """A compliance violation found in infrastructure template."""

    rule_id: str
    rule_name: str
    level: ComplianceLevel
    frameworks: List[str]
    description: str
    location: str
    recommendation: str
    auto_fixable: bool = False


class ComplianceFramework:
    """Validates infrastructure templates against compliance frameworks."""

    def __init__(self):
        self.rules = self._initialize_compliance_rules()

    def _initialize_compliance_rules(self) -> Dict[str, ComplianceRule]:
        """Initialize compliance rules for various frameworks."""
        rules = {}

        # PCI DSS Rules
        rules["pci_001"] = ComplianceRule(
            id="pci_001",
            name="No hardcoded credit card data",
            description="Credit card data must not be hardcoded in templates",
            level=ComplianceLevel.CRITICAL,
            frameworks=["PCI DSS"],
            pattern=r"\b4[0-9]{12}(?:[0-9]{3})?\b|\b5[1-5][0-9]{14}\b|\b3[47][0-9]{13}\b",
            recommendation="Use Azure Key Vault or encrypted storage for sensitive data",
        )

        rules["pci_002"] = ComplianceRule(
            id="pci_002",
            name="Encryption at rest required",
            description="All storage must use encryption at rest",
            level=ComplianceLevel.CRITICAL,
            frameworks=["PCI DSS", "HIPAA"],
            pattern=r"encryption.*=.*true|encrypted.*=.*true",
            negative_pattern=r"storage.*encryption.*=.*false",
            recommendation="Enable encryption at rest for all storage accounts",
        )

        # HIPAA Rules
        rules["hipaa_001"] = ComplianceRule(
            id="hipaa_001",
            name="Data in transit encryption",
            description="All data transmission must be encrypted",
            level=ComplianceLevel.CRITICAL,
            frameworks=["HIPAA", "SOX"],
            pattern=r"enable_https_traffic_only.*=.*true|ssl_enforcement_enabled.*=.*true",
            recommendation="Enable HTTPS/TLS for all data transmission",
        )

        rules["hipaa_002"] = ComplianceRule(
            id="hipaa_002",
            name="Access logging required",
            description="All resource access must be logged",
            level=ComplianceLevel.HIGH,
            frameworks=["HIPAA", "SOX", "ISO 27001"],
            pattern=r"diagnostic.*settings|log_analytics|audit",
            recommendation="Enable diagnostic settings and audit logging",
        )

        # SOX Rules
        rules["sox_001"] = ComplianceRule(
            id="sox_001",
            name="Network isolation",
            description="Production resources must be network isolated",
            level=ComplianceLevel.HIGH,
            frameworks=["SOX", "ISO 27001"],
            pattern=r"network_security_group|subnet|virtual_network",
            recommendation="Implement proper network segmentation",
        )

        rules["sox_002"] = ComplianceRule(
            id="sox_002",
            name="Backup and recovery",
            description="Critical data must have backup and recovery",
            level=ComplianceLevel.HIGH,
            frameworks=["SOX", "ISO 27001"],
            pattern=r"backup|recovery|geo_redundant",
            recommendation="Implement automated backup and disaster recovery",
        )

        # GDPR Rules
        rules["gdpr_001"] = ComplianceRule(
            id="gdpr_001",
            name="Data residency compliance",
            description="Personal data must remain in approved regions",
            level=ComplianceLevel.CRITICAL,
            frameworks=["GDPR"],
            pattern=r"location.*=.*(europe|eu-)",
            recommendation="Ensure data residency in EU regions for GDPR compliance",
        )

        rules["gdpr_002"] = ComplianceRule(
            id="gdpr_002",
            name="Data retention policies",
            description="Automated data retention policies required",
            level=ComplianceLevel.HIGH,
            frameworks=["GDPR"],
            pattern=r"retention|lifecycle|delete_after",
            recommendation="Implement automated data retention and deletion",
        )

        # ISO 27001 Rules
        rules["iso_001"] = ComplianceRule(
            id="iso_001",
            name="Multi-factor authentication",
            description="Administrative access requires MFA",
            level=ComplianceLevel.HIGH,
            frameworks=["ISO 27001", "SOX"],
            pattern=r"mfa|multi.*factor|conditional_access",
            recommendation="Enable MFA for all administrative access",
        )

        rules["iso_002"] = ComplianceRule(
            id="iso_002",
            name="Least privilege access",
            description="Resources should follow least privilege principle",
            level=ComplianceLevel.MEDIUM,
            frameworks=["ISO 27001", "SOX", "HIPAA"],
            pattern=r'role.*=.*"Contributor"|role.*=.*"Reader"',
            negative_pattern=r'role.*=.*"Owner"|permissions.*=.*"\*"',
            recommendation="Use specific roles instead of broad permissions",
        )

        # Azure Security Best Practices
        rules["azure_001"] = ComplianceRule(
            id="azure_001",
            name="No public access to databases",
            description="Databases should not allow public internet access",
            level=ComplianceLevel.CRITICAL,
            frameworks=["PCI DSS", "HIPAA", "SOX"],
            pattern=(
                r'public_network_access_enabled.*=.*false|'
                r'firewall_rule.*start_ip_address.*=.*"10\.|192\.168\.|172\."'
            ),
            negative_pattern=r'public_network_access_enabled.*=.*true|firewall_rule.*start_ip_address.*=.*"0\.0\.0\.0"',
            recommendation="Restrict database access to private networks only",
        )

        rules["azure_002"] = ComplianceRule(
            id="azure_002",
            name="Web Application Firewall required",
            description="Web applications must use WAF protection",
            level=ComplianceLevel.HIGH,
            frameworks=["PCI DSS", "ISO 27001"],
            pattern=r"application_gateway.*waf|web_application_firewall",
            recommendation="Deploy Web Application Firewall for web applications",
        )

        rules["azure_003"] = ComplianceRule(
            id="azure_003",
            name="Resource tagging for governance",
            description="All resources must be properly tagged",
            level=ComplianceLevel.MEDIUM,
            frameworks=["SOX", "ISO 27001"],
            pattern=r"tags.*=.*{.*environment.*=|tags.*=.*{.*owner.*=",
            recommendation="Add required tags: environment, owner, cost-center",
        )

        return rules

    def validate_template(
        self, template: str, required_frameworks: List[str] = None
    ) -> Dict[str, Any]:
        """Validate template against compliance frameworks."""
        violations = []
        passed_rules = []

        # Get applicable rules
        applicable_rules = self._get_applicable_rules(required_frameworks or [])

        for rule in applicable_rules:
            violation = self._check_rule(template, rule)
            if violation:
                violations.append(violation)
            else:
                passed_rules.append(rule.id)

        # Calculate compliance score
        total_rules = len(applicable_rules)
        passed_count = len(passed_rules)
        compliance_score = (
            (passed_count / total_rules * 100) if total_rules > 0 else 100
        )

        return {
            "compliance_score": compliance_score,
            "violations": violations,
            "passed_rules": passed_rules,
            "total_rules_checked": total_rules,
            "framework_compliance": self._calculate_framework_compliance(
                violations, required_frameworks or []
            ),
            "remediation_priority": self._prioritize_remediation(violations),
        }

    def _get_applicable_rules(self, frameworks: List[str]) -> List[ComplianceRule]:
        """Get rules applicable to specified frameworks."""
        if not frameworks:
            return list(self.rules.values())

        applicable_rules = []
        for rule in self.rules.values():
            if any(framework in rule.frameworks for framework in frameworks):
                applicable_rules.append(rule)

        return applicable_rules

    def _check_rule(self, template: str, rule: ComplianceRule) -> ComplianceViolation:
        """Check if template violates a specific rule."""
        template_lower = template.lower()

        # Check positive pattern (what should be present)
        if rule.pattern:
            if not re.search(rule.pattern, template_lower, re.IGNORECASE):
                return ComplianceViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    level=rule.level,
                    frameworks=rule.frameworks,
                    description=f"Missing: {rule.description}",
                    location="Template",
                    recommendation=rule.recommendation,
                )

        # Check negative pattern (what should NOT be present)
        if rule.negative_pattern:
            match = re.search(rule.negative_pattern, template_lower, re.IGNORECASE)
            if match:
                return ComplianceViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    level=rule.level,
                    frameworks=rule.frameworks,
                    description=f"Violation: {rule.description}",
                    location=f"Line containing: {match.group()[:50]}...",
                    recommendation=rule.recommendation,
                )

        return None

    def _calculate_framework_compliance(
        self, violations: List[ComplianceViolation], frameworks: List[str]
    ) -> Dict[str, float]:
        """Calculate compliance score per framework."""
        framework_scores = {}

        for framework in frameworks:
            framework_rules = [
                rule for rule in self.rules.values() if framework in rule.frameworks
            ]
            framework_violations = [v for v in violations if framework in v.frameworks]

            total_rules = len(framework_rules)
            violations_count = len(framework_violations)

            if total_rules > 0:
                score = ((total_rules - violations_count) / total_rules) * 100
                framework_scores[framework] = max(0, score)
            else:
                framework_scores[framework] = 100

        return framework_scores

    def _prioritize_remediation(
        self, violations: List[ComplianceViolation]
    ) -> List[ComplianceViolation]:
        """Prioritize violations for remediation."""

        # Sort by level (critical first), then by number of affected frameworks
        def sort_key(violation):
            level_priority = {
                ComplianceLevel.CRITICAL: 0,
                ComplianceLevel.HIGH: 1,
                ComplianceLevel.MEDIUM: 2,
                ComplianceLevel.LOW: 3,
            }
            return (level_priority[violation.level], -len(violation.frameworks))

        return sorted(violations, key=sort_key)

    def generate_compliance_report(
        self, validation_result: Dict[str, Any], frameworks: List[str]
    ) -> str:
        """Generate a human-readable compliance report."""
        violations = validation_result["violations"]
        score = validation_result["compliance_score"]
        framework_scores = validation_result["framework_compliance"]

        report = f"""
# Compliance Validation Report

## Overall Compliance Score: {score:.1f}%

"""

        # Framework-specific scores
        if framework_scores:
            report += "## Framework Compliance\n"
            for framework, framework_score in framework_scores.items():
                status_emoji = (
                    "✅"
                    if framework_score >= 90
                    else "⚠️" if framework_score >= 70 else "❌"
                )
                report += f"- {status_emoji} **{framework}**: {framework_score:.1f}%\n"
            report += "\n"

        # Critical violations
        critical_violations = [
            v for v in violations if v.level == ComplianceLevel.CRITICAL
        ]
        if critical_violations:
            report += "## 🚨 Critical Violations (Must Fix)\n"
            for violation in critical_violations:
                report += (
                    f"- **{violation.rule_name}** ({', '.join(violation.frameworks)})\n"
                )
                report += f"  - {violation.description}\n"
                report += f"  - 💡 {violation.recommendation}\n\n"

        # High priority violations
        high_violations = [v for v in violations if v.level == ComplianceLevel.HIGH]
        if high_violations:
            report += "## ⚠️ High Priority Violations\n"
            for violation in high_violations:
                report += (
                    f"- **{violation.rule_name}** ({', '.join(violation.frameworks)})\n"
                )
                report += f"  - {violation.description}\n"
                report += f"  - 💡 {violation.recommendation}\n\n"

        # Medium/Low violations
        other_violations = [
            v
            for v in violations
            if v.level in [ComplianceLevel.MEDIUM, ComplianceLevel.LOW]
        ]
        if other_violations:
            report += "## 📋 Other Recommendations\n"
            for violation in other_violations:
                report += f"- **{violation.rule_name}** ({violation.level.value})\n"
                report += f"  - {violation.recommendation}\n\n"

        if not violations:
            report += (
                "## ✅ All Compliance Checks Passed!\n\n"
                "Your infrastructure template meets all specified compliance requirements.\n"
            )

        return report
