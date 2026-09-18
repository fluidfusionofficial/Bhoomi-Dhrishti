from setuptools import setup, find_packages

setup(
    name="bhoomi-common",
    version="0.1.0",
    description="Shared library for all Bhoomi Dhrishti FastAPI services",
    author="Bhoomi Dhrishti Platform Team",
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.111.0",
        "pydantic>=2.7.0",
        "sqlalchemy[asyncio]>=2.0.0",
        "asyncpg>=0.29.0",
        "python-jose[cryptography]>=3.3.0",
        "httpx>=0.27.0",
        "structlog>=24.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0",
            "pytest-asyncio>=0.23",
            "ruff>=0.4",
        ]
    },
)
