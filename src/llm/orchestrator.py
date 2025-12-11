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
            fhir_context = f"\n\nPATIENT FHIR DATA (minimized raw JSON):\n{json.dumps(fhir_data, indent=2)}\n\nUse this data to provide personalized, context-aware responses."
            messages[0]["content"] += fhir_context
        
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_completion_tokens=1000
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Please try again."

