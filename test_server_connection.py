#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
서버 연결 테스트 스크립트

MCP 서버에 연결하여 도구 목록을 조회합니다.
"""

import sys
import logging
import asyncio
import aiohttp
import json

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 서버 URL 설정
SERVER_URL = "http://localhost:8085"

async def test_connection():
    """서버 연결 테스트"""
    logger.info("=== 서버 연결 테스트 시작 ===")
    
    try:
        # 서버 상태 확인 (루트 경로 확인)
        logger.info(f"서버 상태 확인: {SERVER_URL}")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SERVER_URL}/") as response:
                status_code = response.status
                logger.info(f"루트 경로 접근 상태 코드: {status_code}")
                # 404여도 서버가 실행 중이라면 계속 진행
        
        # 도구 목록 조회
        logger.info("도구 목록 조회")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SERVER_URL}/mcp/tools") as response:
                if response.status == 200:
                    data = await response.json()
                    tools = data.get("tools", [])
                    logger.info(f"도구 목록: {len(tools)}개")
                    for tool in tools:
                        logger.info(f"  - {tool.get('name')}: {tool.get('description')}")
                else:
                    logger.error(f"도구 목록 조회 실패: {response.status}")
                    return False
        
        logger.info("서버 연결 테스트 성공!")
        return True
    
    except Exception as e:
        logger.error(f"서버 연결 테스트 중 오류 발생: {str(e)}")
        return False

async def test_invoke_tool():
    """도구 호출 테스트"""
    logger.info("=== 도구 호출 테스트 시작 ===")
    
    try:
        # list_requests 도구 호출
        logger.info("list_requests 도구 호출")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SERVER_URL}/mcp/invoke", 
                json={"name": "list_requests", "parameters": {"random_string": "test"}}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"응답: {json.dumps(data, indent=2, ensure_ascii=False)}")
                else:
                    logger.error(f"도구 호출 실패: {response.status}")
                    return False
        
        logger.info("도구 호출 테스트 성공!")
        return True
    
    except Exception as e:
        logger.error(f"도구 호출 테스트 중 오류 발생: {str(e)}")
        return False

async def main():
    """메인 함수"""
    # 서버 연결 테스트
    connection_success = await test_connection()
    if not connection_success:
        logger.error("서버 연결 테스트 실패")
        return False
    
    # 도구 호출 테스트
    invoke_success = await test_invoke_tool()
    if not invoke_success:
        logger.error("도구 호출 테스트 실패")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 