"""Human approval handler for chat."""

from langgraph.types import interrupt

from ...logging_system import log_agent_complete, log_agent_start, log_info
from ...templates.template_manager import template_manager
from ..state import InfrastructureStateDict
from ..utils import make_llm_call

AGENT_NAME = "human_approval_handler"


def human_approval(state: InfrastructureStateDict) -> InfrastructureStateDict:
    """Handle human approval workflow using LangGraph interrupt."""
    log_agent_start("Human Approval", "Requesting human approval")

    # Check if manual approval is required from UI settings
    requires_approval = state.get("requires_approval", True)
    log_info(AGENT_NAME, f"requires_approval={requires_approval}")

    if not requires_approval:
        # Auto-approve if approval not required
        log_info(AGENT_NAME, "Auto-approving (approval not required)")
        approval_received = True
    else:
        # Use LangGraph interrupt to pause and wait for human input
        log_info(AGENT_NAME, "Interrupting workflow for human approval")

        # Create approval request data for the UI
        approval_request = {
            "type": "approval_request",
            "current_agent": "human_approval",
            "workflow_phase": "approval",
            "deployment_summary": state.get(
                "deployment_summary", "Infrastructure deployment ready"
            ),
        }

        # This will pause the workflow and wait for human input
        log_info(
            AGENT_NAME,
            "Calling interrupt() - will pause or return resume value",
        )
        approval_response = interrupt(str(approval_request))
        log_info(AGENT_NAME, f"interrupt() returned: {approval_response}")

        # Use LLM to analyze the human response for approval
        approval_received = analyze_approval_response(approval_response)

        log_info(
            AGENT_NAME,
            f"Human response: {approval_response}, approval_received: {approval_received}",
        )

    log_agent_complete(
        AGENT_NAME,
        f"Approval {'granted' if approval_received else 'denied'}",
    )

    return {
        **state,
        "current_agent": "human_approval",
        "approval_received": approval_received,
    }


def analyze_approval_response(approval_response: str) -> bool:
    """Analyze human approval response using LLM."""

    # Use LLM to analyze the response
    try:
        approval_prompt = template_manager.get_prompt(
            "approval_detection",
            conversation_context=f"User response: {approval_response}",
        )

        llm_response = make_llm_call(approval_prompt, approval_response).strip().upper()

        log_info(
            AGENT_NAME,
            f"LLM response: '{llm_response}'",
        )

        if "APPROVED" in llm_response:
            log_info(AGENT_NAME, "LLM detected approval")
            return True
        if "DENIED" in llm_response:
            log_info(AGENT_NAME, "LLM detected denial")
            return False
        # UNCLEAR or any other response - default to no approval for safety
        log_info(
            AGENT_NAME,
            "LLM response unclear, defaulting to no approval",
        )
        return False

    except Exception as e:
        log_info(
            AGENT_NAME,
            f"LLM analysis failed: {e}, defaulting to no approval",
        )
        return False
