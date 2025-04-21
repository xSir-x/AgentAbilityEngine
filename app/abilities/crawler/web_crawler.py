import aiohttp
from typing import Dict, Any
from ...core.base_ability import BaseAbility

class WebCrawlerAbility(BaseAbility):
    """Web crawler ability implementation"""
    
    @property
    def name(self) -> str:
        return "web_crawler"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def validate(self, context: Dict[str, Any]) -> bool:
        """Validate input parameters
        
        Required parameters:
        - url: Target webpage URL
        
        Optional parameters:
        - headers: Custom request headers
        """
        return isinstance(context.get("url"), str)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute crawler logic
        
        Returns:
            Dict[str, Any]: {
                "status": HTTP status code,
                "content": Page content,
                "headers": Response headers
            }
        """
        url = context["url"]
        headers = context.get("headers", {})
        
        # async with aiohttp.ClientSession() as session:
        #     async with session.get(url, headers=headers) as response:
        #         return {
        #             "status": response.status,
        #             "content": await response.text(),
        #             "headers": dict(response.headers)
        #         }
        
        return {
                    "status": 200,
                    "content": "test normal"
                }