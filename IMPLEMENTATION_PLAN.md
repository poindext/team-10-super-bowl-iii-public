# AI Health Companion - Implementation Plan

## Project Overview
**Role**: Development Manager & Implementation System (Cursor)  
**Type**: Demo application (NOT production healthcare system)  
**Primary User**: Patient (non-technical)

## Design Philosophy (CRITICAL)
- **Capability-Driven, NOT Use-Case-Driven**
- No hardcoded medical logic (e.g., "if diabetes → suggest endocrinologist")
- LLM interprets context and decides actions dynamically
- All flows emerge from reasoning, not rules
- Tools expand capability dynamically

## Tech Stack (From BRD)
- **Chat Interface**: Streamlit.io
- **Language**: Python
- **LLM Provider**: OpenAI
- **External APIs**: 
  - Provider Availability API
  - Clinical Trial Search API
- **Data Format**: FHIR (test data)

## Proposed Folder Structure

```
Team10HealthCompanion/
├── HealthCompanion_BRD.md          # Requirements document
├── IMPLEMENTATION_PLAN.md           # This file
├── README.md                        # Project documentation
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── fhir_test_patients.csv           # Test patient data with MPIIDs and FHIR endpoints
├── src/
│   ├── __init__.py
│   ├── main.py                      # Streamlit entry point
│   ├── auth/
│   │   ├── __init__.py
│   │   └── login.py                 # Minimal login UI
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # LLM reasoning engine
│   │   └── prompts.py               # System prompts, safety guardrails & emergency detection
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py                  # Base tool interface
│   │   ├── fhir_fetch.py            # FHIR data fetching tool (executed immediately after login)
│   │   ├── provider_search.py       # Provider Availability tool
│   │   └── clinical_trial_search.py # Clinical Trial Search tool
│   ├── chat/
│   │   ├── __init__.py
│   │   ├── session.py               # Session memory management
│   │   └── ui.py                    # Streamlit chat UI components
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── fhir_minimizer.py        # FHIR data minimization utilities
│   │   ├── patient_data.py          # Patient data utilities (CSV reader)
│   │   └── debug.py                 # Debug panel for development
│   └── yaml/
│       ├── FHIR_SERVICE_CONTRACT.yaml              # OpenAPI 3.0 contract for FHIR service
│       └── TRIAL_SEARCH_SERVICE_CONTRACT.yaml      # OpenAPI 3.0 contract for clinical trial search service
```

## Core Components Architecture

### 1. Authentication Module (`src/auth/`)
- **Purpose**: Minimal login UI before chat access
- **Functionality**: 
  - Simple hardcoded username/password for demo
  - **Hardcoded MPI ID mapping**: Login credentials map to MPIID from `fhir_test_patients.csv`
  - **Test Patient**: Steve Burns (MPIID: 100000009) - default test patient
  - Session initialization with associated MPIID
  - **Immediately after login**: Triggers FHIR fetch tool with mapped MPIID
- **Implementation Note**: 
  - For demo, any valid login maps to test patient MPIID: 100000009 (Steve Burns)
  - FHIR endpoint is retrieved from CSV file based on MPIID

### 2. FHIR Fetch Tool (`src/tools/fhir_fetch.py`)
- **Purpose**: Fetch patient-specific FHIR test data (executed immediately after login)
- **Data Source**: 
  - Reads patient endpoints from `fhir_test_patients.csv` (MPIID, Name, Endpoint)
  - Uses MPIID from authenticated session to lookup endpoint
  - Endpoint format: `http://ec2-98-82-129-136.compute-1.amazonaws.com/ucr/csp/healthshare/hsods/fhir/r4/Patient/{MPIID}/$everything`
- **Authentication**: 
  - Uses Basic Authentication (username/password from environment variables)
  - Credentials: `FHIR_USERNAME` and `FHIR_PASSWORD` from `.env`
- **Critical Flow**:
  - **First action** after successful login
  - Retrieves MPIID from session
  - Looks up endpoint from CSV file
  - Makes authenticated GET request to FHIR endpoint
  - If FHIR fetch **succeeds**: Proceed to chat interface with FHIR data in context
  - If FHIR fetch **fails**: End flow, display error message asking user to contact technical staff
