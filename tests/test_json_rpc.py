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

from pmagent.mcp_server import app, jsonrpc_endpoint

class TestJsonRPCEndpoint(unittest.TestCase):
    """JSON-RPC 엔드포인트 테스트"""
    
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
    
    def test_jsonrpc_valid_request(self):
        """유효한 JSON-RPC 요청 테스트"""
        payload = {
            "jsonrpc": "2.0",
            "method": "list_requests",
            "params": {},
            "id": 123
        }
        
        response = self.client.post("/", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 123)
        self.assertIn("result", data)
        self.assertIn("requests", data["result"])
    
    def test_jsonrpc_invalid_jsonrpc_version(self):
        """잘못된 JSON-RPC 버전 테스트"""
        payload = {
            "jsonrpc": "1.0",  # 잘못된 버전
            "method": "list_requests",
            "params": {},
            "id": 124
        }
        
        response = self.client.post("/", json=payload)
        self.assertEqual(response.status_code, 200)  # 에러 응답이라도 상태 코드는 200
        
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 124)
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], -32600)  # 잘못된 요청 에러 코드
    
    def test_jsonrpc_missing_method(self):
        """메소드 누락 테스트"""
        payload = {
            "jsonrpc": "2.0",
            # method 필드 누락
            "params": {},
            "id": 125
        }
        
        response = self.client.post("/", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 125)
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], -32600)
    
    def test_jsonrpc_invalid_method(self):
        """존재하지 않는 메소드 테스트"""
        payload = {
            "jsonrpc": "2.0",
            "method": "non_existent_method",
            "params": {},
            "id": 126
        }
        
        response = self.client.post("/", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 126)
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], -32601)  # 메소드 없음 에러 코드
    
    def test_jsonrpc_invalid_json(self):
        """잘못된 JSON 형식 테스트"""
        # 문법적으로 유효한 JSON이지만 필드가 잘못된 경우
        payload = {
            "invalid_field": "value",  # jsonrpc, method, id 필드 누락
        }
        
        response = self.client.post("/", json=payload)
        # 서버는 200 상태 코드와 함께 JSON-RPC 오류 응답을 반환
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertIn("error", data)
        # 잘못된 요청 에러 코드
        self.assertEqual(data["error"]["code"], -32600)
    
    def test_jsonrpc_list_params(self):
        """리스트 형태의 params 처리 테스트"""
        payload = {
            "jsonrpc": "2.0",
            "method": "list_requests",
            "params": [{"dummy": "value"}],  # 리스트 형태의 params
            "id": 128
        }
        
        response = self.client.post("/", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 128)
        self.assertIn("result", data)
        self.assertIn("requests", data["result"])
    
    def test_jsonrpc_error_handling(self):
        """메소드 실행 중 오류 발생 테스트"""
        payload = {
            "jsonrpc": "2.0",
            "method": "request_planning",
            "params": {
                "originalRequest": "테스트"
                # tasks 필드 누락으로 오류 발생
            },
            "id": 129
        }
        
        response = self.client.post("/", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 129)
        self.assertIn("error", data)
        # HTTP 400 Bad Request를 JSON-RPC 에러로 변환
        self.assertEqual(data["error"]["code"], 400)

if __name__ == "__main__":
    unittest.main() 