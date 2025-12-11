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
    st.header("Chat with your Health Companion")
    
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
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        add_message("user", prompt)
        st.chat_message("user").write(prompt)
        
        # Get minimized FHIR data for context (minimized once and cached in session)
        minimized_fhir_data = get_minimized_fhir_data()
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = orchestrator.generate_response(
                    user_message=prompt,
                    conversation_history=messages,
                    fhir_data=minimized_fhir_data
                )
                st.write(response)
                add_message("assistant", response)

