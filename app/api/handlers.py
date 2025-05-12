import json
import os
from datetime import datetime
from tornado.web import RequestHandler
from ..core.ability_manager import AbilityManager
from ..utils.obs_helper import OBSHelper

# 配置上传文件存储路径
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

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
            
    async def get(self, ability_name: str):
        """Handle ability execution request with GET method
        
        Args:
            ability_name: Name of the ability to execute
        """
        try:
            # 从URL参数获取数据
            context = {}
            for key in self.request.arguments:
                # 处理参数值，tornado以字节形式存储参数
                values = self.request.arguments[key]
                # 如果是单值参数，取第一个值
                if len(values) == 1:
                    context[key] = values[0].decode('utf-8')
                # 如果是多值参数，转换所有值
                else:
                    context[key] = [value.decode('utf-8') for value in values]
            
            # 特殊处理product_search能力
            if ability_name == "product_search" and "keyword" not in context and len(context) == 0:
                # 查看是否有查询字符串但没有指定参数名
                query_string = self.request.query
                if query_string and not '=' in query_string:
                    # 将整个查询字符串视为关键词
                    context["keyword"] = query_string
            
            result = await self.ability_manager.execute_ability(ability_name, context)
            self.write({"success": True, "data": result})
        except KeyError as e:
            self.set_status(404)
            self.write({"success": False, "error": str(e)})
        except ValueError as e:
            self.set_status(400)
            self.write({"success": False, "error": str(e)})
        except Exception as e:
            import traceback
            self.set_status(500)
            self.write({"success": False, "error": f"Internal server error: {str(e)}"})

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

class FileUploadHandler(BaseHandler):
    """Handler for file uploads to Huawei Cloud OBS"""
    
    def initialize(self, config):
        """Initialize with config from server"""
        self.config = config
        obs_config = config.get("huaweicloud", {}).get("obs", {})
        self.obs_helper = OBSHelper(
            access_key_id=obs_config.get("access_key_id"),
            secret_access_key=obs_config.get("secret_access_key"),
            server=obs_config.get("server"),
            bucket_name=obs_config.get("bucket_name")
        )
    
    async def post(self):
        """Handle file upload request"""
        try:
            files = self.request.files.get('file', [])
            if not files:
                raise ValueError("No file uploaded")
            
            file_info = files[0]
            original_filename = file_info['filename']
            
            # 验证文件类型
            if not original_filename.endswith('.xlsx'):
                raise ValueError("Only .xlsx files are allowed")
            
            # 上传文件到华为云 OBS
            file_url = await self.obs_helper.upload_file(
                file_data=file_info['body'],
                original_filename=original_filename
            )
            
            self.write({
                "success": True,
                "data": {
                    "filename": os.path.basename(file_url),
                    "file_url": file_url
                }
            })
        except ValueError as e:
            self.set_status(400)
            self.write({"success": False, "error": str(e)})
        except Exception as e:
            self.set_status(500)
            self.write({"success": False, "error": str(e)})