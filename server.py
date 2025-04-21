import tornado.ioloop
import tornado.web
import yaml
from app.core.ability_manager import AbilityManager
from app.api.handlers import AbilityHandler, HealthHandler, AbilityListHandler, FileUploadHandler
from app.abilities.crawler.web_crawler import WebCrawlerAbility
from app.abilities.analyzer.sales_analyzer import SalesAnalyzer

def load_config():
    """Load configuration file"""
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def make_app():
    """Create Tornado application"""
    # Load configuration
    config = load_config()
    
    # Initialize ability manager
    ability_manager = AbilityManager()
    
    # Register abilities
    ability_manager.register(WebCrawlerAbility())
    ability_manager.register(SalesAnalyzer())
    
    return tornado.web.Application([
        (r"/api/ability/([^/]+)", AbilityHandler, dict(ability_manager=ability_manager)),
        (r"/api/abilities", AbilityListHandler, dict(ability_manager=ability_manager)),
        (r"/api/upload", FileUploadHandler, dict(config=config)),
        (r"/health", HealthHandler),
    ])

if __name__ == "__main__":
    try:
        config = load_config()
        port = config.get("server", {}).get("port", 8000)
        
        app = make_app()
        app.listen(port)
        print(f"Server is running on port {port}")
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        print("\nServer stopping...")
    except Exception as e:
        print(f"Error starting server: {e}")