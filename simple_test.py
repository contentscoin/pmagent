#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
간단한 MCP 서버 API 테스트 스크립트
"""

import requests
import json

# 서버 URL
SERVER_URL = "http://localhost:8086"

# 1. 도구 목록 조회
print("===== 도구 목록 조회 =====")
try:
    response = requests.get(f"{SERVER_URL}/mcp/tools")
    if response.status_code == 200:
        tools = response.json().get("tools", [])
        print(f"도구 목록 ({len(tools)}개):")
        for tool in tools:
            print(f"  - {tool.get('name')}: {tool.get('description', '설명 없음')}")
        with open("tools_result.json", "w", encoding="utf-8") as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=2)
    else:
        print(f"도구 목록 조회 실패: {response.status_code}, {response.text}")
except Exception as e:
    print(f"오류 발생: {str(e)}")

# 2. 태스크 요청 테스트
print("\n===== 태스크 요청 테스트 =====")
try:
    payload = {
        "name": "request_planning",
        "parameters": {
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
    }
    
    print(f"요청: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    response = requests.post(f"{SERVER_URL}/mcp/invoke", json=payload)
    print(f"상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"응답: {json.dumps(result, ensure_ascii=False, indent=2)}")
        with open("planning_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        print(f"요청 실패: {response.text}")
except Exception as e:
    print(f"오류 발생: {str(e)}")

# 3. 목록 조회 테스트
print("\n===== 요청 목록 조회 테스트 =====")
try:
    payload = {
        "name": "list_requests",
        "parameters": {
            "random_string": "test"
        }
    }
    
    print(f"요청: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    response = requests.post(f"{SERVER_URL}/mcp/invoke", json=payload)
    print(f"상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"응답: {json.dumps(result, ensure_ascii=False, indent=2)}")
        with open("list_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        print(f"요청 실패: {response.text}")
except Exception as e:
    print(f"오류 발생: {str(e)}") 