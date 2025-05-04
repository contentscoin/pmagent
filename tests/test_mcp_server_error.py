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

from pmagent.mcp_server import app, invoke_tool

class TestMCPServerErrors(unittest.TestCase):
    """MCP 서버의 오류 처리 테스트"""
    
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
    
    def test_missing_name_parameter(self):
        """name 매개변수 누락 테스트"""
        payload = {
            "parameters": {
                "requestId": "test-id"
            }
        }
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 422)  # Unprocessable Entity
    
    def test_missing_parameters(self):
        """parameters 매개변수 누락 테스트"""
        payload = {
            "name": "get_next_task"
        }
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 400)  # API는 400 Bad Request 반환
    
    def test_non_existing_tool(self):
        """존재하지 않는 도구 호출 테스트"""
        payload = {
            "name": "non_existing_tool",
            "parameters": {}
        }
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 404)  # Not Found
    
    def test_invalid_json(self):
        """유효하지 않은 JSON 테스트"""
        response = self.client.post(
            "/invoke", 
            headers={"Content-Type": "application/json"},
            content="invalid json data"
        )
        self.assertEqual(response.status_code, 422)  # Unprocessable Entity
    
    @patch('pmagent.mcp_server.invoke_tool')
    def test_internal_server_error(self, mock_invoke_tool):
        """내부 서버 오류 처리 테스트"""
        # 예외를 발생시키도록 모의 설정
        mock_invoke_tool.side_effect = Exception("내부 서버 오류")
        
        payload = {
            "name": "list_requests",
            "parameters": {}
        }
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 200)  # 현재 API 설계에서는 내부 오류도 200 반환
    
    def test_task_errors(self):
        """태스크 관련 오류 테스트"""
        # 존재하지 않는 요청 ID로 태스크 완료 요청
        payload = {
            "name": "mark_task_done",
            "parameters": {
                "requestId": "non-existent-id",
                "taskId": "task-id"
            }
        }
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 400)  # API는 400 Bad Request 반환
        
        # 존재하지 않는 요청 ID로 다음 태스크 요청
        payload = {
            "name": "get_next_task",
            "parameters": {
                "requestId": "non-existent-id"
            }
        }
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 400)  # API는 400 Bad Request 반환
        
        # 존재하지 않는 요청 ID로 요청 완료 승인
        payload = {
            "name": "approve_request_completion",
            "parameters": {
                "requestId": "non-existent-id"
            }
        }
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 400)  # API는 400 Bad Request 반환

if __name__ == "__main__":
    unittest.main() 