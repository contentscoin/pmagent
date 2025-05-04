#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""PMAgent MCP Server

프로젝트 관리를 위한 MCP(Model Context Protocol) 서버와 클라이언트 라이브러리.
"""

__version__ = "0.1.0"

from .task_manager import task_manager
from .mcp_server import app, start_server

__all__ = ["task_manager", "app", "start_server"] 