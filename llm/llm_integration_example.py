#!/usr/bin/env python3
"""
Example integration of search_trials_tool with an LLM (OpenAI).

This demonstrates how to:
1. Load tool definitions
2. Register tools with the LLM
3. Handle function calls
4. Execute tools and return results
"""

import json
import os
from typing import Dict, Any, List
from openai import OpenAI
from search_trials_tool import search_trials_tool


# Tool registry - maps tool names to their implementation functions
TOOL_REGISTRY = {
    "search_trials": search_trials_tool,
}


def load_tools() -> List[Dict[str, Any]]:
    """Load tool definitions from tools.json."""
    tools_path = os.path.join(os.path.dirname(__file__), "tools.json")
    with open(tools_path, "r") as f:
        return json.load(f)


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Execute a tool by name with the given arguments.

    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments to pass to the tool

    Returns:
        Result from the tool execution
    """
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")

    tool_func = TOOL_REGISTRY[tool_name]
    return tool_func(**arguments)


def chat_with_llm(
    messages: List[Dict[str, str]],
    tools: List[Dict[str, Any]],
    model: str = "gpt-4",
    max_iterations: int = 10
) -> str:
    """
    Chat with an LLM that can use tools.

    Args:
        messages: Conversation history
        tools: List of tool definitions
        model: OpenAI model to use
        max_iterations: Maximum number of tool-calling iterations

    Returns:
        Final response from the LLM
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if not client.api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Set it with: export OPENAI_API_KEY=your_key"
        )

    iteration = 0
    while iteration < max_iterations:
        # Call the LLM with tools
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",  # Let the model decide when to use tools
        )

        # Get the assistant's message
        assistant_message = response.choices[0].message
        messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in (assistant_message.tool_calls or [])
            ]
        })

        # If no tool calls, we're done
        if not assistant_message.tool_calls:
            return assistant_message.content or ""

        # Execute tool calls
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            print(f"\n🔧 Calling tool: {function_name}")
            print(f"   Arguments: {function_args}")

            try:
                # Execute the tool
                tool_result = execute_tool(function_name, function_args)

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(tool_result, indent=2),
                })

                print(f"✓ Tool executed successfully")

            except Exception as e:
                # Handle tool execution errors
                error_msg = f"Error executing {function_name}: {str(e)}"
                print(f"✗ {error_msg}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": error_msg,
                })

        iteration += 1

    return "Maximum iterations reached"


def main():
    """Example usage of the LLM integration."""
    print("=" * 60)
    print("LLM Integration Example - Clinical Trial Search")
    print("=" * 60)

    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  ERROR: OPENAI_API_KEY not set!")
        print("Set it with: export OPENAI_API_KEY=your_key")
        return

    # Load tool definitions
    print("\n📋 Loading tool definitions...")
    tools = load_tools()
    print(f"✓ Loaded {len(tools)} tool(s)")

    # Example conversation
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that can search for clinical "
                "trials. When users ask about trials, use the search_trials "
                "tool to find relevant information."
            )
        },
        {
            "role": "user",
            "content": "Find me clinical trials for diabetes treatment"
        }
    ]

    print("\n💬 Starting conversation with LLM...")
    print(f"User: {messages[-1]['content']}")

    # Chat with LLM
    response = chat_with_llm(messages, tools)

    print(f"\n🤖 Assistant: {response}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

