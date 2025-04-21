import json
from tornado.web import RequestHandler
from ..core.ability_manager import AbilityManager

class BaseHandler(RequestHandler):
    """Base request handler"""
    
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

class AbilityHandler(BaseHandler):
    """Handler for ability execution"""
    
    def initialize(self, ability_manager: AbilityManager):
        self.ability_manager = ability_manager
    
    async def post(self, ability_name: str):
        """Handle ability execution request
        
        Args:
            ability_name: Name of the ability to execute
        """
        try:
            context = json.loads(self.request.body)
            result = await self.ability_manager.execute_ability(ability_name, context)
            self.write({"success": True, "data": result})
        except json.JSONDecodeError:
            self.set_status(400)
            self.write({"success": False, "error": "Invalid JSON format"})
        except KeyError as e:
            self.set_status(404)
            self.write({"success": False, "error": str(e)})
        except ValueError as e:
            self.set_status(400)
            self.write({"success": False, "error": str(e)})
        except Exception as e:
            self.set_status(500)
            self.write({"success": False, "error": "Internal server error"})

class HealthHandler(BaseHandler):
    """Health check handler"""
    
    def get(self):
        """Handle health check request"""
        self.write({"status": "ok"})

class AbilityListHandler(BaseHandler):
    """Handler for listing available abilities"""
    
    def initialize(self, ability_manager: AbilityManager):
        self.ability_manager = ability_manager
    
    def get(self):
        """Get list of all registered abilities"""
        abilities = self.ability_manager.list_abilities()
        self.write({"abilities": abilities})