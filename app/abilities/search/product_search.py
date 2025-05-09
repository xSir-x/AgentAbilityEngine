"""
Product search ability for searching products in Elasticsearch.
Provides fuzzy search capability with fallback recommendations.
"""
from typing import Dict, Any, List, Optional
import yaml
import os
import logging
import json
import random
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError
from ...core.base_ability import BaseAbility

class ProductSearchAbility(BaseAbility):
    """
    Product search ability implementation using Elasticsearch
    
    Features:
    - Fuzzy search for products based on keywords
    - Multi-field search (款号, 产品名称, 品目)
    - Fallback recommendations when no results found
    """
    
    def __init__(self):
        """Initialize with elasticsearch configuration"""
        # Load configuration file
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                 "config", "es_config.yaml")
        self.config = {}
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f) or {}
                logging.info(f"Loaded ES configuration from {config_path}")
            else:
                logging.warning(f"ES configuration file not found at {config_path}")
        except Exception as e:
            logging.error(f"Failed to load ES configuration: {e}")
        
        # Elasticsearch configuration
        self.es_config = self.config.get("elasticsearch", {
            "host": "es-cn-north-4.myhuaweicloud.com",  # Updated to use Huawei Cloud hostname format
            "port": 9200,
            "username": "admin",
            "password": "!Y12345678",
            "use_ssl": True  # Default to True for Huawei Cloud ES
        })
        
        # Search configuration
        self.search_config = self.config.get("search", {
            "index": "products",
            "default_size": 5,
            "fuzziness": "AUTO",
            "min_score": 0.5
        })
        
        # Fallback configuration
        self.fallback_config = self.config.get("fallback", {
            "enabled": True,
            "keywords": ["耳环", "手链", "耳饰"],
            "size": 3
        })
        
        # Initialize elasticsearch client to None, will be established when needed
        self.es_client = None
    
    def _get_es_client(self) -> Elasticsearch:
        """
        Get elasticsearch client, create new if doesn't exist
        
        Returns:
            Elasticsearch: Elasticsearch client
        
        Raises:
            ConnectionError: If connection to Elasticsearch fails
        """
        try:
            if self.es_client is None:
                # Extract connection parameters
                host = self.es_config.get("host")
                port = self.es_config.get("port")
                username = self.es_config.get("username")
                password = self.es_config.get("password")
                use_ssl = self.es_config.get("use_ssl", False)
                
                # 打印连接参数 (密码只显示前两位，其余用*替代)
                masked_password = password[:2] + "*" * (len(password) - 2) if password else None
                logging.warning(f"ES连接参数: host={host}, port={port}, username={username}, password={masked_password}, use_ssl={use_ssl}")
                
                # Construct connection URL
                es_url = f"{'https' if use_ssl else 'http'}://{host}:{port}"
                logging.info(f"正在连接到Elasticsearch: {es_url} (use_ssl={use_ssl})")
                
                # 记录连接配置（不包含密码）
                logging.debug(f"Elasticsearch连接配置: host={host}, port={port}, username={username}, use_ssl={use_ssl}")
                
                # Create Elasticsearch client with simpler configuration
                logging.debug(f"创建Elasticsearch客户端实例，超时设置为30秒")
                self.es_client = Elasticsearch(
                    [es_url],
                    http_auth=(username, password),
                    use_ssl=use_ssl,
                    verify_certs=False,  # In production, should be True with proper certificates
                    ssl_show_warn=False,
                    timeout=30,  # 30 second timeout for all operations
                    retry_on_timeout=True,
                    max_retries=3
                )
                
                # Validate connection
                logging.debug("尝试ping Elasticsearch以验证连接...")
                if self.es_client.ping():
                    es_info = self.es_client.info()
                    logging.info(f"成功连接到Elasticsearch! 版本: {es_info['version']['number']}")
                    logging.debug(f"Elasticsearch完整信息: {json.dumps(es_info, ensure_ascii=False)}")
                else:
                    logging.error("Elasticsearch ping失败，无法建立连接")
                    self.es_client = None
                    raise ConnectionError("Cannot ping Elasticsearch")
            
            return self.es_client
        except ConnectionError as e:
            logging.error(f"Elasticsearch连接错误: {str(e)}")
            logging.error(f"连接异常详情: {e.__class__.__name__}")
            logging.debug(f"连接异常堆栈: ", exc_info=True)
            self.es_client = None  # Reset client on connection error
            raise ConnectionError(f"Failed to connect to Elasticsearch: {str(e)}")
        except Exception as e:
            logging.error(f"Elasticsearch客户端错误: {str(e)}")
            logging.error(f"异常类型: {e.__class__.__name__}")
            logging.debug(f"异常堆栈: ", exc_info=True)
            self.es_client = None  # Reset client on error
            raise ConnectionError(f"Error with Elasticsearch client: {str(e)}")
    
    @property
    def name(self) -> str:
        """Ability name"""
        return "product_search"
    
    @property
    def version(self) -> str:
        """Ability version"""
        return "1.0.0"
    
    async def validate(self, context: Dict[str, Any]) -> bool:
        """
        Validate input parameters
        
        Args:
            context: Dictionary containing input parameters
            
        Returns:
            bool: Whether the parameters are valid
        """
        # Check if keyword parameter is provided
        return "keyword" in context and isinstance(context["keyword"], str)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute ability logic - search for products
        
        Args:
            context: Dictionary containing input parameters
                - keyword: Search keyword
                - size: (optional) Number of results to return
            
        Returns:
            Dict[str, Any]: Search results
                - success: Whether search was successful
                - results: List of products found
                - total: Total number of matches
                - is_fallback: Whether results are fallback recommendations
        """
        keyword = context.get("keyword", "").strip()
        size = context.get("size", self.search_config.get("default_size", 5))
        
        if not keyword:
            logging.warning("收到空的搜索关键词请求")
            return {
                "success": False,
                "error": "Empty search keyword",
                "results": [],
                "total": 0,
                "is_fallback": False
            }
        
        logging.info(f"开始搜索产品，关键词: '{keyword}'，返回数量: {size}")
        
        try:
            # Get elasticsearch client
            logging.debug(f"尝试获取Elasticsearch客户端连接...")
            es_client = self._get_es_client()
            logging.debug(f"成功获取Elasticsearch客户端连接")
            
            # Perform fuzzy search
            logging.info(f"执行模糊搜索，关键词: '{keyword}'")
            search_results = self._fuzzy_search(es_client, keyword, size)
            
            # Check if results were found
            if search_results["total"] == 0 and self.fallback_config.get("enabled", True):
                logging.info(f"关键词 '{keyword}' 未找到结果，启用备选推荐")
                fallback_results = self._get_fallback_recommendations(es_client)
                fallback_results["is_fallback"] = True
                fallback_results["original_keyword"] = keyword
                logging.info(f"返回备选推荐结果，数量: {fallback_results['total']}")
                return fallback_results
            
            # Return search results
            logging.info(f"搜索成功完成，找到 {search_results['total']} 个结果")
            return search_results
                
        except Exception as e:
            logging.error(f"产品搜索错误: {e}")
            logging.error(f"异常类型: {e.__class__.__name__}")
            logging.debug(f"异常堆栈: ", exc_info=True)
            return {
                "success": False,
                "error": f"Search error: {str(e)}",
                "results": [],
                "total": 0,
                "is_fallback": False
            }
    
    def _fuzzy_search(self, es_client: Elasticsearch, keyword: str, size: int) -> Dict[str, Any]:
        """
        Perform fuzzy search in Elasticsearch
        
        Args:
            es_client: Elasticsearch client
            keyword: Search keyword
            size: Number of results to return
            
        Returns:
            Dict[str, Any]: Search results
        """
        index = self.search_config.get("index", "products")
        fuzziness = self.search_config.get("fuzziness", "AUTO")
        min_score = self.search_config.get("min_score", 0.5)
        
        logging.debug(f"准备执行模糊搜索，索引: {index}, 关键词: '{keyword}', 大小: {size}, 模糊度: {fuzziness}")
        
        # Build query - combining multiple query types for better fuzzy matching
        query = {
            "query": {
                "bool": {
                    "should": [
                        # Multi match query for text fields
                        {
                            "multi_match": {
                                "query": keyword,
                                "fields": ["产品名称^3", "品目^2"],  # Boost product name and category
                                "fuzziness": fuzziness,
                                "operator": "or"
                            }
                        },
                        # Wildcard query for style number
                        {
                            "wildcard": {
                                "款号": f"*{keyword}*"
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": size
        }
        
        logging.debug(f"ES搜索查询: {json.dumps(query, ensure_ascii=False)}")
        
        # Execute search with explicit timeout and retries
        max_attempts = 3
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                logging.debug(f"开始第 {attempt+1}/{max_attempts} 次搜索尝试...")
                # Add request_timeout to prevent hanging
                response = es_client.search(
                    index=index, 
                    body=query,
                    request_timeout=30,  # 30 second timeout for search operation
                )
                
                logging.debug(f"ES搜索响应: {json.dumps(response, ensure_ascii=False, default=str)[:500]}...")
                
                # Process results - safely handle different response formats
                try:
                    # For Elasticsearch 7.x+
                    if isinstance(response["hits"]["total"], dict) and "value" in response["hits"]["total"]:
                        total = response["hits"]["total"]["value"]
                        logging.debug(f"使用ES 7.x+格式解析总数: {total}")
                    # For Elasticsearch 6.x and earlier
                    else:
                        total = response["hits"]["total"]
                        logging.debug(f"使用ES 6.x格式解析总数: {total}")
                except (KeyError, TypeError):
                    # Fallback if response format is unexpected
                    total = len(response["hits"]["hits"]) if "hits" in response and "hits" in response["hits"] else 0
                    logging.warning(f"无法从ES响应中确定总命中数，使用命中列表长度代替: {total}")
                
                hits = response["hits"]["hits"]
                logging.debug(f"ES返回原始命中数: {len(hits)}")
                
                # Format results
                results = []
                for hit in hits:
                    source = hit["_source"]
                    score = hit["_score"]
                    
                    # Skip low quality matches
                    if score < min_score:
                        logging.debug(f"跳过低质量匹配: 款号={source.get('款号', '')}, 分数={score} < {min_score}")
                        continue
                        
                    # Format the product data
                    product = {
                        "款号": source.get("款号", ""),
                        "产品名称": source.get("产品名称", ""),
                        "品目": source.get("品目", ""),
                        "score": score,
                        "is_fallback": False
                    }
                    results.append(product)
                
                logging.info(f"成功执行搜索: 关键词='{keyword}', 原始命中={total}, 过滤后结果={len(results)}")
                
                return {
                    "success": True,
                    "results": results,
                    "total": len(results),
                    "original_total": total,
                    "is_fallback": False
                }
                
            except ConnectionError as e:
                last_exception = e
                logging.warning(f"搜索尝试 {attempt+1}/{max_attempts} 失败，连接错误: {str(e)}")
                if attempt < max_attempts - 1:
                    import time
                    retry_delay = 1 * (attempt + 1)
                    logging.debug(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)  # Exponential backoff
                    # Try to reconnect on next attempt
                    try:
                        # Ping to check if connection is still valid
                        logging.debug("尝试ping ES服务器检查连接状态...")
                        if not es_client.ping(request_timeout=5):
                            # Connection is down, reset client to force reconnection
                            logging.debug("ping失败，重置客户端以强制重新连接")
                            self.es_client = None
                            es_client = self._get_es_client()
                    except Exception as ping_error:
                        # Failed to ping, reset client
                        logging.debug(f"ping异常: {str(ping_error)}，重置客户端以强制重新连接")
                        self.es_client = None
                        es_client = self._get_es_client()
            except Exception as e:
                last_exception = e
                logging.warning(f"搜索尝试 {attempt+1}/{max_attempts} 失败，错误: {str(e)}")
                logging.debug(f"异常详情: {e.__class__.__name__}", exc_info=True)
                if attempt < max_attempts - 1:
                    import time
                    retry_delay = 1 * (attempt + 1)
                    logging.debug(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)  # Exponential backoff
        
        # If we got here, all attempts failed
        error_msg = f"经过 {max_attempts} 次尝试后搜索失败。最后错误: {str(last_exception)}"
        logging.error(error_msg)
        raise ConnectionError(error_msg)
    
    def _get_fallback_recommendations(self, es_client: Elasticsearch) -> Dict[str, Any]:
        """
        Get fallback product recommendations when no results found
        
        Args:
            es_client: Elasticsearch client
            
        Returns:
            Dict[str, Any]: Fallback recommendations
        """
        index = self.search_config.get("index", "products")
        fallback_size = self.fallback_config.get("size", 3)
        keywords = self.fallback_config.get("keywords", ["耳环", "手链", "耳饰"])
        
        # Select random keyword from the list
        random_keyword = random.choice(keywords)
        logging.info(f"Using fallback keyword: '{random_keyword}'")
        
        # Build query for fallback
        query = {
            "query": {
                "multi_match": {
                    "query": random_keyword,
                    "fields": ["产品名称", "品目"],
                    "operator": "or"
                }
            },
            "size": fallback_size
        }
        
        # Execute search with explicit timeout and retries
        max_attempts = 3
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                # Add request_timeout to prevent hanging
                response = es_client.search(
                    index=index, 
                    body=query,
                    request_timeout=30,  # 30 second timeout for search operation
                )
                
                # Process results - safely handle different response formats
                try:
                    # For Elasticsearch 7.x+
                    if isinstance(response["hits"]["total"], dict) and "value" in response["hits"]["total"]:
                        total = response["hits"]["total"]["value"]
                    # For Elasticsearch 6.x and earlier
                    else:
                        total = response["hits"]["total"]
                except (KeyError, TypeError):
                    # Fallback if response format is unexpected
                    total = len(response["hits"]["hits"]) if "hits" in response and "hits" in response["hits"] else 0
                    logging.warning("Could not determine total hits count from ES response in fallback, using hits length instead")
                
                hits = response["hits"]["hits"]
                
                # Format results
                results = []
                for hit in hits:
                    source = hit["_source"]
                    
                    # Format the product data
                    product = {
                        "款号": source.get("款号", ""),
                        "产品名称": source.get("产品名称", ""),
                        "品目": source.get("品目", ""),
                        "score": hit["_score"],
                        "is_fallback": True,
                        "fallback_keyword": random_keyword
                    }
                    results.append(product)
                
                return {
                    "success": True,
                    "results": results,
                    "total": len(results),
                    "original_total": total,
                    "is_fallback": True,
                    "fallback_keyword": random_keyword
                }
                
            except ConnectionError as e:
                last_exception = e
                logging.warning(f"Fallback search attempt {attempt+1}/{max_attempts} failed with connection error: {str(e)}")
                if attempt < max_attempts - 1:
                    import time
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                    # Try to reconnect on next attempt
                    try:
                        # Ping to check if connection is still valid
                        if not es_client.ping(request_timeout=5):
                            # Connection is down, reset client to force reconnection
                            self.es_client = None
                            es_client = self._get_es_client()
                    except Exception:
                        # Failed to ping, reset client
                        self.es_client = None
                        es_client = self._get_es_client()
            except Exception as e:
                last_exception = e
                logging.warning(f"Fallback search attempt {attempt+1}/{max_attempts} failed with error: {str(e)}")
                if attempt < max_attempts - 1:
                    import time
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
        
        # If we got here, all attempts failed - since this is fallback, return empty results instead of raising
        logging.error(f"Failed to execute fallback search after {max_attempts} attempts. Last error: {str(last_exception)}")
        return {
            "success": False,
            "results": [],
            "total": 0,
            "original_total": 0,
            "is_fallback": True,
            "fallback_keyword": random_keyword,
            "error": f"Fallback search failed: {str(last_exception)}"
        }
    
    def __del__(self):
        """Clean up resources when object is destroyed"""
        # There's no explicit close method for Elasticsearch client in newer versions
        # Resources will be freed automatically when client is garbage collected
        pass