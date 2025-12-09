#!/usr/bin/env python3
"""
Simple example of using search_trials_tool with ChatGPT (OpenAI).
"""

import json
import os
from openai import OpenAI
from search_trials_tool import search_trials_tool

# Load tool definitions
with open("tools.json", "r") as f:
    tools = json.load(f)

# Initialize ChatGPT client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not client.api_key:
    print("ERROR: Please set OPENAI_API_KEY environment variable")
    print("Example: export OPENAI_API_KEY=sk-...")
    exit(1)


def chat_with_chatgpt(user_message: str):
    """
    Chat with ChatGPT, handling tool calls automatically.
    
    Args:
        user_message: The user's message/question
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that helps users find clinical "
                "trials. When users ask about trials, use the search_trials "
                "tool to find relevant information. Provide clear, helpful "
                "responses based on the trial data."
            )
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    # Keep chatting until we get a final response (no more tool calls)
    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        # Call ChatGPT
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo" for faster/cheaper
            messages=messages,
            tools=tools,
        )

        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        # If no tool calls, we're done - return the response
        if not assistant_message.tool_calls:
            return assistant_message.content

        # Execute tool calls
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            print(f"\n🔍 Searching for: {function_args.get('queryText', 'N/A')}")

            try:
                # Execute the tool
                tool_result = search_trials_tool(**function_args)

                # Add tool result back to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(tool_result),
                })

            except Exception as e:
                # Handle errors
                error_msg = f"Error: {str(e)}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": error_msg,
                })

        iteration += 1

    return "Maximum iterations reached. Please try again."


def main():
    """Interactive chat with ChatGPT."""
    print("=" * 60)
    print("ChatGPT Clinical Trial Search Assistant")
    print("=" * 60)
    print("\nAsk me about clinical trials! (Type 'quit' to exit)\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        print("\n🤖 ChatGPT: ", end="", flush=True)
        response = chat_with_chatgpt(user_input)
        print(response)
        print()


if __name__ == "__main__":
    main()

