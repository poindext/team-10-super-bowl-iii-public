"""
Gradio application entry point for AI Health Companion.
Parallel implementation to Streamlit - zero impact on existing app.
Run with: python gradio_app.py
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import gradio as gr
from src.auth.gradio_login import (
    is_authenticated,
    get_mpiid,
    get_patient_name,
    authenticate,
    logout,
    DEMO_USERNAME,
    DEMO_PASSWORD
)
from src.chat.gradio_session import (
    GradioSession,
    add_message,
    get_messages,
    set_fhir_data,
    get_fhir_data,
    set_minimized_fhir_data,
    get_minimized_fhir_data
)
from src.tools.fhir_fetch import FHIRFetchTool
from src.utils.fhir_minimizer import minimize_fhir_bundle
from src.utils.health_summary import extract_health_summary
from src.llm.orchestrator import LLMOrchestrator

# Module-level cache for FHIR data (persists across Gradio state serialization)
_fhir_cache = {}  # {mpiid: {'fhir_data': ..., 'minimized_fhir_data': ...}}


def dict_to_session(state_dict):
    """Convert dict to GradioSession."""
    if isinstance(state_dict, GradioSession):
        return state_dict
    if not isinstance(state_dict, dict) or state_dict is None:
        return GradioSession()
    
    session = GradioSession()
    # Only restore basic fields - fhir_data will be re-fetched if needed
    if 'messages' in state_dict:
        session.messages = state_dict['messages'] if isinstance(state_dict['messages'], list) else []
    if 'authenticated' in state_dict:
        # Convert string back to boolean
        session.authenticated = state_dict['authenticated'] == 'true' if isinstance(state_dict['authenticated'], str) else bool(state_dict['authenticated'])
    if 'mpiid' in state_dict and state_dict['mpiid']:
        session.mpiid = str(state_dict['mpiid'])
    if 'patient_name' in state_dict and state_dict['patient_name']:
        session.patient_name = str(state_dict['patient_name'])
    # fhir_data and minimized_fhir_data are not stored in state - will be None
    return session


def session_to_dict(session):
    """Convert GradioSession to dict for Gradio state storage."""
    if isinstance(session, dict):
        return session
    if not isinstance(session, GradioSession):
        return None
    
    # Only store serializable data - convert booleans to strings to avoid Gradio introspection issues
    result = {
        'messages': session.messages if session.messages else [],
        'authenticated': 'true' if session.authenticated else 'false',  # Store as string, not boolean
        'mpiid': str(session.mpiid) if session.mpiid else None,
        'patient_name': str(session.patient_name) if session.patient_name else None,
    }
    # Don't store fhir_data or minimized_fhir_data in state - they're too large
    # They'll be re-fetched if needed
    return result


def handle_login(username: str, password: str, state_dict) -> tuple:
    """Handle login attempt."""
    state = dict_to_session(state_dict)
    state, success = authenticate(state, username, password)
    
    if success:
        return handle_post_login(state)
    else:
        # Return boolean values instead of gr.update() objects
        return session_to_dict(state), True, False, "", [], ""


def handle_post_login(state) -> tuple:
    """Handle post-login flow: fetch FHIR data and setup main UI."""
    if not isinstance(state, GradioSession):
        state = dict_to_session(state)
    
    mpiid = get_mpiid(state)
    patient_name = get_patient_name(state)
    
    # Initialize orchestrator if needed
    if state.orchestrator is None:
        try:
            state.orchestrator = LLMOrchestrator()
        except Exception as e:
            # Return boolean values for visibility
            return session_to_dict(state), True, False, "", [], ""
    
    # Check cache first, then session, then fetch
    fhir_data = None
    if mpiid in _fhir_cache:
        # Restore from cache
        cached = _fhir_cache[mpiid]
        fhir_data = cached.get('fhir_data')
        minimized_fhir = cached.get('minimized_fhir_data')
        if fhir_data:
            state = set_fhir_data(state, fhir_data)
        if minimized_fhir:
            state = set_minimized_fhir_data(state, minimized_fhir)
    
    # Fetch FHIR data if not already loaded
    if get_fhir_data(state) is None:
        try:
            if state.fhir_fetch_tool is None:
                state.fhir_fetch_tool = FHIRFetchTool()
            
            result = state.fhir_fetch_tool.execute(mpiid)
            
            if result["success"]:
                fhir_data = result["data"]
                state = set_fhir_data(state, fhir_data)
                
                # Minimize FHIR data once and store
                minimized_fhir = None
                if isinstance(fhir_data, dict) and fhir_data.get("resourceType") == "Bundle":
                    minimized_fhir = minimize_fhir_bundle(fhir_data)
                    state = set_minimized_fhir_data(state, minimized_fhir)
                
                # Cache FHIR data by MPIID so it persists across state serialization
                _fhir_cache[mpiid] = {
                    'fhir_data': fhir_data,
                    'minimized_fhir_data': minimized_fhir
                }
                
                # Build health summary HTML
                health_summary_html = build_health_summary_html(fhir_data)
                
                # Show welcome message if no messages yet
                messages = get_messages(state)
                chat_history = []
                if len(messages) == 0:
                    welcome_msg = "👋 **Welcome!** I'm here to help you understand your health information. Ask me anything about your medical records, conditions, or medications."
                    state = add_message(state, "assistant", welcome_msg)
                    # Gradio Chatbot expects (user_message, assistant_message) tuples
                    # For welcome message, user is None
                    chat_history = [(None, welcome_msg)]
                else:
                    # Build chat history from existing messages - pair user and assistant messages
                    current_user = None
                    for msg in messages:
                        if msg["role"] == "user":
                            current_user = msg["content"]
                        elif msg["role"] == "assistant":
                            # Pair with previous user message (or None if no user message)
                            chat_history.append((current_user, msg["content"]))
                            current_user = None
                
                # Return boolean values for visibility (False=hide login, True=show main)
                return session_to_dict(state), False, True, health_summary_html, chat_history, f"**Patient:** {patient_name} (MPIID: {mpiid})"
            else:
                # FHIR fetch failed - show login again
                return session_to_dict(state), True, False, "", [], ""
        except Exception as e:
            # Error loading - show login again
            return session_to_dict(state), True, False, "", [], ""
    else:
        # FHIR data already loaded - get from state or cache
        fhir_data = get_fhir_data(state)
        if not fhir_data and mpiid in _fhir_cache:
            # Restore from cache if missing from state
            cached = _fhir_cache[mpiid]
            fhir_data = cached.get('fhir_data')
            minimized_fhir = cached.get('minimized_fhir_data')
            if fhir_data:
                state = set_fhir_data(state, fhir_data)
            if minimized_fhir:
                state = set_minimized_fhir_data(state, minimized_fhir)
        
        health_summary_html = build_health_summary_html(fhir_data)
        messages = get_messages(state)
        
        # Build chat history - pair user and assistant messages
        chat_history = []
        current_user = None
        for msg in messages:
            if msg["role"] == "user":
                current_user = msg["content"]
            elif msg["role"] == "assistant":
                # Pair with previous user message (or None if no user message)
                chat_history.append((current_user, msg["content"]))
                current_user = None
        
        # Show welcome if no messages
        if len(chat_history) == 0:
            welcome_msg = "👋 **Welcome!** I'm here to help you understand your health information. Ask me anything about your medical records, conditions, or medications."
            state = add_message(state, "assistant", welcome_msg)
            # Gradio Chatbot expects (user_message, assistant_message) tuples
            chat_history = [(None, welcome_msg)]
        
        # Return boolean values for visibility
        return session_to_dict(state), False, True, health_summary_html, chat_history, f"**Patient:** {patient_name} (MPIID: {mpiid})"


def get_debug_info(state_dict) -> str:
    """Generate debug information from state."""
    state = dict_to_session(state_dict)
    
    debug_lines = []
    debug_lines.append("### 🔍 Debug Panel\n")
    
    # Authentication Status
    debug_lines.append("#### Authentication")
    authenticated = getattr(state, 'authenticated', False) if state else False
    debug_lines.append(f"**Authenticated:** {authenticated}")
    
    mpiid = None
    if authenticated:
        mpiid = getattr(state, 'mpiid', 'N/A')
        patient_name = getattr(state, 'patient_name', 'N/A')
        debug_lines.append(f"**MPIID:** {mpiid}")
        debug_lines.append(f"**Patient Name:** {patient_name}")
    
    debug_lines.append("\n---\n")
    
    # Session Status
    debug_lines.append("#### Session")
    debug_lines.append(f"**Initialized:** {state is not None}")
    
    # Message History
    debug_lines.append("#### Message History")
    messages = getattr(state, 'messages', []) if state else []
    debug_lines.append(f"**Message Count:** {len(messages)}")
    
    # FHIR Data Status
    debug_lines.append("#### FHIR Data")
    fhir_data = get_fhir_data(state) if state else None
    
    # Check cache if not in state
    if not fhir_data and mpiid and mpiid in _fhir_cache:
        cached = _fhir_cache[mpiid]
        fhir_data = cached.get('fhir_data')
        debug_lines.append(f"**Cache Status:** ✅ Found in cache")
    
    if fhir_data:
        debug_lines.append("**Status:** ✅ FHIR data loaded")
        try:
            if isinstance(fhir_data, dict):
                fhir_keys = list(fhir_data.keys())[:5]
                debug_lines.append(f"**Top-level keys:** {', '.join(fhir_keys)}")
                if 'entry' in fhir_data:
                    entry_count = len(fhir_data.get('entry', []))
                    debug_lines.append(f"**Entries:** {entry_count}")
            else:
                debug_lines.append(f"**Type:** {type(fhir_data).__name__}")
        except Exception as e:
            debug_lines.append(f"**Error reading FHIR data:** {str(e)}")
    else:
        debug_lines.append("**Status:** ❌ No FHIR data loaded")
    
    debug_lines.append("\n---\n")
    
    # LLM Orchestrator Status
    debug_lines.append("#### LLM Orchestrator")
    orchestrator = getattr(state, 'orchestrator', None) if state else None
    debug_lines.append(f"**Initialized:** {orchestrator is not None}")
    if orchestrator:
        try:
            model = getattr(orchestrator, 'model', 'N/A')
            debug_lines.append(f"**Model:** {model}")
        except Exception as e:
            debug_lines.append(f"**Error:** {str(e)}")
    
    debug_lines.append("\n---\n")
    
    # Environment Variables
    debug_lines.append("#### Environment Variables")
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
        debug_lines.append(f"**{key}:** {value}")
    
    debug_lines.append("\n---\n")
    
    # Flow Status
    debug_lines.append("#### Flow Status")
    flow_steps = {
        "1. Authentication": "✅ Complete" if authenticated else "⏳ Pending",
        "2. Session Init": "✅ Complete" if state else "⏳ Pending",
        "3. FHIR Fetch": "✅ Complete" if fhir_data else "⏳ Pending",
        "4. LLM Ready": "✅ Ready" if orchestrator else "⏳ Pending",
        "5. Chat Active": "✅ Active" if len(messages) > 0 else "⏳ Waiting"
    }
    
    for step, status in flow_steps.items():
        debug_lines.append(f"**{step}:** {status}")
    
    return "\n".join(debug_lines)


def build_health_summary_html(fhir_data) -> str:
    """Build health summary HTML from FHIR data."""
    if not fhir_data:
        return ""
    
    health_summary = extract_health_summary(fhir_data)
    html = f"""
    <div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #1f77b4; margin-bottom: 1rem;">
        <h3>Health Summary</h3>
        <p><strong>{health_summary['one_line_summary']}</strong></p>
    """
    
    if health_summary['diagnoses']:
        html += "<p><strong>Current Diagnoses:</strong></p><ul>"
        for diagnosis in health_summary['diagnoses']:
            html += f"<li>{diagnosis}</li>"
        html += "</ul>"
    else:
        html += "<p><em>No active diagnoses on record</em></p>"
    
    info_parts = []
    if health_summary['medication_count'] > 0:
        info_parts.append(f"{health_summary['medication_count']} medication(s)")
    if health_summary['last_encounter_date']:
        date_str = health_summary['last_encounter_date']
        if 'T' in date_str:
            date_str = date_str.split('T')[0]
        info_parts.append(f"Last visit: {date_str}")
    
    if info_parts:
        html += f"<p>{' | '.join(info_parts)}</p>"
    
    html += "</div>"
    return html


def handle_message(message: str, state_dict, chatbot: list) -> tuple:
    """Handle user message and generate response."""
    state = dict_to_session(state_dict)
    
    if not is_authenticated(state):
        return session_to_dict(state), chatbot, ""
    
    if not message.strip():
        return session_to_dict(state), chatbot, ""
    
    # Add user message
    state = add_message(state, "user", message)
    
    # Note: Don't update chatbot here - wait for assistant response to add as a pair
    
    # Get orchestrator
    if state.orchestrator is None:
        try:
            state.orchestrator = LLMOrchestrator()
        except Exception as e:
            error_msg = f"Error: Failed to initialize AI - {str(e)}"
            state = add_message(state, "assistant", error_msg)
            chatbot.append((error_msg, "assistant"))
            return session_to_dict(state), chatbot, ""
    
    # Restore FHIR data from cache if missing
    mpiid = get_mpiid(state)
    if not get_fhir_data(state) and mpiid and mpiid in _fhir_cache:
        cached = _fhir_cache[mpiid]
        fhir_data = cached.get('fhir_data')
        minimized_fhir = cached.get('minimized_fhir_data')
        if fhir_data:
            state = set_fhir_data(state, fhir_data)
        if minimized_fhir:
            state = set_minimized_fhir_data(state, minimized_fhir)
    
    # Get minimized FHIR data
    minimized_fhir_data = get_minimized_fhir_data(state)
    
    # Get conversation history
    messages = get_messages(state)
    conversation_history = messages[:-1] if len(messages) > 1 else []
    
    # Generate response
    try:
        response = state.orchestrator.generate_response(
            user_message=message,
            conversation_history=conversation_history,
            fhir_data=minimized_fhir_data
        )
        
        # Add assistant response
        state = add_message(state, "assistant", response)
        # Gradio Chatbot expects (user_message, assistant_message) tuples
        chatbot.append((message, response))
        
    except Exception as e:
        error_msg = f"I apologize, but I encountered an unexpected error: {str(e)}. Please try again or contact technical support."
        state = add_message(state, "assistant", error_msg)
        # Gradio Chatbot expects (user_message, assistant_message) tuples
        chatbot.append((message, error_msg))
        import traceback
        print(f"Gradio UI Error: {traceback.format_exc()}")
    
    return session_to_dict(state), chatbot, ""


def handle_logout(state_dict) -> tuple:
    """Handle logout - clear session and show login."""
    state = dict_to_session(state_dict)
    mpiid = get_mpiid(state)
    state = logout(state)
    state.messages = []
    state.fhir_data = None
    state.minimized_fhir_data = None
    state.orchestrator = None
    state.fhir_fetch_tool = None
    
    # Optionally clear cache on logout (or keep it for faster re-login)
    # if mpiid in _fhir_cache:
    #     del _fhir_cache[mpiid]
    
    # Return boolean values for visibility (True=show login, False=hide main)
    return session_to_dict(state), True, False, "", [], ""


def create_app():
    """Create and launch Gradio app."""
    # Use Blocks but with minimal state to avoid introspection issues
    with gr.Blocks(title="AI Health Companion", theme=gr.themes.Soft()) as app:
        # State management - use simple dict, not complex object
        state = gr.State(value={})
        
        gr.Markdown("# AI Health Companion")
        
        # Status message (not used in simple approach)
        # status_msg = gr.Markdown("", visible=False)
        
        # Login UI
        login_ui = gr.Column(visible=True)
        with login_ui:
            gr.Markdown("## 🔐 Please log in to continue")
            username_input = gr.Textbox(label="Username", placeholder="Enter username")
            password_input = gr.Textbox(label="Password", type="password", placeholder="Enter password")
            login_btn = gr.Button("Log In", variant="primary")
            with gr.Accordion("Demo Credentials", open=False):
                gr.Markdown(f"**Username:** `{DEMO_USERNAME}`\n**Password:** `{DEMO_PASSWORD}`")
        
        # Main UI (initially hidden)
        main_ui = gr.Column(visible=False)
        with main_ui:
            # Header with patient info and logout button side by side
            with gr.Row():
                with gr.Column(scale=9):
                    patient_info = gr.Markdown("")
                with gr.Column(scale=1, min_width=100):
                    logout_btn = gr.Button("Logout", variant="secondary", size="sm")
            
            # Health Summary
            health_summary = gr.HTML("")
            
            # Chat Interface
            chatbot = gr.Chatbot(
                height=500,
                show_label=False,
                container=True,
                value=[]
            )
            
            # Chat input
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Ask me about your health...",
                    show_label=False,
                    scale=4,
                    container=False
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)
            
            # Debug Panel (collapsible) - moved below send button
            with gr.Accordion("🔍 Debug Panel", open=False):
                debug_panel = gr.Markdown("")
        
        # Login handler - wrap to convert boolean visibility to gr.update()
        def login_wrapper(username, password, current_state):
            result = handle_login(username, password, current_state)
            # Generate debug info
            debug_info = get_debug_info(result[0])
            # Convert boolean visibility to gr.update() objects
            return (
                result[0],  # state
                gr.update(visible=result[1]),  # login_ui
                gr.update(visible=result[2]),  # main_ui
                result[3],  # health_summary
                debug_info,  # debug_panel
                result[4],  # chatbot
                result[5]   # patient_info
            )
        
        login_btn.click(
            fn=login_wrapper,
            inputs=[username_input, password_input, state],
            outputs=[state, login_ui, main_ui, health_summary, debug_panel, chatbot, patient_info]
        )
        
        # Message handler wrapper to update debug panel
        def message_wrapper(message, current_state, chat_history):
            result = handle_message(message, current_state, chat_history)
            debug_info = get_debug_info(result[0])
            return (
                result[0],  # state
                result[1],  # chatbot
                result[2],  # msg_input
                debug_info  # debug_panel
            )
        
        # Message handlers
        send_btn.click(
            fn=message_wrapper,
            inputs=[msg_input, state, chatbot],
            outputs=[state, chatbot, msg_input, debug_panel]
        )
        
        msg_input.submit(
            fn=message_wrapper,
            inputs=[msg_input, state, chatbot],
            outputs=[state, chatbot, msg_input, debug_panel]
        )
        
        # Logout handler - wrap to convert boolean visibility to gr.update()
        def logout_wrapper(current_state):
            result = handle_logout(current_state)
            debug_info = get_debug_info(result[0])
            return (
                result[0],  # state
                gr.update(visible=result[1]),  # login_ui
                gr.update(visible=result[2]),  # main_ui
                result[3],  # health_summary
                debug_info,  # debug_panel
                result[4],  # chatbot
                result[5]   # patient_info
            )
        
        logout_btn.click(
            fn=logout_wrapper,
            inputs=[state],
            outputs=[state, login_ui, main_ui, health_summary, debug_panel, chatbot, patient_info]
        )
    
    return app


if __name__ == "__main__":
    app = create_app()
    # Disable API generation completely to avoid introspection bug
    # Set api_name=None to prevent API route creation
    app.launch(
        server_name="127.0.0.1", 
        server_port=7860, 
        share=False, 
        show_api=False
    )
