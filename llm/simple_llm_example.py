#!/usr/bin/env python3
"""
Minimal example showing how to use search_trials_tool with OpenAI.
"""

import json
import os
from openai import OpenAI
from search_trials_tool import search_trials_tool

# Load tool definitions
with open("tools.json", "r") as f:
    tools = json.load(f)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Make a request with tools
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {
            "role": "user",
            "content": "Find me clinical trials for diabetes treatment"
        }
    ],
    tools=tools,
)

message = response.choices[0].message

# Check if the LLM wants to call a tool
if message.tool_calls:
    for tool_call in message.tool_calls:
        if tool_call.function.name == "search_trials":
            # Parse arguments
            args = json.loads(tool_call.function.arguments)
            
            # Call the tool
            result = search_trials_tool(**args)
            
            print("Tool Result:")
            print(json.dumps(result, indent=2))
else:
    print("LLM Response:", message.content)

