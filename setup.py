from setuptools import setup, find_packages

setup(
    name="agent-ability-engine",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "tornado>=6.0.0",
        "aiohttp>=3.8.0",
        "pytest>=7.0.0",
        "prometheus-client>=0.16.0",
        "pyyaml>=6.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-tornado>=0.8.1",
    ],
    python_requires=">=3.8",
)