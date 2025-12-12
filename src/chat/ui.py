"""
Streamlit chat UI components.
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from src.chat.session import add_message, get_messages, get_minimized_fhir_data
from src.llm.orchestrator import LLMOrchestrator


def render_chat_interface():
    """Render the main chat interface."""
    
    # Initialize orchestrator
    if "orchestrator" not in st.session_state:
        try:
            st.session_state.orchestrator = LLMOrchestrator()
        except Exception as e:
            st.error(f"Failed to initialize AI: {str(e)}")
            st.stop()
    
    orchestrator = st.session_state.orchestrator
    
    # Display chat history
    messages = get_messages()
    if messages:
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
    else:
        # Welcome message
        st.info("👋 **Welcome!** I'm here to help you understand your health information. Ask me anything about your medical records, conditions, or medications.")
    
    # Chat input with better styling
    if prompt := st.chat_input("Ask me about your health..."):
        # Add user message
        add_message("user", prompt)
        st.chat_message("user").write(prompt)
        
        # Get minimized FHIR data for context (minimized once and cached in session)
        minimized_fhir_data = get_minimized_fhir_data()
        
        # Generate response
        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking..."):
                    response = orchestrator.generate_response(
                        user_message=prompt,
                        conversation_history=messages,
                        fhir_data=minimized_fhir_data
                    )
                    st.markdown(response)
                    add_message("assistant", response)
            except Exception as e:
                error_msg = f"I apologize, but I encountered an unexpected error: {str(e)}. Please try again or contact technical support."
                st.error(error_msg)
                add_message("assistant", error_msg)
                import traceback
                print(f"UI Error: {traceback.format_exc()}")

