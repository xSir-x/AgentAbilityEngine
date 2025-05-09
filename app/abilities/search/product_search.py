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
                use_ssl = self.es_config.get("use_ssl", True)  # Default to True for Huawei Cloud
                
                # Construct connection URL
                es_url = f"{'https' if use_ssl else 'http'}://{host}:{port}"
                logging.info(f"Connecting to Huawei Cloud Elasticsearch at {es_url}")
                
                # Create Elasticsearch client with simpler configuration
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
                if self.es_client.ping():
                    es_info = self.es_client.info()
                    logging.info(f"Connected to Elasticsearch version {es_info['version']['number']}")
                else:
                    logging.error("Cannot ping Elasticsearch")
                    self.es_client = None
                    raise ConnectionError("Cannot ping Elasticsearch")
            
            return self.es_client
        except ConnectionError as e:
            logging.error(f"Elasticsearch connection error: {e}")
            self.es_client = None  # Reset client on connection error
            raise ConnectionError(f"Failed to connect to Elasticsearch: {str(e)}")
        except Exception as e:
            logging.error(f"Elasticsearch client error: {e}")
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
            return {
                "success": False,
                "error": "Empty search keyword",
                "results": [],
                "total": 0,
                "is_fallback": False
            }
        
        logging.info(f"Searching for products with keyword: '{keyword}'")
        
        try:
            # Get elasticsearch client
            es_client = self._get_es_client()
            
            # Perform fuzzy search
            search_results = self._fuzzy_search(es_client, keyword, size)
            
            # Check if results were found
            if search_results["total"] == 0 and self.fallback_config.get("enabled", True):
                logging.info(f"No results found for '{keyword}', using fallback recommendations")
                fallback_results = self._get_fallback_recommendations(es_client)
                fallback_results["is_fallback"] = True
                fallback_results["original_keyword"] = keyword
                return fallback_results
            
            # Return search results
            return search_results
                
        except Exception as e:
            logging.error(f"Product search error: {e}", exc_info=True)
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
                    logging.warning("Could not determine total hits count from ES response, using hits length instead")
                
                hits = response["hits"]["hits"]
                
                # Format results
                results = []
                for hit in hits:
                    source = hit["_source"]
                    score = hit["_score"]
                    
                    # Skip low quality matches
                    if score < min_score:
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
                
                return {
                    "success": True,
                    "results": results,
                    "total": len(results),
                    "original_total": total,
                    "is_fallback": False
                }
                
            except ConnectionError as e:
                last_exception = e
                logging.warning(f"Search attempt {attempt+1}/{max_attempts} failed with connection error: {str(e)}")
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
                logging.warning(f"Search attempt {attempt+1}/{max_attempts} failed with error: {str(e)}")
                if attempt < max_attempts - 1:
                    import time
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
        
        # If we got here, all attempts failed
        raise ConnectionError(f"Failed to execute search after {max_attempts} attempts. Last error: {str(last_exception)}")
    
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