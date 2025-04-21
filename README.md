# AgentAbilityEngine

AgentAbilityEngine 是一个基于 Python Tornado 的 Agent 开放平台 API 框架，用于快速开发和部署各种 Agent 能力（如爬虫、自动化分析等）。

## 项目结构

```
AgentAbilityEngine/
├── app/
│   ├── core/                    # 核心功能
│   │   ├── ability_manager.py   # 能力管理器
│   │   ├── ability_context.py   # 能力上下文
│   │   └── base_ability.py      # 基础能力抽象类
│   ├── abilities/               # 具体能力实现
│   │   ├── crawler/            # 爬虫能力
│   │   └── analyzer/           # 分析能力
│   ├── api/                    # API路由
│   │   └── handlers.py
│   └── utils/                  # 工具类
├── config/                     # 配置文件
├── tests/                     # 单元测试
└── server.py                  # 服务入口
```

## 环境要求

- Python 3.8+
- Tornado 6.0+
- aiohttp
- pytest (用于测试)

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动服务：
```bash
python server.py
```

服务默认运行在 http://localhost:8000

## API 使用说明

### 调用能力接口

```bash
POST /api/ability/{ability_name}
Content-Type: application/json

{
    "parameters": {
        // 能力所需参数
    }
}
```

示例：
```bash
curl -X POST http://localhost:8000/api/ability/web_crawler \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
```

## 开发新能力

1. 在 `app/abilities` 下创建新的能力目录
2. 实现 BaseAbility 接口：

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
        # 实现参数验证逻辑
        return True
    
    async def execute(self, context: dict) -> dict:
        # 实现能力执行逻辑
        return {"result": "success"}
```

3. 在 server.py 中注册新能力：

```python
ability_manager.register(YourAbility())
```

## 单元测试

运行所有测试：
```bash
pytest tests/
```

运行特定测试：
```bash
pytest tests/test_your_ability.py
```

## 部署

### Docker 部署

1. 构建镜像：
```bash
docker build -t agent-ability-engine .
```

2. 运行容器：
```bash
docker run -d -p 8000:8000 agent-ability-engine
```

### 传统部署

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置服务：
- 修改 config/config.yaml 中的配置

3. 启动服务：
```bash
python server.py
```

建议使用 supervisor 或 systemd 管理服务进程。

## 监控与日志

- 日志位置：logs/
- 支持 Prometheus 指标采集
- 健康检查接口：/health

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License