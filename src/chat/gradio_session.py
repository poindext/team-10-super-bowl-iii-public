"""
Gradio-specific session management - parallel to Streamlit session.py.
Uses Gradio's state management instead of Streamlit's session_state.
"""

from typing import List, Dict, Any, Optional


class GradioSession:
    """Session state manager for Gradio - stores data per user session."""
    
    def __init__(self):
        """Initialize session with default values."""
        self.messages: List[Dict[str, Any]] = []
        self.fhir_data: Optional[Any] = None
        self.minimized_fhir_data: Optional[Any] = None
        self.session_initialized: bool = True
        self.authenticated: bool = False
        self.mpiid: Optional[str] = None
        self.patient_name: Optional[str] = None
        self.orchestrator = None
        self.fhir_fetch_tool = None


def initialize_session(state: GradioSession) -> GradioSession:
    """Initialize session variables if they don't exist."""
    if state is None:
        state = GradioSession()
    
    if not hasattr(state, 'messages') or state.messages is None:
        state.messages = []
    
    if not hasattr(state, 'fhir_data'):
        state.fhir_data = None
    
    if not hasattr(state, 'session_initialized'):
        state.session_initialized = True
    
    return state


def add_message(state: GradioSession, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> GradioSession:
    """
    Add a message to the conversation history.
    
    Args:
        state: Gradio session state
        role: Message role ('user' or 'assistant')
        content: Message content
        metadata: Optional metadata (e.g., tool invocations)
    """
    state = initialize_session(state)
    
    message = {
        "role": role,
        "content": content,
        "metadata": metadata or {}
    }
    state.messages.append(message)
    return state


def get_messages(state: GradioSession) -> List[Dict[str, Any]]:
    """Get all messages in the conversation history."""
    state = initialize_session(state)
    return state.messages if state.messages else []


def clear_messages(state: GradioSession) -> GradioSession:
    """Clear all messages from conversation history."""
    state = initialize_session(state)
    state.messages = []
    return state


def set_fhir_data(state: GradioSession, fhir_data: Any) -> GradioSession:
    """Store FHIR data in session."""
    state = initialize_session(state)
    state.fhir_data = fhir_data
    return state


def get_fhir_data(state: GradioSession) -> Optional[Any]:
    """Get FHIR data from session."""
    state = initialize_session(state)
    return state.fhir_data if hasattr(state, 'fhir_data') else None


def set_minimized_fhir_data(state: GradioSession, minimized_fhir_data: Any) -> GradioSession:
    """Store minimized FHIR data in session."""
    state = initialize_session(state)
    state.minimized_fhir_data = minimized_fhir_data
    return state


def get_minimized_fhir_data(state: GradioSession) -> Optional[Any]:
    """Get minimized FHIR data from session, minimize if not available."""
    state = initialize_session(state)
    
    # Check if minimized version exists
    if hasattr(state, 'minimized_fhir_data') and state.minimized_fhir_data is not None:
        return state.minimized_fhir_data
    
    # If not, minimize the full FHIR data if available
    fhir_data = get_fhir_data(state)
    if fhir_data:
        from src.utils.fhir_minimizer import minimize_fhir_bundle
        if isinstance(fhir_data, dict) and fhir_data.get("resourceType") == "Bundle":
            minimized = minimize_fhir_bundle(fhir_data)
            set_minimized_fhir_data(state, minimized)
            return minimized
    
    return None

