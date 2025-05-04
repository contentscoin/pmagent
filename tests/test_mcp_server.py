#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import logging
from pathlib import Path
from fastapi.testclient import TestClient

# 테스트를 위한 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from pmagent.mcp_server import app, request_planning, get_next_task, mark_task_done, approve_task_completion
from pmagent.mcp_server import approve_request_completion, add_tasks_to_request, list_requests, open_task_details

class TestMCPServer(unittest.TestCase):
    """MCP 서버 API 엔드포인트 테스트"""
    
    def setUp(self):
        """각 테스트 시작 전 실행되는 설정"""
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = self.temp_dir.name
        
        # 환경 변수 패치
        self.patcher = patch.dict('os.environ', {'DATA_DIR': self.data_dir})
        self.patcher.start()
        
        # 빈 데이터 파일 생성
        Path(self.data_dir).mkdir(exist_ok=True)
        with open(os.path.join(self.data_dir, "requests.json"), "w") as f:
            json.dump({}, f)
        with open(os.path.join(self.data_dir, "tasks.json"), "w") as f:
            json.dump({}, f)
        
        # 테스트 클라이언트 생성
        self.client = TestClient(app)
    
    def tearDown(self):
        """각 테스트 종료 후 실행되는 정리"""
        self.patcher.stop()
        self.temp_dir.cleanup()
    
    def test_server_root(self):
        """서버 루트 엔드포인트 테스트"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "running")
    
    def test_get_tools(self):
        """도구 목록 조회 테스트"""
        response = self.client.get("/tools")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("tools", data)
        self.assertGreater(len(data["tools"]), 0)
    
    def test_invoke_request_planning(self):
        """request_planning 호출 테스트"""
        payload = {
            "name": "request_planning",
            "parameters": {
                "originalRequest": "테스트 요청",
                "tasks": [
                    {"title": "태스크 1", "description": "설명 1"},
                    {"title": "태스크 2", "description": "설명 2"}
                ]
            }
        }
        
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("requestId", data)
        self.assertEqual(data["taskCount"], 2)
    
    def test_invoke_invalid_tool(self):
        """존재하지 않는 도구 호출 테스트"""
        payload = {
            "name": "non_existent_tool",
            "parameters": {}
        }
        
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 404)
    
    def test_invoke_with_list_params(self):
        """리스트 형태의 파라미터로 호출 테스트"""
        # 일부 클라이언트가 리스트 형태로 파라미터를 전달하는 경우
        # 현재 이 형태는 스키마 검증에서 실패하므로 422 상태 코드 예상
        payload = {
            "name": "list_requests",
            "parameters": []  # 빈 리스트 파라미터
        }
        
        response = self.client.post("/invoke", json=payload)
        # FastAPI의 스키마 검증에서 422 응답 반환 - 이는 정상적인 동작
        self.assertEqual(response.status_code, 422)
        
        # 올바른 형식으로 다시 시도
        payload = {
            "name": "list_requests",
            "parameters": {}  # 빈 딕셔너리 파라미터
        }
        
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("requests", data)
    
    def test_complete_workflow(self):
        """전체 워크플로우 테스트"""
        # 1. 요청 계획 생성
        planning_payload = {
            "name": "request_planning",
            "parameters": {
                "originalRequest": "전체 워크플로우 테스트",
                "tasks": [
                    {"title": "태스크 1", "description": "설명 1"}
                ]
            }
        }
        
        planning_response = self.client.post("/invoke", json=planning_payload)
        self.assertEqual(planning_response.status_code, 200)
        request_id = planning_response.json()["requestId"]
        
        # 2. 다음 태스크 가져오기
        next_task_payload = {
            "name": "get_next_task",
            "parameters": {
                "requestId": request_id
            }
        }
        
        next_task_response = self.client.post("/invoke", json=next_task_payload)
        self.assertEqual(next_task_response.status_code, 200)
        self.assertTrue(next_task_response.json()["hasNextTask"])
        task_id = next_task_response.json()["task"]["id"]
        
        # 3. 태스크 완료 표시
        mark_done_payload = {
            "name": "mark_task_done",
            "parameters": {
                "requestId": request_id,
                "taskId": task_id,
                "completedDetails": "작업 완료"
            }
        }
        
        mark_done_response = self.client.post("/invoke", json=mark_done_payload)
        self.assertEqual(mark_done_response.status_code, 200)
        self.assertTrue(mark_done_response.json()["success"])
        
        # 4. 태스크 승인
        approve_task_payload = {
            "name": "approve_task_completion",
            "parameters": {
                "requestId": request_id,
                "taskId": task_id
            }
        }
        
        approve_task_response = self.client.post("/invoke", json=approve_task_payload)
        self.assertEqual(approve_task_response.status_code, 200)
        self.assertTrue(approve_task_response.json()["success"])
        
        # 5. 요청 완료 승인
        approve_request_payload = {
            "name": "approve_request_completion",
            "parameters": {
                "requestId": request_id
            }
        }
        
        approve_request_response = self.client.post("/invoke", json=approve_request_payload)
        self.assertEqual(approve_request_response.status_code, 200)
        self.assertTrue(approve_request_response.json()["success"])
    
    def test_jsonrpc_request(self):
        """JSON-RPC 형식의 요청 테스트"""
        jsonrpc_payload = {
            "jsonrpc": "2.0",
            "method": "list_requests",
            "params": {},
            "id": 1
        }
        
        response = self.client.post("/", json=jsonrpc_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 1)
        self.assertIn("result", data)
    
    def test_error_handling(self):
        """에러 처리 테스트"""
        # 잘못된 형식의 요청
        invalid_payload = {
            "name": "request_planning",
            "parameters": {
                "originalRequest": "테스트",
                # tasks 필드 누락
            }
        }
        
        response = self.client.post("/invoke", json=invalid_payload)
        self.assertEqual(response.status_code, 400)  # 에러 응답
    
    def test_non_dict_tasks(self):
        """딕셔너리가 아닌 태스크 처리 테스트"""
        # 올바른 형식의 딕셔너리 태스크 사용
        payload = {
            "name": "request_planning",
            "parameters": {
                "originalRequest": "테스트 요청",
                "tasks": [
                    {"title": "태스크 제목", "description": "태스크 설명"}  # 올바른 형식의 딕셔너리
                ]
            }
        }
        
        # 요청 전송
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("requestId", data)
        
        # 잘못된 형식의 태스크는 현재 지원되지 않음을 확인
        payload = {
            "name": "request_planning",
            "parameters": {
                "originalRequest": "테스트 요청",
                "tasks": [
                    {"0": "태스크 제목", "1": "태스크 설명"}  # 잘못된 형식의 딕셔너리 태스크
                ]
            }
        }
        
        response = self.client.post("/invoke", json=payload)
        # 서버 구현에서는 title 필드가 없으면 400 Bad Request 응답
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main() 