import json
from tornado.web import RequestHandler
from ..core.ability_manager import AbilityManager

class BaseHandler(RequestHandler):
    """基础请求处理器"""
    
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

class AbilityHandler(BaseHandler):
    """能力调用处理器"""
    
    def initialize(self, ability_manager: AbilityManager):
        self.ability_manager = ability_manager
    
    async def post(self, ability_name: str):
        """处理能力调用请求
        
        Args:
            ability_name: 能力名称
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
    """健康检查处理器"""
    
    def get(self):
        """处理健康检查请求"""
        self.write({"status": "ok"})

class AbilityListHandler(BaseHandler):
    """能力列表处理器"""
    
    def initialize(self, ability_manager: AbilityManager):
        self.ability_manager = ability_manager
    
    def get(self):
        """获取所有已注册的能力列表"""
        abilities = self.ability_manager.list_abilities()
        self.write({"abilities": abilities})