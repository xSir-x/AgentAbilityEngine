"""
Login ability for authenticating users using MySQL database on Huawei Cloud.
"""
from typing import Dict, Any
from ...core.base_ability import BaseAbility
import yaml
import os
import logging
import json
import pymysql
from pymysql.cursors import DictCursor

class LoginAbility(BaseAbility):
    """Login ability implementation for authenticating users from MySQL database"""
    
    def __init__(self):
        """Initialize with database configuration"""
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
        
        # Database configuration
        self.db_config = self.config.get("database", {
            "host": "e6ea2387617046a283e6b583b0fc9a31in01.internal.cn-south-1.mysql.rds.myhuaweicloud.com",
            "user": "root",
            "password": "",  # Will be loaded from config
            "db": "merchant_db",
            "charset": "utf8mb4",
            "cursorclass": DictCursor
        })
        
        # Fallback configuration if database connection fails
        self.fallback_enabled = self.config.get("fallback_enabled", True)
        self.merchant_data = self.config.get("merchants", {})
        self.users = self.config.get("users", {
            "admin": {"password": "admin123", "merchant_id": "default_merchant"}
        })
        
        # Initialize connection to None, will be established when needed
        self.connection = None
    
    def _get_connection(self):
        """Get database connection, create new if doesn't exist or closed"""
        try:
            if self.connection is None or not self.connection.open:
                self.connection = pymysql.connect(**self.db_config)
            return self.connection
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            raise
    
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
        
        print("username: "+username)
        print("password: "+password)
        # Try to authenticate using database
        try:
            # Get database connection
            connection = self._get_connection()
            
            with connection.cursor() as cursor:
                # Verify user credentials
                # Note: In production, passwords should be hashed
                sql = "SELECT * FROM sales_vendor_info WHERE user_name = %s AND password = %s"
                connection.commit()
                cursor.execute(sql, (username, password))
                user_data = cursor.fetchone()
                
                if not user_data:
                    return {
                        "success": False,
                        "error": "Invalid username or password"
                    }
                
                # # Get merchant details based on merchant_id
                # merchant_id = user_data.get("merchant_id")
                # sql = "SELECT * FROM merchants WHERE merchant_id = %s"
                # cursor.execute(sql, (merchant_id,))
                # merchant_info = cursor.fetchone()

                return {
                    "success": True,
                    "merchant_id": user_data[2],
                    "merchant_bg_url": user_data[3] ,
                    "merchant_bot_id": user_data[4] ,
                    "merchant_user_id": user_data[5] ,
                    "merchant_coze_token": user_data[6]
                }
                       
        except Exception as e:
            logging.error(f"Database login error: {e}")
            
            # Fallback to configuration-based authentication if enabled
            if not self.fallback_enabled:
                return {
                    "success": False,
                    "error": f"Database error: {str(e)}"
                }
            
            # Log fallback authentication attempt
            logging.info(f"Falling back to configuration-based authentication for user: {username}")
            
            # Fallback authentication logic
            user_data = self.users.get(username)
            if not user_data or user_data.get("password") != password:
                return {
                    "success": False,
                    "error": "Invalid username or password"
                }
            
            # Get merchant details
            merchant_id = user_data.get("vendor_id", "default_merchant")
            merchant_info = self.merchant_data.get(merchant_id, {})
            
            # Return merchant details
            return {
                "success": True,
                "merchant_id": merchant_id,
                "merchant_bg_url": merchant_info.get("vendor_bg", "https://default-bg-url.com/background.jpg"),
                "merchant_bot_id": merchant_info.get("bot_id", "default_bot_id"),
                "merchant_user_id": merchant_info.get("user_id", "default_user_id"),
                "merchant_coze_token": merchant_info.get("coze_token", "default_coze_token")
            }
    
    def __del__(self):
        """Close database connection when object is destroyed"""
        if hasattr(self, 'connection') and self.connection and self.connection.open:
            self.connection.close()