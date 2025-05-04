#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import sys
import asyncio
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import logging
from pathlib import Path
from fastapi.testclient import TestClient
import uuid
from datetime import datetime

# 테스트를 위한 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from pmagent.mcp_server import app, invoke_tool
from pmagent.task_manager import TaskManager

class TestIntegration(unittest.TestCase):
    """MCP 서버와 TaskManager 통합 테스트"""
    
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
        
        # TaskManager 인스턴스 생성
        self.task_manager = TaskManager()
    
    def tearDown(self):
        """각 테스트 종료 후 실행되는 정리"""
        self.patcher.stop()
        self.temp_dir.cleanup()
    
    def test_server_task_manager_sync(self):
        """서버와 TaskManager 간의 동기화 테스트"""
        # 직접 TaskManager로 요청 생성
        direct_result = self.task_manager.request_planning("직접 생성 테스트", [
            {"title": "태스크", "description": "설명"}
        ])
        direct_request_id = direct_result["requestId"]
        
        # API를 통해 이 요청에 접근
        payload = {
            "name": "get_next_task",
            "parameters": {
                "requestId": direct_request_id
            }
        }
        
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 200)
        
        # 응답 검증
        data = response.json()
        self.assertTrue(data["hasNextTask"])
        self.assertEqual(data["task"]["title"], "태스크")
    
    def test_api_task_manager_sync(self):
        """API와 TaskManager 간의 동기화 테스트"""
        # API를 통해 요청 생성
        payload = {
            "name": "request_planning",
            "parameters": {
                "originalRequest": "API 생성 테스트",
                "tasks": [
                    {"title": "API 태스크", "description": "API 설명"}
                ]
            }
        }
        
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 200)
        api_request_id = response.json()["requestId"]
        
        # 직접 TaskManager 인스턴스로 이 요청에 접근
        next_task = self.task_manager.get_next_task(api_request_id)
        
        # 검증
        self.assertTrue(next_task["hasNextTask"])
        self.assertEqual(next_task["task"]["title"], "API 태스크")
    
    def test_multi_client_workflow(self):
        """여러 클라이언트의 워크플로우 테스트"""
        # 첫 번째 클라이언트로 요청 생성
        client1_payload = {
            "name": "request_planning",
            "parameters": {
                "originalRequest": "클라이언트1 테스트",
                "tasks": [
                    {"title": "클라이언트1 태스크", "description": "설명"}
                ]
            }
        }
        
        client1_response = self.client.post("/invoke", json=client1_payload)
        self.assertEqual(client1_response.status_code, 200)
        request_id = client1_response.json()["requestId"]
        
        # 두 번째 클라이언트로 태스크 가져오기
        client2_payload = {
            "name": "get_next_task",
            "parameters": {
                "requestId": request_id
            }
        }
        
        client2_response = self.client.post("/invoke", json=client2_payload)
        self.assertEqual(client2_response.status_code, 200)
        task_id = client2_response.json()["task"]["id"]
        
        # 첫 번째 클라이언트로 태스크 완료
        client1_mark_done_payload = {
            "name": "mark_task_done",
            "parameters": {
                "requestId": request_id,
                "taskId": task_id,
                "completedDetails": "클라이언트1 완료"
            }
        }
        
        client1_mark_done_response = self.client.post("/invoke", json=client1_mark_done_payload)
        self.assertEqual(client1_mark_done_response.status_code, 200)
        
        # 두 번째 클라이언트로 태스크 승인
        client2_approve_payload = {
            "name": "approve_task_completion",
            "parameters": {
                "requestId": request_id,
                "taskId": task_id
            }
        }
        
        client2_approve_response = self.client.post("/invoke", json=client2_approve_payload)
        self.assertEqual(client2_approve_response.status_code, 200)
        
        # 첫 번째 클라이언트로 요청 완료 승인
        client1_approve_request_payload = {
            "name": "approve_request_completion",
            "parameters": {
                "requestId": request_id
            }
        }
        
        client1_approve_request_response = self.client.post("/invoke", json=client1_approve_request_payload)
        self.assertEqual(client1_approve_request_response.status_code, 200)
        
        # 최종 상태 확인
        self.assertEqual(self.task_manager.requests[request_id]["status"], "COMPLETED")
    
    def test_parallel_update_operations(self):
        """병렬 업데이트 작업 테스트"""
        # 요청 생성
        result = self.task_manager.request_planning("병렬 업데이트 테스트", [
            {"title": "태스크1", "description": "설명1"},
            {"title": "태스크2", "description": "설명2"}
        ])
        request_id = result["requestId"]
        
        # 첫 번째 태스크 가져오기
        next_task = self.task_manager.get_next_task(request_id)
        task_id1 = next_task["task"]["id"]
        
        # API를 통해 첫 번째 태스크 완료
        payload1 = {
            "name": "mark_task_done",
            "parameters": {
                "requestId": request_id,
                "taskId": task_id1,
                "completedDetails": "API 완료"
            }
        }
        
        response1 = self.client.post("/invoke", json=payload1)
        self.assertEqual(response1.status_code, 200)
        
        # 직접 TaskManager를 통해 태스크 승인
        self.task_manager.approve_task_completion(request_id, task_id1)
        
        # 두 번째 태스크 가져오기
        next_task = self.task_manager.get_next_task(request_id)
        task_id2 = next_task["task"]["id"]
        
        # API를 통해 두 번째 태스크 완료
        payload2 = {
            "name": "mark_task_done",
            "parameters": {
                "requestId": request_id,
                "taskId": task_id2,
                "completedDetails": "API 완료 2"
            }
        }
        
        response2 = self.client.post("/invoke", json=payload2)
        self.assertEqual(response2.status_code, 200)
        
        # 직접 TaskManager를 통해 태스크 승인
        self.task_manager.approve_task_completion(request_id, task_id2)
        
        # API를 통해 요청 완료 승인
        payload3 = {
            "name": "approve_request_completion",
            "parameters": {
                "requestId": request_id
            }
        }
        
        response3 = self.client.post("/invoke", json=payload3)
        self.assertEqual(response3.status_code, 200)
        
        # 최종 상태 확인
        self.assertEqual(self.task_manager.requests[request_id]["status"], "COMPLETED")
        
        # 모든 태스크가 적절히 처리되었는지 확인
        tasks_progress = self.task_manager._get_tasks_progress(request_id)
        for task in tasks_progress:
            self.assertEqual(task["status"], "DONE")
            self.assertTrue(task["approved"])
    
    def test_api_data_persistence(self):
        """API를 통한 데이터 지속성 테스트"""
        # API로 요청 생성
        payload = {
            "name": "request_planning",
            "parameters": {
                "originalRequest": "지속성 테스트",
                "tasks": [
                    {"title": "지속성 태스크", "description": "설명"}
                ]
            }
        }
        
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 200)
        request_id = response.json()["requestId"]
        
        # 새 TaskManager 인스턴스 생성 (동일한 데이터 디렉토리 사용)
        new_manager = TaskManager()
        
        # 새 인스턴스에서 요청 확인
        self.assertIn(request_id, new_manager.requests)
        self.assertEqual(new_manager.requests[request_id]["originalRequest"], "지속성 테스트")
    
    def test_jsonrpc_integration(self):
        """JSON-RPC 엔드포인트 통합 테스트"""
        # JSON-RPC 형식으로 요청 생성
        jsonrpc_payload = {
            "jsonrpc": "2.0",
            "method": "request_planning",
            "params": {
                "originalRequest": "JSON-RPC 테스트",
                "tasks": [
                    {"title": "JSON-RPC 태스크", "description": "설명"}
                ]
            },
            "id": 1
        }
        
        response = self.client.post("/", json=jsonrpc_payload)
        self.assertEqual(response.status_code, 200)
        request_id = response.json()["result"]["requestId"]
        
        # 직접 TaskManager로 확인
        self.assertIn(request_id, self.task_manager.requests)
        self.assertEqual(self.task_manager.requests[request_id]["originalRequest"], "JSON-RPC 테스트")
    
    def test_invoke_tool_function(self):
        """invoke_tool 함수 직접 테스트"""
        # 요청 생성
        invocation = {
            "name": "request_planning",
            "parameters": {
                "originalRequest": "invoke_tool 테스트",
                "tasks": [
                    {"title": "invoke_tool 태스크", "description": "설명"}
                ]
            }
        }
        
        result = invoke_tool(invocation["name"], invocation["parameters"])
        request_id = result["requestId"]
        
        # 결과 검증
        self.assertIn(request_id, self.task_manager.requests)
        
        # 다음 태스크 가져오기
        next_invocation = {
            "name": "get_next_task",
            "parameters": {
                "requestId": request_id
            }
        }
        
        next_result = invoke_tool(next_invocation["name"], next_invocation["parameters"])
        
        # 결과 검증
        self.assertTrue(next_result["hasNextTask"])
        self.assertEqual(next_result["task"]["title"], "invoke_tool 태스크")
    
    def test_error_propagation(self):
        """오류 전파 테스트"""
        # 존재하지 않는 요청 ID로 다음 태스크 요청 시도
        payload = {
            "name": "get_next_task",
            "parameters": {
                "requestId": "non-existent-id"
            }
        }
        
        response = self.client.post("/invoke", json=payload)
        self.assertEqual(response.status_code, 400)  # Bad Request 예상
        
        # 존재하지 않는 도구 호출 시도
        invalid_payload = {
            "name": "non_existent_tool",
            "parameters": {}
        }
        
        invalid_response = self.client.post("/invoke", json=invalid_payload)
        self.assertEqual(invalid_response.status_code, 404)  # Not Found 예상
    
    def test_concurrent_updates(self):
        """동시 업데이트 테스트"""
        # 요청 생성
        result = self.task_manager.request_planning("동시 업데이트 테스트", [
            {"title": "태스크", "description": "설명"}
        ])
        request_id = result["requestId"]
        
        # 다음 태스크 가져오기
        next_task = self.task_manager.get_next_task(request_id)
        task_id = next_task["task"]["id"]
        
        # 첫 번째 클라이언트로 태스크 업데이트
        payload1 = {
            "name": "update_task",
            "parameters": {
                "requestId": request_id,
                "taskId": task_id,
                "title": "업데이트된 제목 1"
            }
        }
        
        # 두 번째 클라이언트로 동일한 태스크 업데이트
        payload2 = {
            "name": "update_task",
            "parameters": {
                "requestId": request_id,
                "taskId": task_id,
                "title": "업데이트된 제목 2"
            }
        }
        
        # 첫 번째 업데이트 실행
        response1 = self.client.post("/invoke", json=payload1)
        self.assertEqual(response1.status_code, 200)
        
        # 두 번째 업데이트 실행
        response2 = self.client.post("/invoke", json=payload2)
        self.assertEqual(response2.status_code, 200)
        
        # 최종 상태 확인
        task = self.task_manager.tasks[task_id]
        self.assertEqual(task["title"], "업데이트된 제목 2")  # 마지막 업데이트가 적용되어야 함
    
    def test_complete_workflow_integration(self):
        """전체 워크플로우 통합 테스트"""
        # 1. 요청 계획 생성
        planning_payload = {
            "name": "request_planning",
            "parameters": {
                "originalRequest": "전체 통합 테스트",
                "tasks": [
                    {"title": "태스크 1", "description": "설명 1"},
                    {"title": "태스크 2", "description": "설명 2"},
                    {"title": "태스크 3", "description": "설명 3"}
                ],
                "splitDetails": "3개 태스크로 분할됨"
            }
        }
        
        planning_response = self.client.post("/invoke", json=planning_payload)
        self.assertEqual(planning_response.status_code, 200)
        request_id = planning_response.json()["requestId"]
        
        # 2. 첫 번째 태스크 가져오기
        next_task_payload = {
            "name": "get_next_task",
            "parameters": {
                "requestId": request_id
            }
        }
        
        next_task_response = self.client.post("/invoke", json=next_task_payload)
        self.assertEqual(next_task_response.status_code, 200)
        self.assertTrue(next_task_response.json()["hasNextTask"])
        task_id1 = next_task_response.json()["task"]["id"]
        
        # 3. 첫 번째 태스크 완료 및 승인
        mark_done_payload = {
            "name": "mark_task_done",
            "parameters": {
                "requestId": request_id,
                "taskId": task_id1,
                "completedDetails": "태스크 1 완료됨"
            }
        }
        
        mark_done_response = self.client.post("/invoke", json=mark_done_payload)
        self.assertEqual(mark_done_response.status_code, 200)
        
        approve_task_payload = {
            "name": "approve_task_completion",
            "parameters": {
                "requestId": request_id,
                "taskId": task_id1
            }
        }
        
        approve_task_response = self.client.post("/invoke", json=approve_task_payload)
        self.assertEqual(approve_task_response.status_code, 200)
        
        # 4. 두 번째 태스크 가져오기 및 처리
        next_task_response = self.client.post("/invoke", json=next_task_payload)
        self.assertEqual(next_task_response.status_code, 200)
        task_id2 = next_task_response.json()["task"]["id"]
        
        mark_done_payload["parameters"]["taskId"] = task_id2
        mark_done_payload["parameters"]["completedDetails"] = "태스크 2 완료됨"
        self.client.post("/invoke", json=mark_done_payload)
        
        approve_task_payload["parameters"]["taskId"] = task_id2
        self.client.post("/invoke", json=approve_task_payload)
        
        # 5. 세 번째 태스크 가져오기 및 처리
        next_task_response = self.client.post("/invoke", json=next_task_payload)
        self.assertEqual(next_task_response.status_code, 200)
        task_id3 = next_task_response.json()["task"]["id"]
        
        mark_done_payload["parameters"]["taskId"] = task_id3
        mark_done_payload["parameters"]["completedDetails"] = "태스크 3 완료됨"
        self.client.post("/invoke", json=mark_done_payload)
        
        approve_task_payload["parameters"]["taskId"] = task_id3
        self.client.post("/invoke", json=approve_task_payload)
        
        # 6. 모든 태스크 완료 확인
        next_task_response = self.client.post("/invoke", json=next_task_payload)
        self.assertEqual(next_task_response.status_code, 200)
        self.assertFalse(next_task_response.json()["hasNextTask"])
        self.assertTrue(next_task_response.json()["allTasksDone"])
        
        # 7. 요청 완료 승인
        approve_request_payload = {
            "name": "approve_request_completion",
            "parameters": {
                "requestId": request_id
            }
        }
        
        approve_request_response = self.client.post("/invoke", json=approve_request_payload)
        self.assertEqual(approve_request_response.status_code, 200)
        
        # 8. 최종 상태 확인
        self.assertEqual(self.task_manager.requests[request_id]["status"], "COMPLETED")
        
        # 9. 완료된 요청 목록 확인
        list_requests_payload = {
            "name": "list_requests",
            "parameters": {}
        }
        
        list_response = self.client.post("/invoke", json=list_requests_payload)
        self.assertEqual(list_response.status_code, 200)
        
        # 요청 목록에 완료된 요청이 있는지 확인
        requests = list_response.json()["requests"]
        completed_requests = [req for req in requests if req["status"] == "COMPLETED"]
        self.assertTrue(len(completed_requests) > 0)
        
        # 완료된 요청 중에 방금 생성한 요청이 있는지 확인
        request_ids = [req["id"] for req in completed_requests]
        self.assertIn(request_id, request_ids)

if __name__ == "__main__":
    unittest.main() 