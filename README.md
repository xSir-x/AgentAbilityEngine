# AgentAbilityEngine

<div align="center">
    <img src="docs/images/logo.png" alt="AgentAbilityEngine Logo" width="200"/>
</div>

<div align="center">

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![API Documentation](https://img.shields.io/badge/api-documentation-green.svg)](https://your-docs-url.com)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Code Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)]()

</div>

AgentAbilityEngine is a Python Tornado-based Agent Open Platform API framework for rapid development and deployment of various Agent capabilities (such as web crawling, automated analysis, etc.). To implement a new ability for agent,just need to register your ability in the ability manager and deploy this service in your server; Please do the unite test before deploying on the production, and also please cite your work on the ability function, welcome to commit it to the master branch, we all can re-use your implementation and also would appreiciate your works! Yes, lets all colloabrative together and boost this framework to the moon! Annouced by YaChang Tech Inc, Shenzhen, China

## Project Structure

```
AgentAbilityEngine/
├── app/
│   ├── core/                    # Core functionality
│   │   ├── ability_manager.py   # Ability manager
│   │   ├── ability_context.py   # Ability context
│   │   └── base_ability.py      # Base ability abstract class
│   ├── abilities/               # Concrete ability implementations
│   │   ├── crawler/            # Crawler abilities
│   │   └── analyzer/           # Analysis abilities
│   ├── api/                    # API routes
│   │   └── handlers.py
│   └── utils/                  # Utility classes
├── config/                     # Configuration files
├── tests/                     # Unit tests
└── server.py                  # Service entry point
```

## Requirements

- Python 3.8+
- Tornado 6.0+
- aiohttp
- pytest (for testing)

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the service:
```bash
python server.py
```

Service runs at http://localhost:8000 by default

## API Usage

### Call Ability Interface

```bash
POST /api/ability/{ability_name}
Content-Type: application/json

{
    "parameters": {
        // Required parameters for the ability
    }
}
```

Example:
```bash
curl -X POST http://localhost:8000/api/ability/web_crawler \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
```

## Developing New Abilities

1. Create a new ability directory under `app/abilities`
2. Implement the BaseAbility interface:

```python
from app.core.base_ability import BaseAbility

class YourAbility(BaseAbility):
    @property
    def name(self) -> str:
        return "your_ability_name"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def validate(self, context: dict) -> bool:
        # Implement parameter validation logic
        return True
    
    async def execute(self, context: dict) -> dict:
        # Implement ability execution logic
        return {"result": "success"}
```

3. Register the new ability in server.py:

```python
ability_manager.register(YourAbility())
```

## Unit Testing

Run all tests:
```bash
pytest tests/
```

Run specific test:
```bash
pytest tests/test_your_ability.py
```

## Deployment

### Docker Deployment

1. Build image:
```bash
docker build -t agent-ability-engine .`
```

2. Run container:
```bash
docker run -d -p 8000:8000 agent-ability-engine
```

### Traditional Deployment

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure service:
- Modify settings in config/config.yaml

3. Start service:
```bash
python server.py
```

It's recommended to use supervisor or systemd to manage the service process.

## Monitoring and Logging

- Log location: logs/
- Supports Prometheus metrics collection
- Health check endpoint: /health

## Contributing Guidelines

1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License