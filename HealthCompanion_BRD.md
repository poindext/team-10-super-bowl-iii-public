AI Health Companion — Demo Build Requirements
Business Requirements Document (BRD) for Cursor
Team 10 Solution Planning

1. Purpose
This document defines the business requirements, design principles, scope boundaries, and demo scenarios for the AI Health Companion application.

It serves as the single source of truth for Cursor, which will act as the development manager and implementation system.

⚠️ This is a demo, not a production healthcare system.

The app prioritizes:

High‑quality conversational user experience

LLM reasoning capability

FHIR‑based personalization

Dynamic tool invocation

Strong guardrails for safety

2. Product Overview
What the Product Is
A patient‑facing AI Health Companion that:

Supports natural, free‑flowing conversation

Uses an LLM as the orchestration engine

Pulls FHIR test data at login for personalization

Dynamically chooses actions (explain, ask, suggest, use tools)

Integrates with external APIs for provider search and clinical trials

What It Is Not

Not an emergency triage service

Not a workflow engine

Not a production-ready app

3. Design Philosophy (Critical)
Capability‑Driven, NOT Use‑Case‑Driven
The system must not contain hardcoded logic such as:
“if diabetes → suggest endocrinologist.”

Instead:

LLM interprets context

LLM decides what to do next

Tools expand capability dynamically

All flows emerge from reasoning, not rules

All scenarios provided are illustrative, not prescriptive.

4. Target User
Primary User: Patient

Non‑technical

Seeking clarity, understanding, and support

Unfamiliar with medical workflows and jargon

No caregiver or provider role in MVP.

5. Authentication Requirements
Must log in before accessing the chat

Enables access to patient-specific FHIR test data

Minimal login UI acceptable

6. Conversational Experience Requirements
Experience Characteristics
Organic, natural conversation

No menus

No decision trees

No predefined flows

Supportive, calm, non-alarmist tone

LLM Responsibilities
The LLM orchestrator determines:

What the user means

What matters from FHIR data

Whether to ask more questions

Whether to offer next steps

Whether to invoke a tool

How to phrase information safely

7. FHIR Data Context
LLM May Reason Over
Diagnoses

Medications

Observations

Encounters

Allowed
Personalized insights

Patient-friendly explanations

Suggested next steps

Identifying potential or missed diagnoses, safely framed as:

Observations

Possibilities

Questions to discuss with a clinician

Not Allowed
Definitive diagnosis

Medical treatment decisions

Medication dosing or modification

Required Disclaimers
Whenever insights relate to conditions or diagnoses, the LLM must state:

“I’m not a medical professional.”

“This information is for awareness only.”

“Please discuss with a clinician.”

8. Tools Ecosystem (MVP)
Tools must be:

Modular

Optional

User-consent driven

Invoked only when contextually appropriate

8.1 Provider Availability Tool
External API

Searches providers by specialty

LLM summarizes results conversationally

8.2 Clinical Trial Search Tool
External API

Personalized using FHIR data

Results are informational options

No claim of eligibility

No enrollment actions

Tool Design Principle
Adding new tools must require no redesign of conversation flows.

9. Emergency Handling
If the LLM detects potential emergency language (e.g., severe chest pain):

Stop conversation immediately

Respond with:

“This may be an emergency. Please call 911 immediately.”

No continued assistance

No tool usage

10. Safety & Tone Requirements
Calm

Supportive

Non-judgmental

Non-alarmist

Avoid certainty in clinical matters

Always defer to clinicians

11. MVP Scope (Strict)
Included
Login

Chat interface

LLM reasoning engine

FHIR data personalization

Provider Availability tool

Clinical Trial Search tool

Emergency escalation

Guardrails and disclaimers

Session memory

Excluded
Hardcoded medical logic

Appointment scheduling

Caregiver/provider roles

Analytics

Clinical decision support

Any production-grade guarantees

12. Beyond MVP (Do Not Implement Now)
Additional tools

Multi-user roles

Longitudinal patient journey

HIPAA‑grade compliance

Tracking or analytics

Provider-side portals

13. Demo Scenarios (For Testing Only)
These help Cursor generate test cases.
They MUST NOT be turned into predefined flows.

Scenario 1 — Care Gap Recognition
Trigger: Diagnosis present but no specialist encounter.
LLM suggests specialist exploration → only uses Provider tool if user consents.

Scenario 2 — Medication Explanation
User asks about a medication.
LLM explains simply → includes disclaimers → offers to help prepare questions.

Scenario 3 — Clinical Trial Discovery
User asks about research opportunities.
LLM uses FHIR data → calls Trial Search API → summarizes results clearly.

Scenario 4 — Emergency Escalation
User mentions acute symptoms.
LLM stops normal flow → instructs to call 911 immediately.

14. Demo Goal
Observers should feel:

The assistant is helpful

The LLM is reasoning, not scripted

Tools naturally extend capability

The design is scalable and extensible

15. Tools Selected (Implementation Context)
(Informational only — Cursor handles technical decisions)

Chat Interface
Streamlit.io

Framework for chat UI and demo interface

Programming Language
Python

Primary language for orchestration and tool integration

LLM Provider
OpenAI

Powers the core reasoning engine

External APIs
Provider Availability API

Clinical Trial Search API

Development Environment
Cursor as dev manager + builder

Design Intent
Tools listed above are enablers, not features

System must remain general and tool‑driven, not rule‑driven

End of BRD