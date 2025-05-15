#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent MCP 서버 간단 테스트 클라이언트

이 스크립트는 간단한 테스트를 위한 클라이언트입니다.
"""

import sys
import json
import logging
import requests

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 서버 URL
SERVER_URL = "http://localhost:8085"

# 도구 목록 가져오기
def get_tools():
    try:
        response = requests.get(f"{SERVER_URL}/mcp/tools")
        if response.status_code == 200:
            return response.json().get("tools", [])
        else:
            logger.error(f"도구 목록 조회 실패: {response.text}")
            return []
    except Exception as e:
        logger.error(f"도구 목록 조회 중 오류 발생: {str(e)}")
        return []

# 직접 JSON-RPC 요청
def send_jsonrpc(method, params=None):
    """JSON-RPC 요청을 보냅니다."""
    if params is None:
        params = {}
    
    # JSON-RPC 2.0 규격에 맞게 요청 생성
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    
    logger.info(f"JSON-RPC 요청: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/mcp/invoke",
            json={"name": method, "parameters": params}
        )
        
        logger.info(f"응답 상태 코드: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            logger.info(f"응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        else:
            logger.error(f"요청 실패: {response.text}")
            return None
    except Exception as e:
        logger.error(f"JSON-RPC 요청 중 오류 발생: {str(e)}")
        return None

# 요청 계획 생성
def create_request_planning():
    params = {
        "originalRequest": "웹 애플리케이션 개발 프로젝트 계획",
        "tasks": [
            {
                "title": "요구사항 분석",
                "description": "프로젝트 요구사항을 분석하고 기능 목록 작성"
            },
            {
                "title": "디자인 시안 작성",
                "description": "UI/UX 디자인 시안 작성 및 검토"
            }
        ]
    }
    
    return send_jsonrpc("request_planning", params)

# 요청 목록 조회
def list_requests():
    return send_jsonrpc("list_requests", {"random_string": "test"})

# 메인 함수
def main():
    # 도구 목록 조회
    logger.info("도구 목록 조회 중...")
    tools = get_tools()
    logger.info(f"사용 가능한 도구: {[tool['name'] for tool in tools]}")
    
    # 빈 요청 목록 조회
    logger.info("요청 목록 조회 중...")
    requests_list_before = list_requests()
    
    # 요청 계획 생성
    logger.info("요청 계획 생성 중...")
    planning_result = create_request_planning()
    
    if planning_result and "result" in planning_result:
        # 요청 목록 다시 조회
        logger.info("요청 목록 다시 조회 중...")
        requests_list_after = list_requests()

if __name__ == "__main__":
    main() 