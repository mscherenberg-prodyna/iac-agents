"""Approval handling logic for workflow management."""


def is_approval_message(user_input: str) -> bool:
    """Check if the user input is an approval message."""
    approval_keywords = [
        "yes",
        "approve",
        "approved",
        "proceed",
        "go ahead",
        "deploy",
        "ok",
        "okay",
        "confirm",
        "confirmed",
        "agree",
        "agreed",
        "accept",
    ]

    user_input_lower = user_input.lower().strip()

    # Check for explicit approval keywords
    for keyword in approval_keywords:
        if keyword in user_input_lower:
            return True

    return False
