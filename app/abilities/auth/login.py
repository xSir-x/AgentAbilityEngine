"""
Login ability for authenticating users.
"""
from typing import Dict, Any
from ...core.base_ability import BaseAbility
import yaml
import os
import logging
import json

class LoginAbility(BaseAbility):
    """Login ability implementation for authenticating users"""
    
    def __init__(self):
        """Initialize with default configuration"""
        # Load configuration file if exists
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                   "config", "auth_config.yaml")
        self.config = {}
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f) or {}
        except Exception as e:
            logging.error(f"Failed to load auth configuration: {e}")
        
        # Default merchant data if not specified in config
        self.merchant_data = self.config.get("merchants", {})
        
        # Set default user credentials if not in config
        self.users = self.config.get("users", {
            "admin": {"password": "admin123", "merchant_id": "default_merchant"}
        })
    
    @property
    def name(self) -> str:
        """Ability name"""
        return "login"
    
    @property
    def version(self) -> str:
        """Ability version"""
        return "1.0.0"
    
    async def validate(self, context: Dict[str, Any]) -> bool:
        """Validate input parameters
        
        Args:
            context: Dictionary containing input parameters
            
        Returns:
            bool: Whether the parameters are valid
        """
        # Check if necessary parameters are provided
        return "username" in context and "password" in context
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ability logic
        
        Args:
            context: Dictionary containing input parameters
                - username: User's username
                - password: User's password
            
        Returns:
            Dict[str, Any]: Login result containing merchant details
                - success: Whether login was successful
                - merchant_id: ID of the merchant
                - merchant_bg_url: Background image URL of the merchant
                - merchant_bot_id: Bot ID of the merchant
                - merchant_user_id: User ID of the merchant
                - merchant_coze_token: Coze token of the merchant
        """
        username = context.get("username")
        password = context.get("password")
        
        # Verify user credentials
        user_data = self.users.get(username)
        if not user_data or user_data.get("password") != password:
            return {
                "success": False,
                "error": "Invalid username or password"
            }
        
        # Get merchant details
        merchant_id = user_data.get("merchant_id", "default_merchant")
        merchant_info = self.merchant_data.get(merchant_id, {})
        
        # Return merchant details
        return {
            "success": True,
            "merchant_id": merchant_id,
            "merchant_bg_url": merchant_info.get("bg_url", "https://default-bg-url.com/background.jpg"),
            "merchant_bot_id": merchant_info.get("bot_id", "default_bot_id"),
            "merchant_user_id": merchant_info.get("user_id", "default_user_id"),
            "merchant_coze_token": merchant_info.get("coze_token", "default_coze_token")
        }