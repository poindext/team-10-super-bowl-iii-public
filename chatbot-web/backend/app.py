import os
import json
from typing import Dict, Any, List, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from requests.auth import HTTPBasicAuth

APP_TITLE = "Chatbot Web Backend"

# IRIS endpoint - must be set via environment variable for security
IRIS_ENDPOINT = os.getenv(
    "IRIS_ENDPOINT",
    (
        "http://ec2-98-82-129-136.compute-1.amazonaws.com"
        "/i4h/ctgov/VectorTrialSearch"
    )
)

# OpenAI tool definition (function calling)
TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_trials",
            "description": (
                "Search clinical trials using vector similarity search. "
                "Returns trials matching the query text based on semantic "
                "similarity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "queryText": {
                        "type": "string",
                        "description": "Natural language search text.",
                    },
                    "maxRows": {
                        "type": "integer",
                        "description": "Maximum number of trials to return.",
                    },
                },
                "required": ["queryText"],
            },
        },
    }
]


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None
    maxRows: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    tool_used: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None


def get_iris_auth():
    """Derive auth headers or HTTPBasicAuth from environment variables."""
    username = os.getenv("IRIS_USERNAME")
    password = os.getenv("IRIS_PASSWORD")
    bearer = os.getenv("IRIS_BEARER_TOKEN")
    api_key = os.getenv("IRIS_API_KEY")

    if username and password:
        return HTTPBasicAuth(username, password), {}
    if bearer:
        return None, {"Authorization": f"Bearer {bearer}"}
    if api_key:
        return None, {"X-API-Key": api_key}
    return None, {}


def call_iris_search(query_text: str, max_rows: Optional[int]) -> Any:
    """Call the IRIS VectorTrialSearch endpoint."""
    auth, extra_headers = get_iris_auth()
    payload: Dict[str, Any] = {"queryText": query_text}
    if max_rows is not None:
        payload["maxRows"] = max_rows

    try:
        resp = requests.post(
            IRIS_ENDPOINT,
            json=payload,
            headers=extra_headers,
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"IRIS search failed: {exc}",
        ) from exc


def execute_tool_call(name: str, args: Dict[str, Any]) -> Any:
    if name == "search_trials":
        return call_iris_search(
            query_text=args.get("queryText", ""),
            max_rows=args.get("maxRows"),
        )
    raise ValueError(f"Unknown tool: {name}")


def chat_with_openai(
    user_message: str,
    history: Optional[List[Dict[str, str]]],
    max_rows: Optional[int]
) -> ChatResponse:
    """Handle a single-turn chat with optional tool call execution."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not client.api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not set.",
        )

    messages: List[Dict[str, Any]] = []
    system_prompt = (
        "You are a helpful assistant that can search for clinical trials. "
        "When the user asks about trials, use the search_trials tool to "
        "find relevant matches. Be concise and return key details "
        "(NCTID, title/summary, and any available locations)."
    )
    messages.append({"role": "system", "content": system_prompt})

    if history:
        messages.extend(history)

    # Add user message (include requested maxRows hint in content to guide LLM)
    user_content = user_message
    if max_rows:
        user_content += f" (limit results to about {max_rows})"
    messages.append({"role": "user", "content": user_content})

    # First call - let the model decide to use tools
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    assistant_msg = completion.choices[0].message

    # If no tool calls, return the direct response
    if not assistant_msg.tool_calls:
        return ChatResponse(reply=assistant_msg.content or "")

    # Execute each tool call sequentially (single turn)
    tool_used = None
    tool_args: Optional[Dict[str, Any]] = None
    for tool_call in assistant_msg.tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        tool_used = tool_name
        tool_result = execute_tool_call(tool_name, tool_args)

        # Append tool result so model can craft the final reply
        messages.append(assistant_msg)
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(tool_result),
            }
        )

        # Get final answer after tool result
        final_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        final_msg = final_completion.choices[0].message
        return ChatResponse(
            reply=final_msg.content or "",
            tool_used=tool_used,
            tool_args=tool_args,
        )

    return ChatResponse(reply="No response generated.")


app = FastAPI(title=APP_TITLE)

# CORS configuration - restrict to your domain in production
# Set ALLOWED_ORIGINS environment variable (comma-separated) or defaults to "*"
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    return chat_with_openai(req.message, req.history, req.maxRows)
