"""
UI styling utilities for modern, crisp look and feel.
"""

import streamlit as st


def inject_custom_css():
    """Inject minimal CSS for clean spacing."""
    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1000px;
        }
        .stChatMessage {
            margin-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

