# AI Health Companion

A patient-facing AI Health Companion demo application that provides natural, conversational health support using LLM reasoning and FHIR data personalization.

## ⚠️ Important Notice

**This is a demo application, NOT a production healthcare system.**

## Project Overview

The AI Health Companion is a capability-driven conversational system that:
- Supports natural, free-flowing conversation
- Uses an LLM as the orchestration engine
- Pulls FHIR test data at login for personalization
- Dynamically chooses actions (explain, ask, suggest, use tools)
- Integrates with external APIs for provider search and clinical trials
- Maintains strong guardrails for safety

## Design Philosophy

**Capability-Driven, NOT Use-Case-Driven**

The system contains NO hardcoded logic. Instead:
- LLM interprets context
- LLM decides what to do next
- Tools expand capability dynamically
- All flows emerge from reasoning, not rules

## Tech Stack

- **Chat Interface**: Streamlit.io
- **Language**: Python 3.9+
- **LLM Provider**: OpenAI (GPT-4)
- **External APIs**: 
  - Provider Availability API (stub/dummy for initial build)
  - Clinical Trial Search API
- **Data Format**: FHIR (JSON)

## Setup

### Prerequisites

- Python 3.9 or higher
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/poindext/team-10-super-bowl-iii-public.git
cd Team10HealthCompanion
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
```

5. Add your API keys and configuration to `.env`

### Running the Application

```bash
streamlit run src/main.py
```

## Project Structure

```
Team10HealthCompanion/
├── src/
│   ├── main.py              # Streamlit entry point
│   ├── auth/                # Authentication module
│   ├── llm/                 # LLM orchestrator and reasoning
│   ├── tools/               # Tool ecosystem (FHIR fetch, Provider Search, Clinical Trials)
│   ├── chat/                # Chat interface and session management
│   └── utils/               # Safety guardrails and utilities
├── tests/                   # Test suite
├── data/                    # Test data
└── docs/                    # Documentation
```

## Key Features

- **Natural Conversation**: No menus, no decision trees, organic flow
- **FHIR Integration**: Automatic fetch after login, raw FHIR resources passed to LLM
- **Dynamic Tool Invocation**: Provider search and clinical trial discovery
- **Safety Guardrails**: Emergency detection, required disclaimers
- **Session Memory**: Maintains conversation context

## Critical Implementation Rules

1. **NO hardcoded medical logic** - All decisions through LLM reasoning
2. **NO predefined flows** - Conversation emerges organically
3. **FHIR fetch is mandatory** - Must succeed after login, or flow ends
4. **Raw FHIR resources** - No parsing, pass directly to LLM
5. **Emergency detection** - Stops conversation immediately
6. **Always include disclaimers** when discussing medical conditions

## Development

See `IMPLEMENTATION_PLAN.md` for detailed implementation phases and architecture.

## Documentation

- `HealthCompanion_BRD.md` - Business Requirements Document
- `IMPLEMENTATION_PLAN.md` - Implementation plan and architecture

## License

[To be determined]

