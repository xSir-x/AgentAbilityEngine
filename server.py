import tornado.ioloop
import tornado.web
import yaml
import logging  # 添加logging模块
from app.core.ability_manager import AbilityManager
from app.api.handlers import AbilityHandler, HealthHandler, AbilityListHandler, FileUploadHandler
from app.abilities.crawler.web_crawler import WebCrawlerAbility
from app.abilities.analyzer.sales_analyzer import SalesAnalyzer
from app.abilities.auth.login import LoginAbility
from app.abilities.search.product_search import ProductSearchAbility

def load_config():
    """Load configuration file"""
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def make_app():
    """Create Tornado application"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('server.log')
        ]
    )
    
    # Load configuration
    config = load_config()
    
    # Initialize ability manager
    ability_manager = AbilityManager()
    
    # Register abilities
    ability_manager.register(WebCrawlerAbility())
    ability_manager.register(SalesAnalyzer())
    ability_manager.register(LoginAbility())
    ability_manager.register(ProductSearchAbility())
    
    # Create application with logging
    app = tornado.web.Application([
        (r"/api/ability/([^/]+)", AbilityHandler, dict(ability_manager=ability_manager)),
        (r"/api/abilities", AbilityListHandler, dict(ability_manager=ability_manager)),
        (r"/api/upload", FileUploadHandler, dict(config=config)),
        (r"/health", HealthHandler),
    ])
    
    # Log application startup
    logging.info("Application initialized with registered abilities")
    return app

if __name__ == "__main__":
    try:
        config = load_config()
        port = config.get("server", {}).get("port", 8000)
        
        app = make_app()
        app.listen(port)
        logging.info(f"Server is running and listening on port {port}")
        # Log the actual address being bound to
        logging.info(f"Server bound to 0.0.0.0:{port}")
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        logging.info("\nServer stopping...")
    except Exception as e:
        logging.error(f"Error starting server: {e}")