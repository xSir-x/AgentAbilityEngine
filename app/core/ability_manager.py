from typing import Dict, Any
from .base_ability import BaseAbility

class AbilityManager:
    """Ability Manager responsible for managing and executing all registered abilities"""
    
    def __init__(self):
        self._abilities: Dict[str, BaseAbility] = {}
    
    def register(self, ability: BaseAbility) -> None:
        """Register a new ability
        
        Args:
            ability: An instance implementing BaseAbility interface
        """
        self._abilities[ability.name] = ability
    
    def get_ability(self, name: str) -> BaseAbility:
        """Get ability by name
        
        Args:
            name: Name of the ability
            
        Returns:
            BaseAbility: The ability instance
            
        Raises:
            KeyError: When the specified ability doesn't exist
        """
        if name not in self._abilities:
            raise KeyError(f"Ability {name} not found")
        return self._abilities[name]
    
    async def execute_ability(self, name: str, context: Dict[str, Any]) -> Any:
        """Execute an ability by name
        
        Args:
            name: Name of the ability
            context: Execution context for the ability
            
        Returns:
            Any: Result of ability execution
            
        Raises:
            KeyError: When the specified ability doesn't exist
            ValueError: When input parameter validation fails
        """
        ability = self.get_ability(name)
        if not await ability.validate(context):
            raise ValueError(f"Invalid context for ability {name}")
        return await ability.execute(context)
    
    def list_abilities(self) -> Dict[str, str]:
        """List all registered abilities and their versions
        
        Returns:
            Dict[str, str]: Mapping of ability names to their versions
        """
        return {name: ability.version 
                for name, ability in self._abilities.items()}