- **Data Format**: Minimized FHIR resources (JSON) passed directly to LLM
- **Minimization**: FHIR data is minimized once at load time to reduce token usage (50-70% reduction) while preserving all clinical information
- **No parsing**: LLM receives minimized raw FHIR resources and reasons over them directly
- **Data Types** (as minimized FHIR resources):
  - Diagnoses
  - Medications
  - Observations
  - Encounters

### 3. LLM Orchestrator (`src/llm/orchestrator.py`)
- **Purpose**: Core reasoning engine
- **Responsibilities**:
  - Interprets user intent
  - Reasons over **raw FHIR resources** (no pre-processing/parsing)
  - Decides when to ask questions vs. provide information
  - Chooses which tools to invoke (if any)
  - Maintains conversation flow organically
- **Key Principle**: No hardcoded decision trees
- **FHIR Context**: Minimized raw FHIR resources included in system prompt/context (minimized once at load time, cached in session)

### 4. Tools Ecosystem (`src/tools/`)
- **Design**: Modular, optional, user-consent driven
- **Tools**:
  - **FHIR Fetch**: Executed automatically after login (not user-consent driven)
  - **Provider Search**: External API integration for provider availability
  - **Clinical Trial Search**: Personalized trial search using FHIR data
- **Principle**: Adding new tools requires NO redesign of conversation flows

### 5. Emergency Handling (`src/llm/prompts.py`)
- **Purpose**: Detect emergency language
- **Location**: Emergency detection functions (`check_emergency()`, `get_emergency_response()`) are in `src/llm/prompts.py`
- **Behavior**: 
  - Stop conversation immediately
  - Display: "This may be an emergency. Please call 911 immediately."
  - No continued assistance or tool usage

### 6. Safety & Guardrails (`src/llm/prompts.py`)
- **Required Disclaimers** (when discussing conditions/diagnoses):
  - "I'm not a medical professional."
  - "This information is for awareness only."
  - "Please discuss with a clinician."
- **Tone**: Calm, supportive, non-judgmental, non-alarmist
- **Avoid**: Certainty in clinical matters

### 7. Chat Interface (`src/chat/`)
- **Framework**: Streamlit
- **Features**:
  - Natural conversation UI (no menus, no decision trees)
  - Session memory
  - Message history display
  - Tool invocation indicators

## Implementation Phases

### Phase 1: Project Setup
- [x] Read and understand BRD
- [x] Setup folder structure
- [x] Initialize Python virtual environment
- [x] Connect to existing git repository
- [x] Create requirements.txt with dependencies
- [x] Setup .env.example for configuration

### Phase 2: Core Infrastructure
- [ ] Implement authentication module (minimal login with hardcoded credentials)
- [ ] Implement MPIID mapping: map login to test patient MPIID (default: 100000009 - Steve Burns)
- [ ] Setup Streamlit app structure
- [ ] Create base LLM orchestrator with OpenAI integration
- [ ] Implement session memory management
- [ ] Setup basic chat UI in Streamlit

### Phase 3: FHIR Integration (as Tool)
- [ ] Create CSV reader utility to load `fhir_test_patients.csv`
- [ ] Create FHIR fetch tool (`src/tools/fhir_fetch.py`)
- [ ] Implement endpoint lookup from CSV based on MPIID
- [ ] Implement Basic Authentication using FHIR_USERNAME and FHIR_PASSWORD
- [ ] Implement automatic FHIR fetch immediately after login
- [ ] Implement error handling: if FHIR fetch fails, end flow with technical support message
- [ ] Integrate raw FHIR resources into LLM context (no parsing)
- [ ] Test FHIR fetch success and failure scenarios

### Phase 4: Safety & Emergency Handling
- [ ] Implement emergency language detection
- [ ] Create safety guardrails and disclaimers
- [ ] Integrate disclaimers into LLM responses
- [ ] Test emergency escalation flow

### Phase 5: Tools Integration
- [ ] Create base tool interface
- [ ] Implement FHIR fetch tool (Phase 3)
- [ ] Implement Provider Availability tool
- [ ] Implement Clinical Trial Search tool
- [ ] Integrate tool invocation into LLM orchestrator
- [ ] Ensure user consent flow for tool usage (except FHIR fetch which is automatic)

