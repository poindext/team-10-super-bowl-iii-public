"""
Debug utilities for tracing application flow and state.
"""

import streamlit as st
import json
from typing import Any, Dict


def render_debug_panel():
    """Render a collapsible debug panel in the sidebar showing session state and flow information."""
    with st.sidebar:
        st.markdown("---")
        with st.expander("🔍 Debug Panel", expanded=False):
            st.markdown("### Session State Information")
            
            # Authentication Status
            st.markdown("#### Authentication")
            authenticated = st.session_state.get("authenticated", False)
            st.write(f"**Authenticated:** {authenticated}")
            
            if authenticated:
                mpiid = st.session_state.get("mpiid", "N/A")
                patient_name = st.session_state.get("patient_name", "N/A")
                st.write(f"**MPIID:** {mpiid}")
                st.write(f"**Patient Name:** {patient_name}")
            
            st.divider()
            
            # Session Initialization
            st.markdown("#### Session")
            session_initialized = st.session_state.get("session_initialized", False)
            st.write(f"**Session Initialized:** {session_initialized}")
            
            # Message History
            st.markdown("#### Message History")
            messages = st.session_state.get("messages", [])
            st.write(f"**Message Count:** {len(messages)}")
            
            if messages:
                with st.expander(f"View {len(messages)} Messages"):
                    for i, msg in enumerate(messages):
                        st.markdown(f"**Message {i+1}** ({msg.get('role', 'unknown')}):")
                        st.code(msg.get('content', '')[:200] + ('...' if len(msg.get('content', '')) > 200 else ''))
            
            # FHIR Data Status
            st.markdown("#### FHIR Data")
            fhir_data = st.session_state.get("fhir_data", None)
            if fhir_data:
                st.write("**Status:** ✅ FHIR data loaded")
                try:
                    if isinstance(fhir_data, dict):
                        fhir_keys = list(fhir_data.keys())[:5]
                        st.write(f"**Top-level keys:** {', '.join(fhir_keys)}")
                        if 'entry' in fhir_data:
                            entry_count = len(fhir_data.get('entry', []))
                            st.write(f"**Entries:** {entry_count}")
                    else:
                        st.write(f"**Type:** {type(fhir_data).__name__}")
                except Exception as e:
                    st.write(f"**Error reading FHIR data:** {str(e)}")
            else:
                st.write("**Status:** ❌ No FHIR data loaded")
            
            st.divider()
            
            # LLM Orchestrator Status
            st.markdown("#### LLM Orchestrator")
            orchestrator_initialized = "orchestrator" in st.session_state
            st.write(f"**Initialized:** {orchestrator_initialized}")
            if orchestrator_initialized:
                try:
                    orchestrator = st.session_state.get("orchestrator")
                    if orchestrator:
                        st.write(f"**Model:** {getattr(orchestrator, 'model', 'N/A')}")
                except Exception as e:
                    st.write(f"**Error:** {str(e)}")
            
            st.divider()
            
            # Environment Variables Check (without showing values)
            st.markdown("#### Environment Variables")
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            env_vars = {
                "OPENAI_API_KEY": "✅ Set" if os.getenv("OPENAI_API_KEY") else "❌ Not set",
                "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "Not set"),
                "FHIR_USERNAME": "✅ Set" if os.getenv("FHIR_USERNAME") else "❌ Not set",
                "FHIR_PASSWORD": "✅ Set" if os.getenv("FHIR_PASSWORD") else "❌ Not set",
            }
            
            for key, value in env_vars.items():
                st.write(f"**{key}:** {value}")
            
            st.divider()
            
            # Full Session State (collapsible)
            st.markdown("#### Full Session State")
            with st.expander("View All Session State Keys"):
                session_keys = list(st.session_state.keys())
                st.write(f"**Total keys:** {len(session_keys)}")
                for key in sorted(session_keys):
                    value = st.session_state.get(key)
                    value_type = type(value).__name__
                    value_preview = str(value)[:100] if value is not None else "None"
                    if len(str(value)) > 100:
                        value_preview += "..."
                    st.code(f"{key} ({value_type}): {value_preview}")
            
            st.divider()
            
            # Flow Status
            st.markdown("#### Flow Status")
            flow_steps = {
                "1. Authentication": "✅ Complete" if authenticated else "⏳ Pending",
                "2. Session Init": "✅ Complete" if session_initialized else "⏳ Pending",
                "3. FHIR Fetch": "✅ Complete" if fhir_data else "⏳ Pending",
                "4. LLM Ready": "✅ Ready" if orchestrator_initialized else "⏳ Pending",
                "5. Chat Active": "✅ Active" if len(messages) > 0 else "⏳ Waiting"
            }
            
            for step, status in flow_steps.items():
                st.write(f"**{step}:** {status}")
