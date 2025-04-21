#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pmagent",
    version="0.1.0",
    description="프로젝트 관리용 MCP 서버",
    author="PMAgent Team",
    author_email="example@example.com",
    url="https://github.com/contentscoin/pmagent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9"
    ],
    python_requires=">=3.8",
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