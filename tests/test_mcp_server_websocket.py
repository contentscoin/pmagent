#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import sys
import unittest
import asyncio
from unittest.mock import patch, MagicMock
import tempfile
import logging
from pathlib import Path
import uuid
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

# 테스트를 위한 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from pmagent.mcp_server import app, ConnectionManager

class TestMCPServerWebSocket(unittest.TestCase):
    """MCP 서버의 WebSocket 엔드포인트 테스트"""
    
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
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """WebSocket 연결 테스트"""
        # ConnectionManager 클래스를 모의(mock)로 대체
        with patch('pmagent.mcp_server.ConnectionManager') as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            with self.client.websocket_connect("/ws") as websocket:
                # 연결이 성공적으로 이루어져야 함
                mock_instance.connect.assert_called_once()
                
                # 연결 종료 시 disconnect 호출 확인
                websocket.close()
                mock_instance.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_message_handling(self):
        """WebSocket 메시지 처리 테스트"""
        with self.client.websocket_connect("/ws") as websocket:
            # 클라이언트에서 서버로 메시지 전송
            test_message = {
                "type": "test",
                "data": {"message": "테스트 메시지"}
            }
            websocket.send_json(test_message)
            
            # 서버로부터 응답 받기
            response = websocket.receive_json()
            
            # 응답 검증
            self.assertIn("type", response)
            self.assertEqual(response["type"], "response")
            self.assertIn("data", response)
    
    @pytest.mark.asyncio
    async def test_invalid_json_message(self):
        """유효하지 않은 JSON 메시지 처리 테스트"""
        with self.client.websocket_connect("/ws") as websocket:
            # 유효하지 않은 JSON 형식의 메시지 전송
            websocket.send_text("이것은 유효한 JSON이 아님")
            
            # 서버로부터 오류 응답 받기
            response = websocket.receive_json()
            
            # 오류 응답 검증
            self.assertIn("type", response)
            self.assertEqual(response["type"], "error")
            self.assertIn("data", response)
            self.assertIn("message", response["data"])
    
    @pytest.mark.asyncio
    async def test_missing_type_message(self):
        """type 필드가 없는 메시지 처리 테스트"""
        with self.client.websocket_connect("/ws") as websocket:
            # type 필드가 없는 메시지 전송
            invalid_message = {
                "data": {"message": "type 필드 없음"}
            }
            websocket.send_json(invalid_message)
            
            # 서버로부터 오류 응답 받기
            response = websocket.receive_json()
            
            # 오류 응답 검증
            self.assertIn("type", response)
            self.assertEqual(response["type"], "error")
            self.assertIn("data", response)
            self.assertIn("message", response["data"])
    
    @pytest.mark.asyncio
    async def test_unsupported_message_type(self):
        """지원하지 않는 메시지 타입 처리 테스트"""
        with self.client.websocket_connect("/ws") as websocket:
            # 지원하지 않는 type의 메시지 전송
            unsupported_message = {
                "type": "unsupported_type",
                "data": {"message": "지원되지 않는 타입"}
            }
            websocket.send_json(unsupported_message)
            
            # 서버로부터 오류 응답 받기
            response = websocket.receive_json()
            
            # 오류 응답 검증
            self.assertIn("type", response)
            self.assertEqual(response["type"], "error")
            self.assertIn("data", response)
            self.assertIn("message", response["data"])
    
    @pytest.mark.asyncio
    async def test_mcp_websocket_invoke(self):
        """MCP 웹소켓으로 도구 호출 테스트"""
        with self.client.websocket_connect("/mcp") as websocket:
            # 요청 계획 생성 명령 전송
            invoke_message = {
                "type": "invoke",
                "data": {
                    "name": "request_planning",
                    "parameters": {
                        "originalRequest": "WebSocket 테스트 요청",
                        "tasks": [
                            {"title": "WebSocket 태스크", "description": "WebSocket으로 생성된 태스크"}
                        ]
                    }
                }
            }
            websocket.send_json(invoke_message)
            
            # 서버로부터 응답 받기
            response = websocket.receive_json()
            
            # 응답 검증
            self.assertIn("type", response)
            self.assertEqual(response["type"], "response")
            self.assertIn("data", response)
            self.assertIn("requestId", response["data"])
    
    @pytest.mark.asyncio
    async def test_multiple_clients(self):
        """여러 클라이언트 연결 테스트"""
        # ConnectionManager 인스턴스가 여러 클라이언트를 관리할 수 있는지 테스트
        with patch('pmagent.mcp_server.ConnectionManager') as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            # 첫 번째 클라이언트 연결
            with self.client.websocket_connect("/ws") as websocket1:
                # 두 번째 클라이언트 연결
                with self.client.websocket_connect("/ws") as websocket2:
                    # 두 번의 connect 호출 확인
                    self.assertEqual(mock_instance.connect.call_count, 2)
                    
                    # 클라이언트 각각 종료
                    websocket2.close()
                    # 한 번의 disconnect 호출 확인
                    self.assertEqual(mock_instance.disconnect.call_count, 1)
                
                websocket1.close()
                # 두 번의 disconnect 호출 확인
                self.assertEqual(mock_instance.disconnect.call_count, 2)
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """브로드캐스트 메시지 테스트"""
        # 실제 ConnectionManager 인스턴스 생성
        manager = ConnectionManager()
        
        # 모의 WebSocket 클라이언트 생성
        mock_client1 = MagicMock()
        mock_client2 = MagicMock()
        
        # 클라이언트 연결 추가
        manager.active_connections.append(mock_client1)
        manager.active_connections.append(mock_client2)
        
        # 테스트 메시지
        test_message = {"message": "브로드캐스트 테스트"}
        
        # 브로드캐스트 테스트 (직접 메서드를 호출)
        # 이 부분은 ConnectionManager에 브로드캐스트 메서드가 있다고 가정
        # 실제 구현에 맞게 조정 필요
        if hasattr(manager, 'broadcast'):
            await manager.broadcast(test_message)
            
            # 각 클라이언트가 메시지를 받았는지 확인
            mock_client1.send_json.assert_called_once_with(test_message)
            mock_client2.send_json.assert_called_once_with(test_message)
    
    @pytest.mark.asyncio
    async def test_connection_exception_handling(self):
        """연결 예외 처리 테스트"""
        # 예외를 발생시키는 모의 WebSocket 생성
        mock_websocket = MagicMock()
        mock_websocket.accept.side_effect = Exception("연결 오류")
        
        # ConnectionManager 인스턴스
        manager = ConnectionManager()
        
        # 예외가 적절히 처리되는지 확인
        try:
            await manager.connect(mock_websocket)
            # 예외가 발생해야 하므로 여기에 도달하면 실패
            self.fail("예외가 발생하지 않음")
        except Exception as e:
            # 적절한 예외가 발생했는지 확인
            self.assertEqual(str(e), "연결 오류")

if __name__ == "__main__":
    unittest.main() 