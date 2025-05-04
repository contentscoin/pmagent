#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import sys
import unittest
from unittest.mock import patch
import tempfile
import logging
from pathlib import Path
from fastapi.testclient import TestClient

# 테스트를 위한 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from pmagent.mcp_server import app

class TestSmitheryEndpoint(unittest.TestCase):
    """Smithery 메타데이터 엔드포인트 테스트"""
    
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
    
    def test_smithery_simple_endpoint(self):
        """Smithery 메타데이터 엔드포인트 테스트"""
        response = self.client.get("/smithery-simple.json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("name", data)
        self.assertIn("tools", data)
        self.assertIn("description", data)
        self.assertIn("version", data)
        self.assertIn("authorization", data)

if __name__ == "__main__":
    unittest.main() 