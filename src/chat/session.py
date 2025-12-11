"""
Session memory management for chat conversations.
"""

import streamlit as st
from typing import List, Dict, Any, Optional


def initialize_session():
    """Initialize session state variables if they don't exist."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "fhir_data" not in st.session_state:
        st.session_state.fhir_data = None
    
    if "session_initialized" not in st.session_state:
        st.session_state.session_initialized = True


def add_message(role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Add a message to the conversation history.
    
    Args:
        role: Message role ('user' or 'assistant')
        content: Message content
        metadata: Optional metadata (e.g., tool invocations)
    """
    initialize_session()
    
    message = {
        "role": role,
        "content": content,
        "metadata": metadata or {}
    }
    st.session_state.messages.append(message)


def get_messages() -> List[Dict[str, Any]]:
    """Get all messages in the conversation history."""
    initialize_session()
    return st.session_state.messages


def clear_messages():
    """Clear all messages from conversation history."""
    if "messages" in st.session_state:
        st.session_state.messages = []


def set_fhir_data(fhir_data: Any):
    """Store FHIR data in session state."""
    initialize_session()
    st.session_state.fhir_data = fhir_data


def get_fhir_data() -> Optional[Any]:
    """Get FHIR data from session state."""
    initialize_session()
    return st.session_state.fhir_data


def set_minimized_fhir_data(minimized_fhir_data: Any):
    """Store minimized FHIR data in session."""
    initialize_session()
    st.session_state.minimized_fhir_data = minimized_fhir_data


def get_minimized_fhir_data() -> Optional[Any]:
    """Get minimized FHIR data from session, minimize if not available."""
    initialize_session()
    
    # Check if minimized version exists
    if "minimized_fhir_data" in st.session_state and st.session_state.minimized_fhir_data is not None:
        return st.session_state.minimized_fhir_data
    
    # If not, minimize the full FHIR data if available
    fhir_data = get_fhir_data()
    if fhir_data:
        from src.utils.fhir_minimizer import minimize_fhir_bundle
        if isinstance(fhir_data, dict) and fhir_data.get("resourceType") == "Bundle":
            minimized = minimize_fhir_bundle(fhir_data)
            set_minimized_fhir_data(minimized)
            return minimized
    
    return None

