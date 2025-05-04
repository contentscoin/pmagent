#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cursor MCP 서버 등록 스크립트

PMAgent MCP 서버를 Cursor 편집기에 등록하기 위한 스크립트입니다.
"""

import os
import json
import argparse
import subprocess
import sys
from typing import Dict, Any, List, Optional

# 서버 설정
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8082
DEFAULT_PROTOCOL = "http"

# 서버 정보 (기본값)
SERVER_INFO = {
    "name": "pmagent",
    "version": "0.1.0",
    "description": "PM Agent MCP Server - 프로젝트 관리 에이전트",
    "server_url": f"{DEFAULT_PROTOCOL}://{DEFAULT_HOST}:{DEFAULT_PORT}",
    "methods": [
        {
            "name": "create_session",
            "description": "새 세션 생성",
            "parameters": {}
        },
        {
            "name": "request_planning",
            "description": "새 요청 등록 및 태스크 계획",
            "parameters": {
                "originalRequest": "원래 요청",
                "tasks": "태스크 목록",
                "splitDetails": "분할 세부 정보 (선택)"
            }
        },
        {
            "name": "get_next_task",
            "description": "다음 대기 중인 태스크 가져오기",
            "parameters": {
                "requestId": "요청 ID"
            }
        },
        {
            "name": "mark_task_done",
            "description": "태스크 완료 처리",
            "parameters": {
                "requestId": "요청 ID",
                "taskId": "태스크 ID",
                "completedDetails": "완료 세부 정보 (선택)"
            }
        },
        {
            "name": "approve_task_completion",
            "description": "태스크 완료 승인",
            "parameters": {
                "requestId": "요청 ID",
                "taskId": "태스크 ID"
            }
        },
        {
            "name": "approve_request_completion",
            "description": "전체 요청 완료 승인",
            "parameters": {
                "requestId": "요청 ID"
            }
        },
        {
            "name": "create_agent",
            "description": "새 에이전트 생성",
            "parameters": {
                "type": "에이전트 타입 (pm, designer, frontend, backend, ai_engineer)",
                "name": "에이전트 이름",
                "config": "에이전트 설정 (선택)"
            }
        },
        {
            "name": "get_agent",
            "description": "에이전트 정보 조회",
            "parameters": {
                "agentId": "에이전트 ID"
            }
        },
        {
            "name": "list_agents",
            "description": "에이전트 목록 조회",
            "parameters": {}
        },
        {
            "name": "assign_task_to_agent",
            "description": "에이전트에 태스크 할당",
            "parameters": {
                "agentId": "에이전트 ID",
                "task": "태스크 정보"
            }
        },
        {
            "name": "get_agent_result",
            "description": "에이전트 태스크 결과 조회",
            "parameters": {
                "agentId": "에이전트 ID",
                "taskId": "태스크 ID"
            }
        },
        {
            "name": "export_data",
            "description": "데이터 내보내기",
            "parameters": {
                "sessionId": "세션 ID"
            }
        },
        {
            "name": "import_data",
            "description": "데이터 가져오기",
            "parameters": {
                "sessionId": "세션 ID",
                "fromFile": "파일에서 가져오기 여부"
            }
        }
    ]
}

def get_cursor_cmd() -> str:
    """
    현재 OS에 맞는 Cursor 명령을 반환합니다.
    
    Returns:
        str: Cursor 명령
    """
    if sys.platform == "darwin":  # macOS
        return "/Applications/Cursor.app/Contents/MacOS/Cursor"
    elif sys.platform == "win32":  # Windows
        program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
        return f"{program_files}\\Cursor\\Cursor.exe"
    else:  # Linux 또는 기타
        return "cursor"

def register_mcp_server(server_url: str, server_info: Dict[str, Any]) -> bool:
    """
    MCP 서버를 Cursor에 등록합니다.
    
    Args:
        server_url: 서버 URL
        server_info: 서버 정보
        
    Returns:
        bool: 등록 성공 여부
    """
    try:
        # Cursor 명령 가져오기
        cursor_cmd = get_cursor_cmd()
        
        # MCP 등록 명령
        mcp_cmd = [cursor_cmd, "--add-mcp-server", server_url]
        
        # Cursor 실행
        subprocess.run(mcp_cmd, check=True)
        
        print(f"✅ MCP 서버가 Cursor에 성공적으로 등록되었습니다: {server_url}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ MCP 서버 등록 실패: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

def start_server(host: str, port: int) -> subprocess.Popen:
    """
    PMAgent MCP 서버를 시작합니다.
    
    Args:
        host: 호스트
        port: 포트
        
    Returns:
        subprocess.Popen: 서버 프로세스
    """
    try:
        # 서버 실행 명령
        server_cmd = [sys.executable, "server.py", "--host", host, "--port", str(port)]
        
        # 서버 시작 (백그라운드에서 실행)
        process = subprocess.Popen(server_cmd)
        
        print(f"✅ PMAgent MCP 서버가 {host}:{port}에서 시작되었습니다.")
        return process
    except Exception as e:
        print(f"❌ 서버 시작 실패: {str(e)}")
        sys.exit(1)

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='PMAgent MCP 서버 Cursor 등록 스크립트')
    parser.add_argument('--host', default=DEFAULT_HOST, help='서버 호스트 (기본값: localhost)')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='서버 포트 (기본값: 8082)')
    parser.add_argument('--register-only', action='store_true', help='등록만 수행 (서버 시작 안함)')
    parser.add_argument('--start-only', action='store_true', help='서버 시작만 수행 (등록 안함)')
    
    args = parser.parse_args()
    
    # 서버 URL 생성
    server_url = f"{DEFAULT_PROTOCOL}://{args.host}:{args.port}"
    SERVER_INFO["server_url"] = server_url
    
    # 서버 시작 (--register-only가 지정되지 않은 경우)
    server_process = None
    if not args.register_only:
        server_process = start_server(args.host, args.port)
    
    # MCP 서버 등록 (--start-only가 지정되지 않은 경우)
    if not args.start_only:
        register_mcp_server(server_url, SERVER_INFO)
    
    # 서버 프로세스가 있는 경우 종료 대기
    if server_process:
        try:
            print("서버가 실행 중입니다. Ctrl+C를 눌러 종료할 수 있습니다.")
            server_process.wait()
        except KeyboardInterrupt:
            print("\n사용자에 의해 서버가 종료되었습니다.")
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    main() 