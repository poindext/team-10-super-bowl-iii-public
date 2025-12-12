"""
Provider Search Tool - searches for healthcare providers by zip code.
Available for LLM to call when users ask about finding providers.
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

# Load environment variables
load_dotenv()

# API Configuration
BASE_URL = "http://ec2-98-82-129-136.compute-1.amazonaws.com/i4h/ctgov"
PROVIDER_SEARCH_ENDPOINT = f"{BASE_URL}/ProviderSearch"
TIMEOUT = 30


class ProviderSearchTool(BaseTool):
    """Tool to search for healthcare providers by zip code."""
    
    def __init__(self):
        """Initialize provider search tool with credentials."""
        # Use provider API credentials if available, otherwise fall back to FHIR credentials
        self.username = os.getenv("PROVIDER_API_USERNAME") or os.getenv("FHIR_USERNAME")
        self.password = os.getenv("PROVIDER_API_PASSWORD") or os.getenv("FHIR_PASSWORD")
        
        if not self.username or not self.password:
            raise ValueError(
                "Provider search credentials required. Set PROVIDER_API_USERNAME/PROVIDER_API_PASSWORD "
                "or FHIR_USERNAME/FHIR_PASSWORD environment variables."
            )
        
        self.auth = HTTPBasicAuth(self.username, self.password)
    
    def get_name(self) -> str:
        """Get the name of the tool."""
        return "Provider Search"
    
    def extract_zip_from_fhir(self, fhir_data: Any) -> Optional[str]:
        """
        Extract ZIP code from patient's FHIR data.
        
        Args:
            fhir_data: FHIR bundle or resource containing patient data
            
        Returns:
            ZIP code string if found, None otherwise
        """
        if not fhir_data or not isinstance(fhir_data, dict):
            return None
        
        # Check if it's a bundle with entries
        entries = fhir_data.get('entry', [])
        if entries:
            # Search through entries for Patient resource
            for entry in entries:
                resource = entry.get('resource', {}) if isinstance(entry, dict) else {}
                if resource.get('resourceType') == 'Patient':
                    # Extract postal code from Patient address
                    addresses = resource.get('address', [])
                    if isinstance(addresses, list) and len(addresses) > 0:
                        # Get first address (usually home address)
                        first_address = addresses[0]
                        if isinstance(first_address, dict):
                            postal_code = first_address.get('postalCode')
                            if postal_code:
                                # Extract first 5 digits if it's a ZIP+4 format
                                # Convert to string to preserve leading zeros
                                zip_code = str(postal_code).split('-')[0].strip()
                                # Pad with leading zero if needed to ensure 5 digits
                                if zip_code.isdigit() and len(zip_code) < 5:
                                    zip_code = zip_code.zfill(5)
                                if zip_code:
                                    return zip_code
        else:
            # Direct Patient resource
            if fhir_data.get('resourceType') == 'Patient':
                addresses = fhir_data.get('address', [])
                if isinstance(addresses, list) and len(addresses) > 0:
                    first_address = addresses[0]
                    if isinstance(first_address, dict):
                        postal_code = first_address.get('postalCode')
                        if postal_code:
                            # Convert to string to preserve leading zeros
                            zip_code = str(postal_code).split('-')[0].strip()
                            # Pad with leading zero if needed to ensure 5 digits
                            if zip_code.isdigit() and len(zip_code) < 5:
                                zip_code = zip_code.zfill(5)
                            if zip_code:
                                return zip_code
        
        return None
    
    def execute(self, zip_code: Optional[str] = None, fhir_data: Optional[Any] = None, maxresults: Optional[int] = 10, **kwargs) -> Dict[str, Any]:
        """
        Search for healthcare providers by zip code.
        ZIP code can be provided directly or extracted from FHIR data.
        
        Args:
            zip_code: ZIP code to search for (optional - will extract from FHIR if not provided, or can be provided by user)
            fhir_data: Patient FHIR data to extract ZIP code from (if zip_code not provided)
            maxresults: Maximum number of results to return (default: 10)
            **kwargs: Additional parameters (ignored - only zip code search is supported)
            
        Returns:
            Dictionary with 'success' (bool), 'data' (if success), or 'error' (if failure)
        """
        # Use provided ZIP code if available, otherwise try to extract from FHIR data
        if not zip_code or not zip_code.strip():
            if fhir_data:
                zip_code = self.extract_zip_from_fhir(fhir_data)
        
        # If still no ZIP code, return error
        if not zip_code or not zip_code.strip():
            return {
                "success": False,
                "error": "ZIP code is required for provider search. Please provide a ZIP code or ensure it's in your health records."
            }
        
        # Clean and validate zip code - ensure it's a string to preserve leading zeros
        zip_code = str(zip_code).strip()
        # Pad with leading zero if needed to ensure 5 digits
        if zip_code.isdigit() and len(zip_code) < 5:
            zip_code = zip_code.zfill(5)
        
        params = {
            'zip': zip_code,
            'maxresults': maxresults if maxresults else 10
        }
        
        try:
            response = requests.get(
                PROVIDER_SEARCH_ENDPOINT,
                params=params,
                auth=self.auth,
                headers={'Accept': 'application/json'},
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                try:
                    providers = response.json()
                    
                    # Format results for display in chat interface
                    formatted_results = []
                    if isinstance(providers, list):
                        for provider in providers:
                            formatted_provider = self._format_provider_for_display(provider)
                            formatted_results.append(formatted_provider)
                    
                    return {
                        "success": True,
                        "data": formatted_results,
                        "count": len(formatted_results),
                        "zip_code": zip_code
                    }
                except ValueError as e:
                    return {
                        "success": False,
                        "error": f"Failed to parse provider search response: {str(e)}"
                    }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "Authentication failed for provider search API"
                }
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    return {
                        "success": False,
                        "error": f"Invalid request: {error_data.get('error', 'Bad request')}"
                    }
                except:
                    return {
                        "success": False,
                        "error": "Invalid request to provider search API"
                    }
            elif response.status_code == 500:
                return {
                    "success": False,
                    "error": "Provider search server error"
                }
            else:
                return {
                    "success": False,
                    "error": f"Provider search API returned error {response.status_code}"
                }
        
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Provider search request timed out"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Could not connect to provider search API"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error during provider search: {str(e)}"
            }
    
    def _format_name(self, name_obj: Dict[str, Any]) -> str:
        """Format provider name from API response."""
        if not isinstance(name_obj, dict):
            return "Unknown"
        
        name_parts = []
        if 'Prefix' in name_obj and name_obj['Prefix']:
            name_parts.append(name_obj['Prefix'])
        if 'First' in name_obj and name_obj['First']:
            name_parts.append(name_obj['First'])
        if 'Middle' in name_obj and name_obj['Middle']:
            name_parts.append(name_obj['Middle'])
        if 'Last' in name_obj and name_obj['Last']:
            name_parts.append(name_obj['Last'])
        if 'Suffix' in name_obj and name_obj['Suffix']:
            name_parts.append(name_obj['Suffix'])
        
        return ' '.join(name_parts) if name_parts else "Unknown"
    
    def _format_specialty(self, specialty_obj: Dict[str, Any]) -> str:
        """Format specialty from API response."""
        if not isinstance(specialty_obj, dict):
            return "Unknown specialty"
        
        description = specialty_obj.get('Description', '')
        code = specialty_obj.get('Code', '')
        
        if description:
            return description
        elif code:
            return f"Specialty code: {code}"
        else:
            return "Unknown specialty"
    
    def _format_provider_for_display(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a provider record for display in chat interface.
        Returns only the fields that should be displayed.
        """
        name = self._format_name(provider.get('Name', {}))
        specialty = self._format_specialty(provider.get('PrimarySpecialtyCodedValue', {}))
        addresses = self._format_addresses(provider.get('Addresses', []))
        
        # Format for display - only include key fields
        formatted = {
            'name': name,
            'specialty': specialty,
            'address': addresses[0] if addresses else 'Address not available',
            'npi': provider.get('NPI', 'N/A')
        }
        
        # Add additional address if available
        if len(addresses) > 1:
            formatted['additional_addresses'] = addresses[1:]
        
        return formatted
    
    def _format_addresses(self, addresses: list) -> list:
        """Format addresses from API response."""
        if not isinstance(addresses, list):
            return []
        
        formatted = []
        for addr in addresses:
            if not isinstance(addr, dict):
                continue
            
            addr_parts = []
            if 'AddressLine1' in addr and addr['AddressLine1']:
                addr_parts.append(addr['AddressLine1'])
            if 'AddressLine2' in addr and addr['AddressLine2']:
                addr_parts.append(addr['AddressLine2'])
            
            city = addr.get('City', '')
            state = addr.get('State', '')
            zip_code = addr.get('Zip', '')
            
            location_parts = []
            if city:
                location_parts.append(city)
            if state:
                location_parts.append(state)
            if zip_code:
                location_parts.append(zip_code)
            
            if location_parts:
                addr_parts.append(', '.join(location_parts))
            
            if addr_parts:
                formatted.append(', '.join(addr_parts))
        
        return formatted

