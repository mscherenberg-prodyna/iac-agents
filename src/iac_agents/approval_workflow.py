"""Human-in-the-loop approval workflow for Terraform deployments."""

import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ApprovalStatus(Enum):
    """Status of approval requests."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """Approval request for Terraform deployment."""

    id: str
    template: str
    template_hash: str
    requirements: str
    validation_result: Dict[str, Any]
    estimated_cost: Optional[str]
    created_at: datetime
    status: ApprovalStatus
    reviewer_notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None


class TerraformApprovalWorkflow:
    """Manages human approval workflow for Terraform deployments."""

    def __init__(self):
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[ApprovalRequest] = []

    def create_approval_request(
        self,
        template: str,
        requirements: str,
        validation_result: Dict[str, Any],
        estimated_cost: Optional[str] = None,
    ) -> ApprovalRequest:
        """Create a new approval request."""
        template_hash = hashlib.sha256(template.encode()).hexdigest()[:16]
        request_id = f"tf-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{template_hash}"

        request = ApprovalRequest(
            id=request_id,
            template=template,
            template_hash=template_hash,
            requirements=requirements,
            validation_result=validation_result,
            estimated_cost=estimated_cost,
            created_at=datetime.now(),
            status=ApprovalStatus.PENDING,
        )

        self.pending_requests[request_id] = request
        return request

    def get_approval_summary(self, request_id: str) -> str:
        """Generate human-readable approval summary."""
        if request_id not in self.pending_requests:
            return "❌ Approval request not found"

        request = self.pending_requests[request_id]

        summary = f"""
# Terraform Deployment Approval Request

**Request ID:** `{request.id}`
**Created:** {request.created_at.strftime('%Y-%m-%d %H:%M:%S')}
**Status:** {request.status.value.upper()}

## Requirements
{request.requirements}

## Validation Results
"""

        validation = request.validation_result
        if validation.get("is_valid", False):
            summary += "✅ **Template validation passed**\n\n"
        else:
            summary += "❌ **Template validation failed**\n\n"

        if validation.get("errors"):
            summary += "### ❌ Errors:\n"
            for error in validation["errors"]:
                summary += f"- {error}\n"
            summary += "\n"

        if validation.get("warnings"):
            summary += "### ⚠️ Warnings:\n"
            for warning in validation["warnings"]:
                summary += f"- {warning}\n"
            summary += "\n"

        if validation.get("security_issues"):
            summary += "### 🔒 Security Issues:\n"
            for issue in validation["security_issues"]:
                summary += f"- {issue}\n"
            summary += "\n"

        if validation.get("suggestions"):
            summary += "### 💡 Suggestions:\n"
            for suggestion in validation["suggestions"]:
                summary += f"- {suggestion}\n"
            summary += "\n"

        if request.estimated_cost:
            summary += f"## Estimated Cost\n{request.estimated_cost}\n\n"

        summary += f"""
## Terraform Template
```hcl
{request.template}
```

## Review Checklist
- [ ] Template follows security best practices
- [ ] Resource configurations are appropriate
- [ ] No hardcoded secrets or credentials
- [ ] Network security is properly configured
- [ ] Resource naming follows conventions
- [ ] Cost implications are acceptable
- [ ] Template has been tested in development environment

## Approval Actions
To approve this deployment, respond with: `APPROVE {request.id}`
To reject this deployment, respond with: `REJECT {request.id} [reason]`
To request changes, respond with: `CHANGES {request.id} [required changes]`
"""

        return summary

    def process_approval_response(self, response: str, reviewer: str = "user") -> str:
        """Process human approval response."""
        parts = response.strip().split()
        if len(parts) < 2:
            return "❌ Invalid response format. Use: APPROVE/REJECT/CHANGES <request_id> [notes]"

        action = parts[0].upper()
        request_id = parts[1]
        notes = " ".join(parts[2:]) if len(parts) > 2 else None

        if request_id not in self.pending_requests:
            return f"❌ Request {request_id} not found"

        request = self.pending_requests[request_id]

        if action == "APPROVE":
            return self._approve_request(request, reviewer, notes)
        elif action == "REJECT":
            return self._reject_request(request, reviewer, notes)
        elif action == "CHANGES":
            return self._request_changes(request, reviewer, notes)
        else:
            return "❌ Invalid action. Use APPROVE, REJECT, or CHANGES"

    def _approve_request(
        self, request: ApprovalRequest, reviewer: str, notes: Optional[str]
    ) -> str:
        """Approve a deployment request."""
        request.status = ApprovalStatus.APPROVED
        request.approved_at = datetime.now()
        request.approved_by = reviewer
        request.reviewer_notes = notes

        # Move to history
        self.approval_history.append(request)
        del self.pending_requests[request.id]

        return f"""
✅ **Deployment Approved**

Request `{request.id}` has been approved for deployment.

**Next Steps:**
1. Save the template to a `.tf` file
2. Run `terraform init` to initialize
3. Run `terraform plan` to review changes
4. Run `terraform apply` to deploy
5. Monitor the deployment for any issues

**⚠️ Important Reminders:**
- Test in development environment first
- Have rollback plan ready
- Monitor resource usage and costs
- Document the deployment

**Template ready for deployment:**
```hcl
{request.template}
```
"""

    def _reject_request(
        self, request: ApprovalRequest, reviewer: str, notes: Optional[str]
    ) -> str:
        """Reject a deployment request."""
        request.status = ApprovalStatus.REJECTED
        request.approved_by = reviewer
        request.reviewer_notes = notes

        # Move to history
        self.approval_history.append(request)
        del self.pending_requests[request.id]

        reason = f"\n**Reason:** {notes}" if notes else ""

        return f"""
❌ **Deployment Rejected**

Request `{request.id}` has been rejected.{reason}

Please address the concerns and submit a new request with the revised template.
"""

    def _request_changes(
        self, request: ApprovalRequest, reviewer: str, notes: Optional[str]
    ) -> str:
        """Request changes to deployment."""
        request.reviewer_notes = notes

        changes = f"\n**Requested Changes:** {notes}" if notes else ""

        return f"""
🔄 **Changes Requested**

Request `{request.id}` requires modifications before approval.{changes}

Please revise the template and submit a new approval request.
The current request remains pending until you submit a new version.
"""

    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        return list(self.pending_requests.values())

    def get_approval_history(self, limit: int = 10) -> List[ApprovalRequest]:
        """Get approval history."""
        return sorted(self.approval_history, key=lambda x: x.created_at, reverse=True)[
            :limit
        ]

    def cleanup_expired_requests(self, hours: int = 24):
        """Remove expired approval requests."""
        now = datetime.now()
        expired_ids = []

        for request_id, request in self.pending_requests.items():
            age_hours = (now - request.created_at).total_seconds() / 3600
            if age_hours > hours:
                request.status = ApprovalStatus.EXPIRED
                self.approval_history.append(request)
                expired_ids.append(request_id)

        for request_id in expired_ids:
            del self.pending_requests[request_id]

        return len(expired_ids)

    def export_approval_data(self) -> Dict[str, Any]:
        """Export approval data for persistence."""
        return {
            "pending_requests": {
                k: asdict(v) for k, v in self.pending_requests.items()
            },
            "approval_history": [asdict(req) for req in self.approval_history],
        }
