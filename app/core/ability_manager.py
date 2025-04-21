from typing import Dict, Any
from .base_ability import BaseAbility

class AbilityManager:
    """能力管理器，负责管理和执行所有已注册的能力"""
    
    def __init__(self):
        self._abilities: Dict[str, BaseAbility] = {}
    
    def register(self, ability: BaseAbility) -> None:
        """注册新能力
        
        Args:
            ability: 实现了BaseAbility的能力实例
        """
        self._abilities[ability.name] = ability
    
    def get_ability(self, name: str) -> BaseAbility:
        """获取指定名称的能力
        
        Args:
            name: 能力名称
            
        Returns:
            BaseAbility: 能力实例
            
        Raises:
            KeyError: 当指定名称的能力不存在时
        """
        if name not in self._abilities:
            raise KeyError(f"Ability {name} not found")
        return self._abilities[name]
    
    async def execute_ability(self, name: str, context: Dict[str, Any]) -> Any:
        """执行指定名称的能力
        
        Args:
            name: 能力名称
            context: 能力执行上下文
            
        Returns:
            Any: 能力执行结果
            
        Raises:
            KeyError: 当指定名称的能力不存在时
            ValueError: 当输入参数验证失败时
        """
        ability = self.get_ability(name)
        if not await ability.validate(context):
            raise ValueError(f"Invalid context for ability {name}")
        return await ability.execute(context)
    
    def list_abilities(self) -> Dict[str, str]:
        """列出所有已注册的能力及其版本
        
        Returns:
            Dict[str, str]: 能力名称到版本的映射
        """
        return {name: ability.version 
                for name, ability in self._abilities.items()}