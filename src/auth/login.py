"""
Authentication module for minimal login UI.
Hardcoded credentials for demo purposes.
"""

import streamlit as st


# Hardcoded demo credentials
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"

# Hardcoded MPIID mapping - all logins map to test patient Marla Gonzalez
DEFAULT_MPIID = "100000010"
DEFAULT_PATIENT_NAME = "Marla Gonzalez"


def is_authenticated():
    """Check if user is authenticated in current session."""
    return st.session_state.get("authenticated", False)


def get_mpiid():
    """Get the MPIID associated with the current session."""
    return st.session_state.get("mpiid", None)


def get_patient_name():
    """Get the patient name associated with the current session."""
    return st.session_state.get("patient_name", None)


def authenticate(username: str, password: str) -> bool:
    """
    Authenticate user with hardcoded credentials.
    
    Args:
        username: Username input
        password: Password input
        
    Returns:
        True if credentials are valid, False otherwise
    """
    if username == DEMO_USERNAME and password == DEMO_PASSWORD:
        # Set session state
        st.session_state.authenticated = True
        st.session_state.mpiid = DEFAULT_MPIID
        st.session_state.patient_name = DEFAULT_PATIENT_NAME
        return True
    return False


def show_login_page():
    """
    Display the login page UI.
    Returns True if login successful, False otherwise.
    """
    st.title("AI Health Companion")
    st.markdown("### Please log in to continue")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        submit_button = st.form_submit_button("Log In", use_container_width=True)
        
        if submit_button:
            if authenticate(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")
    
    # Demo credentials hint (for development)
    with st.expander("Demo Credentials"):
        st.code(f"Username: {DEMO_USERNAME}\nPassword: {DEMO_PASSWORD}")


def logout():
    """Clear authentication and session data."""
    for key in ["authenticated", "mpiid", "patient_name"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

