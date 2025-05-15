#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP 공통 모듈

MCP(Model Context Protocol) 구현에 필요한 공통 클래스와 함수를 제공합니다.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger(__name__)

class MCPServer:
    """
    MCP(Model Context Protocol) 서버 클래스
    
    MCP 프로토콜을 구현하는 서버입니다.
    """
    
    def __init__(
        self,
        server_name: str,
        server_version: str,
        tools: List[Dict[str, Any]],
        description: str = "",
        tools_data_path: Optional[str] = None
    ):
        """
        MCPServer 초기화
        
        Args:
            server_name: 서버 이름
            server_version: 서버 버전
            tools: 도구 목록
            description: 서버 설명
            tools_data_path: 도구 데이터 저장 경로
        """
        self.server_name = server_name
        self.server_version = server_version
        self.description = description
        self.tools = tools
        self.tools_data_path = tools_data_path
        
        # 도구 로드
        if tools_data_path and os.path.exists(tools_data_path):
            try:
                with open(tools_data_path, "r", encoding="utf-8") as f:
                    self.tools = json.load(f)
            except Exception as e:
                logger.error(f"도구 데이터 로드 중 오류 발생: {str(e)}")
        
        # 도구 함수 매핑
        self.tool_functions = {}
        for tool in self.tools:
            name = tool.get("name")
            function = tool.get("function")
            if name and function:
                self.tool_functions[name] = function
    
    async def invoke_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        도구 호출
        
        Args:
            tool_name: 도구 이름
            parameters: 파라미터
            
        Returns:
            Dict[str, Any]: 결과
            
        Raises:
            ValueError: 도구가 존재하지 않는 경우
        """
        if tool_name not in self.tool_functions:
            raise ValueError(f"도구가 존재하지 않습니다: {tool_name}")
        
        # 도구 함수 호출
        function = self.tool_functions[tool_name]
        try:
            result = await function(parameters)
            return result
        except Exception as e:
            logger.error(f"도구 호출 중 오류 발생: {str(e)}")
            return {"error": str(e)}
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        도구 목록 반환
        
        Returns:
            List[Dict[str, Any]]: 도구 목록
        """
        # 함수 객체 제거된 도구 정보만 반환
        tools_info = []
        for tool in self.tools:
            tool_info = tool.copy()
            if "function" in tool_info:
                del tool_info["function"]
            tools_info.append(tool_info)
        
        return tools_info
    
    def save_tools(self) -> None:
        """도구 정보를 파일에 저장합니다."""
        if not self.tools_data_path:
            return
        
        try:
            # 함수 객체 제거된 도구 정보만 저장
            tools_data = []
            for tool in self.tools:
                tool_data = tool.copy()
                if "function" in tool_data:
                    del tool_data["function"]
                tools_data.append(tool_data)
            
            # JSON 파일로 저장
            with open(self.tools_data_path, "w", encoding="utf-8") as f:
                json.dump(tools_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"도구 데이터 저장 중 오류 발생: {str(e)}") 