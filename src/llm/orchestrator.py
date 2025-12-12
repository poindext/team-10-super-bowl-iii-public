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
        """Initialize the LLM orchestrator with OpenAI client and tools."""
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-5.1")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.system_prompt = SYSTEM_PROMPT
        
        # Initialize tools
        self.tools = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize available tools for the LLM."""
        try:
            from src.tools.provider_search import ProviderSearchTool
            provider_tool = ProviderSearchTool()
            self.tools['search_providers_by_zip'] = provider_tool
            print("✅ Provider search tool initialized")
        except ValueError as e:
            # Credentials missing - tool not available but app can continue
            print(f"⚠️  Provider search tool not available: {str(e)}")
        except Exception as e:
            # Other errors - log but continue
            print(f"⚠️  Could not initialize provider search tool: {str(e)}")
            # Continue without the tool - app should still work
    
    def _get_function_definitions(self) -> List[Dict[str, Any]]:
        """Get function definitions for OpenAI function calling."""
        functions = []
        
        # Provider Search Tool
        if 'search_providers_by_zip' in self.tools:
            functions.append({
                "type": "function",
                "function": {
                    "name": "search_providers_by_zip",
                    "description": "Search for healthcare providers by ZIP code. Use this when the user asks about finding doctors, providers, or healthcare services. The ZIP code will be automatically extracted from the patient's health records if available, or you can use a ZIP code provided by the user.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "zip_code": {
                                "type": "string",
                                "description": "ZIP code to search for. If not provided, the tool will try to extract it from the patient's health records. If the user provides a ZIP code, use that value. Example: '02142' or '90210'"
                            },
                            "maxresults": {
                                "type": "integer",
                                "description": "Maximum number of results to return. Default is 10.",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 50
                            }
                        },
                        "required": []
                    }
                }
            })
        
        return functions
    
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
        Generate a response using LLM with function calling support.
        
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
        
        # Get function definitions
        functions = self._get_function_definitions()
        
        try:
            # Maximum iterations for function calling loop
            max_iterations = 5
            iteration = 0
            
            while iteration < max_iterations:
                # Prepare API call parameters
                api_params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "timeout": 60
                }
                
                # Add functions if available
                if functions:
                    api_params["tools"] = functions
                    api_params["tool_choice"] = "auto"  # Let the model decide when to use tools
                
                # Call OpenAI API
                response = self.client.chat.completions.create(**api_params)
                
                message = response.choices[0].message
                
                # Add assistant's message to conversation
                assistant_message = {
                    "role": "assistant",
                    "content": message.content
                }
                
                # Add tool calls if present
                if message.tool_calls:
                    assistant_message["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in message.tool_calls
                    ]
                
                messages.append(assistant_message)
                
                # Check if the model wants to call a function
                if message.tool_calls:
                    # Execute function calls
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        # Execute the tool (pass FHIR data so tools can extract patient info)
                        tool_result = self._execute_tool(function_name, function_args, fhir_data=fhir_data)
                        
                        # Add function result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result, indent=2)
                        })
                    
                    # Continue the loop to get the final response
                    iteration += 1
                    continue
                else:
                    # No function calls - return the final response
                    return message.content or "I apologize, but I couldn't generate a response."
            
            # If we've exceeded max iterations, return the last message
            if messages and messages[-1].get("role") == "assistant":
                return messages[-1].get("content", "I apologize, but the conversation exceeded the maximum iterations.")
            else:
                return "I apologize, but I encountered an issue processing your request."
        
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
    
    def _execute_tool(self, function_name: str, function_args: Dict[str, Any], fhir_data: Optional[Any] = None) -> Dict[str, Any]:
        """
        Execute a tool function.
        
        Args:
            function_name: Name of the function to execute
            function_args: Arguments for the function
            fhir_data: Optional FHIR data to pass to tools
            
        Returns:
            Dictionary with tool execution results
        """
        try:
            if function_name == "search_providers_by_zip":
                if 'search_providers_by_zip' not in self.tools:
                    return {
                        "success": False,
                        "error": "Provider search tool is not available"
                    }
                
                tool = self.tools['search_providers_by_zip']
                # Pass FHIR data to tool so it can extract ZIP code
                result = tool.execute(fhir_data=fhir_data, **function_args)
                
                # Format result for LLM consumption
                if result.get("success"):
                    providers = result.get("data", [])
                    return {
                        "success": True,
                        "count": result.get("count", 0),
                        "zip_code": result.get("zip_code"),
                        "providers": providers,
                        "summary": f"Found {result.get('count', 0)} provider(s) in ZIP code {result.get('zip_code')}"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Unknown error during provider search")
                    }
            else:
                return {
                    "success": False,
                    "error": f"Unknown function: {function_name}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing tool {function_name}: {str(e)}"
            }

