"""
LLM Orchestrator - Core reasoning engine for AI Health Companion.
"""

import sys
import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.llm.prompts import SYSTEM_PROMPT, check_emergency, get_emergency_response

# Load environment variables
load_dotenv()


class LLMOrchestrator:
    """LLM orchestrator for reasoning and conversation management."""
    
    def __init__(self):
        """Initialize the LLM orchestrator with OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-5.1")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.system_prompt = SYSTEM_PROMPT
    
    def _build_messages(
        self, 
        conversation_history: List[Dict[str, Any]], 
        fhir_data: Optional[Any] = None
    ) -> List[Dict[str, str]]:
        """
        Build messages list for OpenAI API.
        
        Args:
            conversation_history: List of conversation messages
            fhir_data: Optional FHIR data to include in context
            
        Returns:
            List of message dictionaries for OpenAI API
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add FHIR data context if available (fhir_data should already be minimized from session)
        if fhir_data:
            try:
                # Serialize FHIR data to JSON
                fhir_json = json.dumps(fhir_data, indent=2)
                fhir_size = len(fhir_json)
                
                # Check if FHIR data is too large (rough estimate: 200k chars ≈ 50k tokens)
                if fhir_size > 200000:
                    # Truncate or provide summary instead
                    print(f"Warning: FHIR data is large ({fhir_size} chars). Using summary approach.")
                    # For now, still include it but with a note
                    fhir_context = f"\n\nPATIENT FHIR DATA (minimized raw JSON, {fhir_size} chars):\n{fhir_json[:200000]}...\n[Data truncated due to size - {fhir_size - 200000} chars omitted]\n\nUse this data to provide personalized, context-aware responses."
                else:
                    fhir_context = f"\n\nPATIENT FHIR DATA (minimized raw JSON):\n{fhir_json}\n\nUse this data to provide personalized, context-aware responses."
                
                messages[0]["content"] += fhir_context
            except Exception as e:
                print(f"Error serializing FHIR data: {str(e)}")
                # Continue without FHIR data if serialization fails
                messages[0]["content"] += "\n\nNote: Patient FHIR data is available but could not be included in this request."
        
        # Add conversation history
        for msg in conversation_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return messages
    
    def generate_response(
        self, 
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        fhir_data: Optional[Any] = None
    ) -> str:
        """
        Generate a response using LLM.
        
        Args:
            user_message: Current user message
            conversation_history: Previous conversation messages
            fhir_data: Optional FHIR data for context
            
        Returns:
            LLM generated response
        """
        # Check for emergency first
        if check_emergency(user_message):
            return get_emergency_response()
        
        # Build conversation history with new message
        history = conversation_history + [{"role": "user", "content": user_message}]
        
        # Build messages for API
        messages = self._build_messages(history, fhir_data)
        
        try:
            # Call OpenAI API
            # Note: Not setting max_completion_tokens - let the model generate as much as needed
            # The model will naturally stop when the response is complete
            # This is especially important for comprehensive health summaries
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                timeout=60  # 60 second timeout
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            error_msg = str(e)
            # Log more details for debugging
            import traceback
            error_details = traceback.format_exc()
            print(f"LLM Error: {error_msg}")
            print(f"Error details: {error_details}")
            
            # Provide more helpful error message
            if "context_length_exceeded" in error_msg.lower() or "token" in error_msg.lower():
                return "I apologize, but the health data is too large to process. Please contact technical staff for assistance."
            elif "timeout" in error_msg.lower():
                return "I apologize, but the request timed out. Please try again with a more specific question."
            else:
                return f"I apologize, but I encountered an error: {error_msg}. Please try again."

