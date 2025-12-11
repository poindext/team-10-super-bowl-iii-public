"""
Main Streamlit application entry point for AI Health Companion.
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from src.auth.login import is_authenticated, show_login_page, get_mpiid, get_patient_name, logout
from src.chat.session import initialize_session, set_fhir_data, get_fhir_data, set_minimized_fhir_data
from src.chat.ui import render_chat_interface
from src.utils.debug import render_debug_panel
from src.tools.fhir_fetch import FHIRFetchTool
from src.utils.fhir_minimizer import minimize_fhir_bundle


def main():
    """Main application entry point."""
    # Initialize session
    initialize_session()
    
    # Check authentication
    if not is_authenticated():
        show_login_page()
        return
    
    # User is authenticated - show main application
    mpiid = get_mpiid()
    patient_name = get_patient_name()
    
    # Fetch FHIR data immediately after login (if not already loaded)
    if get_fhir_data() is None:
        # Initialize FHIR fetch tool
        if "fhir_fetch_tool" not in st.session_state:
            try:
                st.session_state.fhir_fetch_tool = FHIRFetchTool()
            except Exception as e:
                st.error(f"Failed to initialize FHIR fetch tool: {str(e)}")
                st.stop()
        
        # Execute FHIR fetch
        with st.spinner("Loading your health information..."):
            result = st.session_state.fhir_fetch_tool.execute(mpiid)
            
            if result["success"]:
                # Store full FHIR data in session
                fhir_data = result["data"]
                set_fhir_data(fhir_data)
                
                # Minimize FHIR data once and store in session
                if isinstance(fhir_data, dict) and fhir_data.get("resourceType") == "Bundle":
                    minimized_fhir = minimize_fhir_bundle(fhir_data)
                    set_minimized_fhir_data(minimized_fhir)
                
                st.session_state.fhir_fetch_success = True
            else:
                # FHIR fetch failed - end flow with error message
                st.error("⚠️ **Unable to Load Health Information**")
                st.error(result.get("error", "Unknown error occurred"))
                st.info("**Please contact technical staff for assistance.**")
                st.stop()
    
    # Main app header with logout
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("AI Health Companion")
        st.markdown(f"**Patient:** {patient_name} (MPIID: {mpiid})")
    with col2:
        if st.button("Logout", type="secondary"):
            logout()
    
    # Debug panel in sidebar (doesn't impact main UI)
    render_debug_panel()
    
    # Render chat interface
    render_chat_interface()


if __name__ == "__main__":
    main()

