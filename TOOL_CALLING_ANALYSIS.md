# Analysis: Why LLM Isn't Calling Provider Search Tool

## Problem
The LLM is asking for more information and suggesting workflows instead of immediately calling the `search_providers_by_zip` tool when users ask to find providers.

## Root Causes Identified

### 1. **Function Description Not Directive Enough** (Line 67 in orchestrator.py)
**Current:**
```python
"description": "Search for healthcare providers by ZIP code. Use this when the user asks about finding doctors, providers, or healthcare services. The ZIP code will be automatically extracted from the patient's health records if available, or you can use a ZIP code provided by the user."
```

**Issues:**
- Says "Use this when..." which is suggestive, not imperative
- Doesn't say "IMMEDIATELY" or "ALWAYS"
- Doesn't emphasize that this should be the FIRST action
- The LLM interprets this as optional guidance rather than a required action

**Fix Needed:**
- Make it more directive: "IMMEDIATELY search for providers when the user asks about finding doctors, providers, or healthcare services. Do not ask for preferences or additional information first - call this tool right away."
- Emphasize that ZIP code is already available from FHIR data

### 2. **System Prompt Encourages Question-Asking** (Line 27 in prompts.py)
**Current:**
```
- Ask clarifying questions when needed
```

**Issue:**
- This instruction encourages the LLM to ask questions BEFORE taking action
- Conflicts with the need to immediately use the tool
- The LLM prioritizes "ask clarifying questions" over "use tool"

**Fix Needed:**
- Add explicit instruction: "When users ask about finding providers, IMMEDIATELY use the search_providers_by_zip tool. Search first, then provide results and ask for preferences if needed."
- Clarify that tool usage should come before asking questions for provider searches

### 3. **Missing Explicit Tool Usage Directive in System Prompt**
**Current System Prompt:**
- Mentions provider search capability but doesn't explicitly instruct to USE the tool
- No clear directive about when to call tools vs. ask questions

**Fix Needed:**
- Add a section: "TOOL USAGE: When users ask about finding providers, immediately call the search_providers_by_zip tool. The tool will automatically use the patient's ZIP code from their health records. Do not ask for preferences or ZIP code first - search immediately and then refine based on results."

### 4. **Tool Choice Setting** (Line 185 in orchestrator.py)
**Current:**
```python
api_params["tool_choice"] = "auto"  # Let the model decide when to use tools
```

**Issue:**
- "auto" means the model decides, and it's being too conservative
- The model might think it needs more information before using the tool

**Potential Fix:**
- Could try "required" for specific cases, but that might be too aggressive
- Better to fix the description and system prompt first

### 5. **Function Parameter Description** (Line 73 in orchestrator.py)
**Current:**
```python
"description": "ZIP code to search for. If not provided, the tool will try to extract it from the patient's health records. If the user provides a ZIP code, use that value. Example: '02142' or '90210'"
```

**Issue:**
- Says "If not provided" which might make the LLM think it needs to provide it
- Doesn't emphasize that the tool handles ZIP extraction automatically

**Fix Needed:**
- Clarify: "Optional. The tool automatically extracts ZIP code from patient's FHIR data. Only provide this if the user explicitly gives a different ZIP code."

## Recommended Fixes

### Fix 1: Update Function Description (orchestrator.py)
```python
"description": "IMMEDIATELY search for healthcare providers when the user asks about finding doctors, providers, or healthcare services. This tool automatically extracts the patient's ZIP code from their health records - you do NOT need to ask for it. Call this tool right away without asking for preferences or additional information first. After getting results, you can then ask about preferences to help narrow down options."
```

### Fix 2: Update System Prompt (prompts.py)
Add to SYSTEM_PROMPT:
```
TOOL USAGE RULES:
- When users ask about finding providers, doctors, or healthcare services, IMMEDIATELY call the search_providers_by_zip tool
- Do NOT ask for preferences, ZIP code, or provider type first - search immediately
- The tool automatically uses the patient's ZIP code from their health records
- After getting search results, you can then ask about preferences to help narrow down
- For other topics, ask clarifying questions when needed, but for provider searches, use the tool first
```

### Fix 3: Update Function Parameter Description
```python
"zip_code": {
    "type": "string",
    "description": "Optional. Usually leave empty - the tool automatically extracts ZIP code from patient's FHIR data. Only provide this if the user explicitly specifies a different ZIP code than what's in their records."
}
```

### Fix 4: Consider More Directive Tool Choice (Optional)
For provider search specifically, could add logic to detect provider-related queries and set `tool_choice` to be more directive, but this might be over-engineering. Better to fix the prompts first.

## Summary

The main issue is that the LLM is being too cautious and asking questions first because:
1. The function description is suggestive, not imperative
2. The system prompt encourages question-asking
3. There's no explicit instruction to use tools BEFORE asking questions for provider searches

The fix is to make the instructions more directive and explicit about when to use the tool immediately.

