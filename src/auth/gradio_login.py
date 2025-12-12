"""
Gradio-specific authentication module.
Parallel to Streamlit login.py but uses Gradio's state management.
"""

from typing import Optional
from src.chat.gradio_session import GradioSession

# Hardcoded demo credentials
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"

# Hardcoded MPIID mapping - all logins map to test patient Steve Burns
DEFAULT_MPIID = "100000009"
DEFAULT_PATIENT_NAME = "Steve Burns"


def is_authenticated(state: GradioSession) -> bool:
    """Check if user is authenticated in current session."""
    if state is None:
        return False
    return getattr(state, 'authenticated', False)


def get_mpiid(state: GradioSession) -> Optional[str]:
    """Get the MPIID associated with the current session."""
    if state is None:
        return None
    return getattr(state, 'mpiid', None)


def get_patient_name(state: GradioSession) -> Optional[str]:
    """Get the patient name associated with the current session."""
    if state is None:
        return None
    return getattr(state, 'patient_name', None)


def authenticate(state: GradioSession, username: str, password: str) -> tuple[GradioSession, bool]:
    """
    Authenticate user with hardcoded credentials.
    
    Args:
        state: Gradio session state
        username: Username input
        password: Password input
        
    Returns:
        Tuple of (updated state, True if credentials are valid, False otherwise)
    """
    if state is None:
        state = GradioSession()
    
    if username == DEMO_USERNAME and password == DEMO_PASSWORD:
        # Set session state
        state.authenticated = True
        state.mpiid = DEFAULT_MPIID
        state.patient_name = DEFAULT_PATIENT_NAME
        return state, True
    return state, False


def logout(state: GradioSession) -> GradioSession:
    """Clear authentication and session data."""
    if state is None:
        state = GradioSession()
    
    state.authenticated = False
    state.mpiid = None
    state.patient_name = None
    return state

