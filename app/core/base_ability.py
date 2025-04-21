from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAbility(ABC):
    """基础能力抽象类，所有具体能力都需要继承此类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """能力名称"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """能力版本"""
        pass
    
    @abstractmethod
    async def validate(self, context: Dict[str, Any]) -> bool:
        """验证输入参数的合法性
        
        Args:
            context: 包含输入参数的字典
            
        Returns:
            bool: 参数是否合法
        """
        pass
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Any:
        """执行能力逻辑
        
        Args:
            context: 包含输入参数的字典
            
        Returns:
            Any: 执行结果
        """
        pass