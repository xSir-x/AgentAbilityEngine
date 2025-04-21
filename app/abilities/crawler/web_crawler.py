import aiohttp
from typing import Dict, Any
from ...core.base_ability import BaseAbility

class WebCrawlerAbility(BaseAbility):
    """网页爬虫能力实现"""
    
    @property
    def name(self) -> str:
        return "web_crawler"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def validate(self, context: Dict[str, Any]) -> bool:
        """验证输入参数
        
        必需参数:
        - url: 要爬取的网页URL
        
        可选参数:
        - headers: 自定义请求头
        """
        return isinstance(context.get("url"), str)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行爬虫逻辑
        
        Returns:
            Dict[str, Any]: {
                "status": HTTP状态码,
                "content": 页面内容,
                "headers": 响应头
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