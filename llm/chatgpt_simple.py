#!/usr/bin/env python3
"""
Minimal ChatGPT example - single question/answer.
"""

import json
import os
from openai import OpenAI
from search_trials_tool import search_trials_tool

# Setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
with open("tools.json", "r") as f:
    tools = json.load(f)

# Ask ChatGPT a question
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Find clinical trials for diabetes treatment"}
    ],
    tools=tools,
)

message = response.choices[0].message

# Handle tool call if needed
if message.tool_calls:
    for tool_call in message.tool_calls:
        if tool_call.function.name == "search_trials":
            args = json.loads(tool_call.function.arguments)
            result = search_trials_tool(**args)
            
            # Send result back to ChatGPT
            response2 = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": "Find clinical trials for diabetes treatment"},
                    message,
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": "search_trials",
                        "content": json.dumps(result),
                    }
                ],
                tools=tools,
            )
            
            print(response2.choices[0].message.content)
else:
    print(message.content)

