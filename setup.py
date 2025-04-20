#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pmagent",
    version="0.1.0",
    author="PMAgent Team",
    author_email="pmagent@example.com",
    description="프로젝트 관리를 위한 MCP 에이전트 및 클라이언트 라이브러리",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pmagent",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[
        "aiohttp>=3.7.0",
        "requests>=2.25.0",
        "pydantic>=1.8.0",
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "flake8>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "tox>=3.24.0",
            "pre-commit>=2.17.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pmagent-server=pmagent.server:main",
            "pmagent-client=pmagent.test_client:cli_entry_point",
        ],
    },
) 