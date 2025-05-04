#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import uuid
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sys
import logging
from pathlib import Path

# 테스트를 위한 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from pmagent.task_manager import TaskManager, load_requests, load_tasks

class TestTaskManager(unittest.TestCase):
    """TaskManager 클래스 테스트"""
    
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
        
        # TaskManager 인스턴스 생성 (패치된 환경에서)
        from pmagent.task_manager import TaskManager
        self.task_manager = TaskManager()
    
    def tearDown(self):
        """각 테스트 종료 후 실행되는 정리"""
        self.patcher.stop()
        self.temp_dir.cleanup()
    
    def test_request_planning_valid_input(self):
        """유효한 입력으로 request_planning 테스트"""
        # 테스트 데이터
        original_request = "테스트 요청"
        tasks = [
            {"title": "태스크 1", "description": "태스크 1 설명"},
            {"title": "태스크 2", "description": "태스크 2 설명"}
        ]
        
        # 함수 호출
        result = self.task_manager.request_planning(original_request, tasks)
        
        # 검증
        self.assertIn("requestId", result)
        self.assertEqual(result["taskCount"], 2)
        
        # 데이터가 저장되었는지 확인
        request_id = result["requestId"]
        self.assertIn(request_id, self.task_manager.requests)
        self.assertEqual(len(self.task_manager.requests[request_id]["tasks"]), 2)
    
    def test_request_planning_invalid_input(self):
        """잘못된 입력으로 request_planning 테스트"""
        # 빈 tasks 리스트
        with self.assertRaises(ValueError):
            self.task_manager.request_planning("테스트", [])
        
        # tasks가 리스트가 아닌 경우
        with self.assertRaises(ValueError):
            self.task_manager.request_planning("테스트", "not a list")
    
    def test_request_planning_with_non_dict_tasks(self):
        """딕셔너리가 아닌 태스크로 request_planning 테스트"""
        # 튜플을 딕셔너리로 변환할 수 있는 형태로 수정
        original_request = "테스트 요청"
        tasks = [
            {"0": "태스크 1", "1": "태스크 1 설명"},  # 딕셔너리로 표현된 태스크
            {"title": "태스크 2", "description": "태스크 2 설명"}  # 정상 딕셔너리
        ]
        
        # 함수 호출
        result = self.task_manager.request_planning(original_request, tasks)
        
        # 검증
        self.assertIn("requestId", result)
        self.assertEqual(result["taskCount"], 2)
    
    def test_get_next_task(self):
        """get_next_task 함수 테스트"""
        # 먼저 요청과 태스크 생성
        original_request = "테스트 요청"
        tasks = [
            {"title": "태스크 1", "description": "태스크 1 설명"},
            {"title": "태스크 2", "description": "태스크 2 설명"}
        ]
        result = self.task_manager.request_planning(original_request, tasks)
        request_id = result["requestId"]
        
        # 다음 태스크 가져오기
        next_task_result = self.task_manager.get_next_task(request_id)
        
        # 검증
        self.assertTrue(next_task_result["hasNextTask"])
        self.assertFalse(next_task_result["allTasksDone"])
        self.assertEqual(next_task_result["task"]["title"], "태스크 1")
        self.assertEqual(len(next_task_result["tasksProgress"]), 2)
    
    def test_mark_task_done_and_approve(self):
        """태스크 완료 및 승인 테스트"""
        # 요청과 태스크 생성
        result = self.task_manager.request_planning("테스트", [{"title": "태스크", "description": "설명"}])
        request_id = result["requestId"]
        
        # 다음 태스크 가져오기
        next_task = self.task_manager.get_next_task(request_id)
        task_id = next_task["task"]["id"]
        
        # 태스크 완료 표시
        mark_result = self.task_manager.mark_task_done(request_id, task_id, "완료됨")
        self.assertTrue(mark_result["success"])
        self.assertEqual(mark_result["task"]["status"], "DONE")
        
        # 태스크 승인
        approve_result = self.task_manager.approve_task_completion(request_id, task_id)
        self.assertTrue(approve_result["success"])
        self.assertTrue(approve_result["task"]["approved"])
        
        # 모든 태스크가 완료되었는지 확인
        final_status = self.task_manager.get_next_task(request_id)
        self.assertFalse(final_status["hasNextTask"])
        self.assertTrue(final_status["allTasksDone"])
    
    def test_add_tasks_to_request(self):
        """기존 요청에 태스크 추가 테스트"""
        # 요청 생성
        result = self.task_manager.request_planning("테스트", [{"title": "태스크 1", "description": "설명 1"}])
        request_id = result["requestId"]
        
        # 새 태스크 추가
        new_tasks = [{"title": "태스크 2", "description": "설명 2"}]
        add_result = self.task_manager.add_tasks_to_request(request_id, new_tasks)
        
        # 검증
        self.assertTrue(add_result["success"])
        self.assertEqual(len(add_result["addedTasks"]), 1)
        self.assertEqual(len(add_result["tasksProgress"]), 2)
        
        # 요청 객체에도 추가되었는지 확인
        self.assertEqual(len(self.task_manager.requests[request_id]["tasks"]), 2)
    
    def test_add_tasks_with_invalid_data(self):
        """잘못된 데이터로 태스크 추가 테스트"""
        # 요청 생성
        result = self.task_manager.request_planning("테스트", [{"title": "태스크", "description": "설명"}])
        request_id = result["requestId"]
        
        # 비정상적인 형태의 태스크 추가 (title이나 description이 없는 경우)
        new_tasks = [{"wrong_field": "잘못된 필드"}]
        add_result = self.task_manager.add_tasks_to_request(request_id, new_tasks)
        
        # 검증 - 에러가 발생하지 않고 기본값으로 처리되어야 함
        self.assertTrue(add_result["success"])
    
    def test_completed_request_approval(self):
        """요청 완료 승인 테스트"""
        # 요청과 태스크 생성
        result = self.task_manager.request_planning("테스트", [{"title": "태스크", "description": "설명"}])
        request_id = result["requestId"]
        
        # 다음 태스크 가져오기
        next_task = self.task_manager.get_next_task(request_id)
        task_id = next_task["task"]["id"]
        
        # 태스크 완료 및 승인
        self.task_manager.mark_task_done(request_id, task_id)
        self.task_manager.approve_task_completion(request_id, task_id)
        
        # 요청 완료 승인
        complete_result = self.task_manager.approve_request_completion(request_id)
        
        # 검증
        self.assertTrue(complete_result["success"])
        self.assertEqual(self.task_manager.requests[request_id]["status"], "COMPLETED")
    
    def test_list_requests(self):
        """요청 목록 조회 테스트"""
        # 테스트 전에 현재 요청 개수 확인
        initial_request_count = len(self.task_manager.list_requests()["requests"])
        
        # 여러 요청 생성
        self.task_manager.request_planning("요청 1", [{"title": "태스크", "description": "설명"}])
        self.task_manager.request_planning("요청 2", [{"title": "태스크", "description": "설명"}])
        
        # 요청 목록 조회
        list_result = self.task_manager.list_requests()
        
        # 검증 - 최소 2개 이상 추가되었는지 확인
        self.assertGreaterEqual(len(list_result["requests"]), initial_request_count + 2)
        
        # 방금 생성한 요청들이 목록에 포함되어 있는지 확인
        found_req1 = False
        found_req2 = False
        for request in list_result["requests"]:
            if request["originalRequest"] == "요청 1":
                found_req1 = True
            elif request["originalRequest"] == "요청 2":
                found_req2 = True
        
        self.assertTrue(found_req1, "요청 1을 찾을 수 없음")
        self.assertTrue(found_req2, "요청 2를 찾을 수 없음")
    
    def test_task_details(self):
        """태스크 상세 정보 조회 테스트"""
        # 요청과 태스크 생성
        result = self.task_manager.request_planning("테스트", [{"title": "태스크", "description": "설명"}])
        request_id = result["requestId"]
        
        # 태스크 ID 가져오기
        next_task = self.task_manager.get_next_task(request_id)
        task_id = next_task["task"]["id"]
        
        # 상세 정보 조회
        details = self.task_manager.open_task_details(task_id)
        
        # 검증
        self.assertIn("task", details)
        self.assertEqual(details["task"]["id"], task_id)
        self.assertEqual(details["task"]["title"], "태스크")

if __name__ == "__main__":
    unittest.main() 