### Phase 6: Testing & Refinement
- [ ] Test demo scenarios from BRD
- [ ] Verify capability-driven behavior (no hardcoded flows)
- [ ] Test emergency handling
- [ ] Verify safety disclaimers appear appropriately
- [ ] Test tool invocations

## Key Dependencies (Initial Estimate)

```
streamlit>=1.28.0
openai>=1.0.0
python-dotenv>=1.0.0
requests>=2.31.0
# Note: No FHIR parsing library needed - raw FHIR JSON passed directly to LLM
```

## Environment Variables Needed

```
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.1  # Primary model (verify model availability)

# FHIR Server Authentication (Basic Auth)
FHIR_USERNAME=your_fhir_username
FHIR_PASSWORD=your_fhir_password

# Provider Availability API (Dummy/stub endpoint for initial build)
PROVIDER_API_URL=provider_availability_api_url
PROVIDER_API_KEY=provider_api_key  # if needed

# Clinical Trial Search API (Will be provided later)
CLINICAL_TRIAL_API_URL=clinical_trial_api_url
CLINICAL_TRIAL_API_KEY=clinical_trial_api_key  # if needed
```

**Note**: FHIR endpoints are read from `fhir_test_patients.csv` file, not from environment variables. The CSV contains MPIID, Name, and Endpoint URL for each test patient.

## Critical Implementation Rules

1. **NO hardcoded medical logic** - All decisions through LLM reasoning
2. **NO predefined flows** - Conversation emerges organically
3. **NO menus or decision trees** - Natural conversation only
4. **Always include disclaimers** when discussing medical conditions
5. **Emergency detection** must stop conversation immediately
6. **Tools are optional** - User consent required (except FHIR fetch which is automatic after login)
7. **FHIR fetch is mandatory** - Must succeed after login, or flow ends with technical support message
8. **FHIR minimization** - FHIR data is minimized once at load time and cached in session to reduce token usage
9. **Minimized FHIR resources** - No parsing, minimized FHIR JSON passed directly to LLM for reasoning
9. **FHIR data informs** but doesn't dictate responses
10. **MPIID mapping** - Login maps to hardcoded MPIID (100000009 - Steve Burns) for demo purposes
11. **FHIR endpoints** - Retrieved from `fhir_test_patients.csv` based on MPIID

## Questions for Clarification

1. **Git Repository**: What is the URL of the existing git repository? https://github.com/poindext/team-10-super-bowl-iii-public
2. **FHIR Data Source**: 
   - Will we use a FHIR test server, or local test data files? - ✅ We will connect to a FHIR test server using endpoints from `fhir_test_patients.csv`
   - What format will the FHIR data be in (JSON, XML)? ✅ JSON
   - What is the FHIR server endpoint/API for fetching patient data? ✅ Endpoints are in `fhir_test_patients.csv` file. Format: `http://ec2-98-82-129-136.compute-1.amazonaws.com/ucr/csp/healthshare/hsods/fhir/r4/Patient/{MPIID}/$everything`
   - Authentication: ✅ Basic Authentication (username/password) - credentials stored in environment variables
   - Test Patient: ✅ Steve Burns (MPIID: 100000009) - default test patient for hardcoded login
3. **External APIs**: 
   - Do you have the actual API endpoints and authentication details for Provider Availability and Clinical Trial Search? - I have the URL for Clinical Trial API. Use a dummy API call for provider directory. 
   - Are there API documentation or test credentials available? - We will provide those details later. 
4. **Authentication**: 
   - For the demo login, should we use a simple hardcoded user/password, or integrate with a specific auth system? ✅ Hardcoded values for now
   - MPIID Mapping: ✅ Login credentials map to hardcoded MPIID (100000009 - Steve Burns) for demo
   - FHIR Authentication: ✅ Basic Auth using FHIR_USERNAME and FHIR_PASSWORD from environment variables
5. **OpenAI Model**: 
   - Which OpenAI model should we use (GPT-4, GPT-3.5-turbo, etc.)? ✅ GPT-5.1 (currently in use)

## Next Steps

1. Get git repository URL and connect
2. Setup virtual environment and install dependencies
3. Create folder structure
4. Begin Phase 2 implementation

