#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent MCP 경로(/mcp)를 사용한 WebSocket 연결 테스트 스크립트

이 스크립트는 PMAgent MCP 서버에 WebSocket으로 연결하여 다음을 테스트합니다:
1. 연결 설정
2. 초기화 메시지 전송
3. 도구 목록 요청
4. 프로젝트 목록 조회
"""

import os
import sys
import json
import asyncio
import websockets
import logging
from uuid import uuid4

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def send_jsonrpc_request(websocket, method, params=None):
    """JSON-RPC 요청을 전송합니다."""
    request_id = str(uuid4())
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method
    }
    
    if params is not None:
        request["params"] = params
    
    request_str = json.dumps(request)
    logger.info(f"요청 전송: {request_str}")
    
    await websocket.send(request_str)
    response_str = await websocket.recv()
    
    logger.info(f"응답 수신: {response_str}")
    response = json.loads(response_str)
    
    return response

async def test_websocket_connection(server_url):
    """WebSocket 연결을 테스트합니다."""
    # /mcp 경로 사용
    ws_url = f"{server_url.replace('http://', 'ws://').replace('https://', 'wss://')}/mcp"
    logger.info(f"WebSocket URL: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            logger.info("WebSocket 연결 성공!")
            
            # 1. 초기화 메시지 전송
            logger.info("초기화 메시지 전송 중...")
            response = await send_jsonrpc_request(websocket, "initialize", {
                "client_info": {
                    "name": "테스트 클라이언트",
                    "version": "1.0.0"
                }
            })
            
            if "result" in response:
                logger.info("초기화 성공!")
                server_info = response.get("result", {}).get("server_info", {})
                logger.info(f"서버 정보: {server_info.get('name')} {server_info.get('version')}")
            else:
                logger.error(f"초기화 실패: {response.get('error')}")
                return
            
            # 2. 도구 목록 요청
            logger.info("도구 목록 요청 중...")
            response = await send_jsonrpc_request(websocket, "tools/list")
            
            if "result" in response and "tools" in response["result"]:
                tools = response["result"]["tools"]
                logger.info(f"{len(tools)}개의 도구를 찾았습니다:")
                for tool in tools:
                    logger.info(f"  - {tool['name']}: {tool.get('description', '설명 없음')}")
            else:
                logger.error(f"도구 목록 요청 실패: {response.get('error')}")
                return
            
            # 3. 프로젝트 목록 조회
            logger.info("프로젝트 목록 조회 중...")
            response = await send_jsonrpc_request(websocket, "tools/invoke", {
                "name": "list_projects",
                "parameters": {}
            })
            
            if "result" in response and "projects" in response["result"]:
                projects = response["result"]["projects"]
                logger.info(f"{len(projects)}개의 프로젝트를 찾았습니다:")
                for project in projects:
                    logger.info(f"  - {project['name']} (ID: {project['id']})")
            else:
                logger.error(f"프로젝트 목록 조회 실패: {response.get('error')}")
                return
            
            logger.info("WebSocket 테스트 완료!")
            
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"WebSocket 연결 오류: {e}")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")

async def main():
    """메인 함수"""
    # 로컬 서버로 테스트
    server_url = "http://localhost:8082"
    
    logger.info(f"PMAgent WebSocket 테스트 시작 (서버 URL: {server_url})")
    await test_websocket_connection(server_url)

if __name__ == "__main__":
    asyncio.run(main()) 