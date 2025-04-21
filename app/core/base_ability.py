from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAbility(ABC):
    """Base ability abstract class that all concrete abilities must inherit from"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Ability name"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Ability version"""
        pass
    
    @abstractmethod
    async def validate(self, context: Dict[str, Any]) -> bool:
        """Validate input parameters
        
        Args:
            context: Dictionary containing input parameters
            
        Returns:
            bool: Whether the parameters are valid
        """
        pass
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Any:
        """Execute ability logic
        
        Args:
            context: Dictionary containing input parameters
            
        Returns:
            Any: Execution result
        """
        pass