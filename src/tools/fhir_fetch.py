"""
FHIR data fetching tool - executed immediately after login.
"""

import os
import sys
import requests
from typing import Dict, Any, Optional
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.tools.base import BaseTool
from src.utils.patient_data import get_patient_endpoint

# Load environment variables
load_dotenv()


class FHIRFetchTool(BaseTool):
    """Tool to fetch patient FHIR data from endpoint."""
    
    def __init__(self):
        """Initialize FHIR fetch tool with credentials."""
        self.username = os.getenv("FHIR_USERNAME")
        self.password = os.getenv("FHIR_PASSWORD")
        
        if not self.username or not self.password:
            raise ValueError("FHIR_USERNAME and FHIR_PASSWORD must be set in environment variables")
    
    def get_name(self) -> str:
        """Get the name of the tool."""
        return "FHIR Fetch"
    
    def execute(self, mpiid: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Fetch FHIR data for a patient.
        
        Args:
            mpiid: Patient MPIID
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with 'success' (bool), 'data' (if success), or 'error' (if failure)
        """
        # Get patient endpoint from CSV
        patient_info = get_patient_endpoint(mpiid)
        
        if not patient_info:
            return {
                "success": False,
                "error": f"Patient with MPIID {mpiid} not found in patient database"
            }
        
        endpoint_url = patient_info['endpoint']
        
        try:
            # Make authenticated GET request
            response = requests.get(
                endpoint_url,
                auth=HTTPBasicAuth(self.username, self.password),
                headers={
                    'Accept': 'application/fhir+json',
                    'Content-Type': 'application/fhir+json'
                },
                timeout=timeout
            )
            
            # Check response status
            if response.status_code == 200:
                try:
                    fhir_data = response.json()
                    return {
                        "success": True,
                        "data": fhir_data,
                        "patient_info": patient_info
                    }
                except ValueError as e:
                    return {
                        "success": False,
                        "error": f"Failed to parse FHIR JSON response: {str(e)}"
                    }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "Authentication failed. Please contact technical staff."
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": f"Patient data not found for MPIID {mpiid}. Please contact technical staff."
                }
            else:
                return {
                    "success": False,
                    "error": f"FHIR server returned error {response.status_code}: {response.reason}. Please contact technical staff."
                }
        
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timed out. Please contact technical staff."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Could not connect to FHIR server. Please contact technical staff."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}. Please contact technical staff."
            }

