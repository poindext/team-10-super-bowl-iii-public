"""
Base tool interface for the tools ecosystem.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseTool(ABC):
    """Base class for all tools in the ecosystem."""
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool.
        
        Returns:
            Dictionary with 'success' (bool) and 'data' or 'error' keys
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the tool."""
        pass

