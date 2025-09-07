"""MCP utilities for agent operations using Python MCP package."""

import json
from typing import Any, Callable, Dict, List, Tuple

from langchain.evaluation import JsonSchemaEvaluator

from ..logging_system import log_info, log_warning
from .mcp_utils import MCPClient
from .utils import load_agent_response_schema, make_structured_llm_call


async def agent_react_step(
    mcp_client: MCPClient,
    system_prompt: str,
    conversation_history: List[str],
    agent_name: str,
    schema: Dict[str, Any] = None,
) -> Tuple[str, str | None]:
    """Execute a ReAct loop with an MCP client and additional tools."""

    # Load schema if not provided
    if schema is None:
        schema = load_agent_response_schema()
    evaluator = JsonSchemaEvaluator()

    async with mcp_client.session() as session:

        # start ReAct loop
        while True:

            # get structured LLM response
            user_message = "\n\n###\n\n".join(conversation_history)

            response_dict = make_structured_llm_call(
                system_prompt, user_message, schema=schema
            )

            # validate response against schema
            validation_result = evaluator.evaluate_strings(
                prediction=json.dumps(response_dict), reference=schema
            )

            if not validation_result.get("score", 0):
                # Add validation error to conversation for agent feedback
                error_msg = (
                    "Invalid JSON schema format. Please ensure your response follows "
                    "the required schema with 'answer', 'tool_calls', or 'routing' fields. "
                    f"Error: {validation_result.get('reasoning', 'Schema validation failed')}"
                )
                conversation_history.append(f"System: {error_msg}")
                log_warning(agent_name, f"Schema validation failed: {response_dict}")
                continue

            # check if reasoning was given
            if response_dict.get("reasoning"):
                reasoning = response_dict["reasoning"]
                log_info(agent_name, f"Reasoning: {reasoning[:200]}...")
                conversation_history.append(f"{agent_name} Reasoning: {reasoning}")

            # check if agent wants to use tools
            if response_dict.get("tool_calls"):
                for tool_call in response_dict["tool_calls"]:
                    tool_name = tool_call["tool_name"]
                    arguments = tool_call["arguments"]

                    log_info(
                        agent_name,
                        f"Calling tool: {tool_name} with args: {str(arguments)[:200]}...",
                    )
                    tool_result = await mcp_client.call_tool(
                        session, tool_name, arguments
                    )
                    log_info(agent_name, f"Tool Result: {str(tool_result)[:200]}...")

                    # Add tool call and result to conversation
                    conversation_history.append(f"Tool Call: {tool_name}({arguments})")
                    conversation_history.append(f"Tool Result: {tool_result}")

            else:
                # No tool calls, check if agent provided an answer
                if response_dict.get("answer"):
                    if response_dict.get("routing", None):
                        return response_dict["answer"], response_dict["routing"]
                    return response_dict["answer"], None
                # No answer or tool calls, provide feedback
                feedback_msg = (
                    "Please provide either an 'answer' to complete the task or "
                    "'tool_calls' to continue with tool execution."
                )
                conversation_history.append(f"System: {feedback_msg}")


class ToolClient:
    """Simple tool client for non-MCP tools that mimics MCP client interface."""

    def __init__(self, tools: List[Dict[str, Any]], tool_executor: Callable):
        """Initialize with tools and executor function."""
        self.tools = tools
        self.tool_executor = tool_executor

    def session(self):
        """Mock session context manager."""
        return self

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

    async def call_tool(
        self, session, tool_name: str, arguments: Dict[str, Any]
    ) -> str:
        """Execute tool using the provided executor."""
        # session parameter is unused but kept for interface compatibility
        return self.tool_executor(tool_name, arguments)


async def agent_react_step_with_tools(
    tools: List[Dict[str, Any]],
    tool_executor: Callable,
    system_prompt: str,
    conversation_history: List[str],
    agent_name: str,
    schema: Dict[str, Any] = None,
) -> Tuple[str, str | None]:
    """Execute ReAct loop with custom tools (non-MCP)."""

    # Create tool client
    tool_client = ToolClient(tools, tool_executor)

    # Use existing react agent with our tool client
    return await agent_react_step(
        tool_client, system_prompt, conversation_history, agent_name, schema
    )
