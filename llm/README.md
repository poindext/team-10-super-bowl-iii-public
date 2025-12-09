# ChatGPT Integration for Clinical Trial Search

This directory contains tools and integration code for using the IRIS VectorTrialSearch REST API with ChatGPT (OpenAI).

## Files

- **`search_trials_tool.py`** - The main tool implementation that calls the REST API
- **`tools.json`** - Tool definition in OpenAI function calling format
- **`chatgpt_example.py`** - Interactive ChatGPT chat example (recommended)
- **`chatgpt_simple.py`** - Minimal single-question example
- **`test_search_trials.py`** - Simple test script
- **`test_search_trials_unit.py`** - Unit tests with mocking

## Setup

### 1. Create Virtual Environment (Recommended for Homebrew Python)

If you're using Homebrew Python (which is externally managed), create a virtual environment:

```bash
cd llm
python3 -m venv venv
source venv/bin/activate
python3 -m pip install openai requests
```

**Note:** The virtual environment is already created and packages are installed! Just activate it:

```bash
cd llm
source venv/bin/activate
# Or use the helper script:
source activate.sh
```

### 2. Set Environment Variables

Set your authentication credentials for the IRIS REST API:

```bash
# Option 1: Basic Authentication
export IRIS_USERNAME=your_username
export IRIS_PASSWORD=your_password

# Option 2: Bearer Token
export IRIS_BEARER_TOKEN=your_token

# Option 3: API Key
export IRIS_API_KEY=your_api_key
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY=your_openai_key
```

## Quick Start with ChatGPT

### 1. Activate Virtual Environment

```bash
cd llm
source venv/bin/activate
# Or: source activate.sh
```

### 2. Set Environment Variables

```bash
# Your OpenAI API key (required)
export OPENAI_API_KEY=sk-your-key-here

# IRIS REST API authentication (choose one):
export IRIS_USERNAME=your_username
export IRIS_PASSWORD=your_password
# OR
export IRIS_BEARER_TOKEN=your_token
# OR
export IRIS_API_KEY=your_api_key
```

### 3. Run the ChatGPT Example

**Make sure the virtual environment is activated first!**

**Interactive chat mode** (recommended):
```bash
cd llm
source venv/bin/activate  # If not already activated
python3 chatgpt_example.py
```

This starts an interactive chat where you can ask questions like:
- "Find clinical trials for diabetes treatment"
- "Search for cancer trials"
- "What trials are available for heart disease?"

**Single question mode**:
```bash
python chatgpt_simple.py
```

## Usage

### Test the Tool Directly

Test the REST API connection:

```bash
python test_search_trials.py
```

### Using ChatGPT in Your Own Code

Here's a minimal example:

```python
from openai import OpenAI
import json
from search_trials_tool import search_trials_tool

# Load tools
with open("tools.json") as f:
    tools = json.load(f)

# Initialize ChatGPT
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ask a question
response = client.chat.completions.create(
    model="gpt-4",  # or "gpt-3.5-turbo"
    messages=[
        {"role": "user", "content": "Find trials for diabetes"}
    ],
    tools=tools
)

# Handle tool calls
message = response.choices[0].message
if message.tool_calls:
    for tool_call in message.tool_calls:
        if tool_call.function.name == "search_trials":
            args = json.loads(tool_call.function.arguments)
            result = search_trials_tool(**args)
            
            # Send result back to ChatGPT for final response
            response2 = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": "Find trials for diabetes"},
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
```

## Tool Definition Format

The tool follows OpenAI's function calling format:

```json
{
  "type": "function",
  "function": {
    "name": "search_trials",
    "description": "...",
    "parameters": {
      "type": "object",
      "properties": {
        "queryText": {"type": "string", "description": "..."},
        "maxRows": {"type": "integer", "description": "..."}
      },
      "required": ["queryText"]
    }
  }
}
```

## Authentication Methods

The tool supports three authentication methods (in priority order):

1. **Basic Auth**: `IRIS_USERNAME` + `IRIS_PASSWORD`
2. **Bearer Token**: `IRIS_BEARER_TOKEN`
3. **API Key**: `IRIS_API_KEY` (sent in `X-API-Key` header)

Only one method needs to be configured. The tool will automatically detect and use the first available method.

## Testing

Run unit tests:

```bash
pytest test_search_trials_unit.py -v
```

Run integration test:

```bash
python test_search_trials.py
```

## Troubleshooting

### Authentication Errors

- Ensure environment variables are set correctly
- Check that only one authentication method is configured
- Verify credentials are valid

### API Connection Errors

- Check that the endpoint URL is correct
- Verify network connectivity
- Check firewall settings

### LLM Integration Issues

- Ensure `OPENAI_API_KEY` is set
- Verify `tools.json` is valid JSON
- Check that tool function names match between `tools.json` and `TOOL_REGISTRY`

