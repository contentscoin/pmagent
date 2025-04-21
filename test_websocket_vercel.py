#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent Vercel 배포 버전 HTTP 테스트 스크립트

이 스크립트는 Vercel에 배포된 PMAgent MCP 서버에 HTTP로 연결하여 다음을 테스트합니다:
1. 서버 정보 확인
2. 도구 목록 가져오기
3. 도구 호출
"""

import os
import sys
import json
import requests
import logging
from uuid import uuid4

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def test_http_connection(server_url):
    """HTTP 연결을 테스트합니다."""
    logger.info(f"서버 URL: {server_url}")
    
    try:
        # 1. 서버 정보 확인
        response = requests.get(server_url)
        if response.status_code == 200:
            logger.info(f"서버 정보: {response.text}")
        else:
            logger.error(f"서버 정보 가져오기 실패: {response.status_code}")
            return
        
        # 2. 도구 목록 가져오기
        logger.info("\n도구 목록 가져오는 중...")
        tools_response = requests.get(f"{server_url}/tools")
        if tools_response.status_code == 200:
            tools_data = tools_response.json()
            tools = tools_data.get("tools", [])
            logger.info(f"{len(tools)}개의 도구를 찾았습니다:")
            for tool in tools:
                logger.info(f"  - {tool['name']}: {tool.get('description', '설명 없음')}")
        else:
            logger.error(f"도구 목록 가져오기 실패: {tools_response.status_code}")
            return
            
        # 3. 도구 호출 - 프로젝트 목록 가져오기
        logger.info("\n프로젝트 목록 가져오는 중...")
        invoke_data = {
            "name": "list_projects",
            "parameters": {}
        }
        invoke_response = requests.post(
            f"{server_url}/invoke",
            headers={"Content-Type": "application/json"},
            data=json.dumps(invoke_data)
        )
        
        if invoke_response.status_code == 200:
            result = invoke_response.json()
            logger.info(f"프로젝트 목록: {json.dumps(result, indent=2)}")
        else:
            logger.error(f"프로젝트 목록 가져오기 실패: {invoke_response.status_code}")
            
        logger.info("HTTP 테스트 완료!")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP 요청 오류: {e}")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")

def main():
    """메인 함수"""
    # Vercel 배포 URL 사용
    server_url = "https://pmagent.vercel.app"
    
    logger.info(f"PMAgent Vercel 배포 버전 HTTP 테스트 시작 (서버 URL: {server_url})")
    test_http_connection(server_url)

if __name__ == "__main__":
    main() 