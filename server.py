import tornado.ioloop
import tornado.web
import yaml
from app.core.ability_manager import AbilityManager
from app.api.handlers import AbilityHandler, HealthHandler, AbilityListHandler
from app.abilities.crawler.web_crawler import WebCrawlerAbility

def load_config():
    """Load configuration file"""
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def make_app():
    """Create Tornado application"""
    # Initialize ability manager
    ability_manager = AbilityManager()
    
    # Register crawler ability
    ability_manager.register(WebCrawlerAbility())
    
    return tornado.web.Application([
        (r"/api/ability/([^/]+)", AbilityHandler, dict(ability_manager=ability_manager)),
        (r"/api/abilities", AbilityListHandler, dict(ability_manager=ability_manager)),
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