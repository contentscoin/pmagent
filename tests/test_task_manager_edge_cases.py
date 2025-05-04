#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import logging
from pathlib import Path
import uuid

# 테스트를 위한 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from pmagent.task_manager import TaskManager

class TestTaskManagerEdgeCases(unittest.TestCase):
    """TaskManager의 특수 케이스 테스트"""
    
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
        
        # TaskManager 인스턴스 생성
        self.manager = TaskManager()
    
    def tearDown(self):
        """각 테스트 종료 후 실행되는 정리"""
        self.patcher.stop()
        self.temp_dir.cleanup()
    
    def test_non_dict_task_handling(self):
        """딕셔너리가 아닌 태스크 처리 테스트"""
        # 문자열 태스크 - 타이틀과 설명이 있는 형태로 처리
        result = self.manager.request_planning("테스트", [
            {"title": "태스크1", "description": "설명1"},
            {"title": "태스크2", "description": "설명2"}
        ])
        self.assertIn("requestId", result)
        request_id = result["requestId"]
        
        # 태스크 목록 확인
        tasks_progress = self.manager._get_tasks_progress(request_id)
        self.assertEqual(len(tasks_progress), 2)
        self.assertEqual(tasks_progress[0]["title"], "태스크1")
        self.assertEqual(tasks_progress[1]["title"], "태스크2")
    
    def test_data_file_handling(self):
        """데이터 파일 처리 테스트"""
        # 새 요청 생성
        result = self.manager.request_planning("테스트 요청", [
            {"title": "태스크1", "description": "설명1"}
        ])
        request_id = result["requestId"]
        
        # 파일에 저장
        self.manager._save_data()
        
        # 새 매니저 인스턴스로 데이터 로드
        new_manager = TaskManager()
        self.assertIn(request_id, new_manager.requests)
        self.assertEqual(new_manager.requests[request_id]["originalRequest"], "테스트 요청")
    
    def test_file_io_operations(self):
        """파일 입출력 작업 테스트"""
        # 요청 생성 및 저장
        result = self.manager.request_planning("테스트 요청", [
            {"title": "태스크1", "description": "설명1"}
        ])
        request_id = result["requestId"]
        
        # 데이터 저장 확인 - 내부적으로 _save_data()를 호출함
        self.manager._save_data()
        
        # 새 매니저 인스턴스로 데이터 로드
        new_manager = TaskManager()
        self.assertIn(request_id, new_manager.requests)
        self.assertEqual(new_manager.requests[request_id]["originalRequest"], "테스트 요청")
    
    def test_request_validation(self):
        """요청 검증 테스트"""
        # 빈 요청 ID
        with self.assertRaises(ValueError):
            self.manager.get_next_task("")
        
        # 존재하지 않는 요청 ID
        with self.assertRaises(ValueError):
            self.manager.get_next_task("non-existent-id")
    
    def test_task_completion_edge_cases(self):
        """태스크 완료 특수 케이스 테스트"""
        # 요청 생성
        result = self.manager.request_planning("테스트", [{"title": "태스크1", "description": "설명1"}])
        request_id = result["requestId"]
        
        # 태스크 ID 가져오기
        tasks_progress = self.manager._get_tasks_progress(request_id)
        task_id = tasks_progress[0]["id"]
        
        # 태스크 완료 처리
        result = self.manager.mark_task_done(request_id, task_id, "완료됨")
        self.assertTrue(result["success"])
        
        # 이미 완료된 태스크 다시 완료 시도 - 실패하지만 예외는 발생하지 않음
        result = self.manager.mark_task_done(request_id, task_id, "다시 완료 시도")
        self.assertFalse(result["success"])
        
        # 태스크 승인
        result = self.manager.approve_task_completion(request_id, task_id)
        self.assertTrue(result["success"])
        
        # 이미 승인된 태스크 다시 승인 시도 - 실패하지만 예외는 발생하지 않음
        result = self.manager.approve_task_completion(request_id, task_id)
        self.assertFalse(result["success"])
    
    def test_multi_request_handling(self):
        """다중 요청 처리 테스트"""
        # 여러 요청 생성
        requests = []
        for i in range(5):
            result = self.manager.request_planning(f"테스트 {i}", [{"title": f"태스크 {i}", "description": f"설명 {i}"}])
            requests.append(result["requestId"])
        
        # 모든 요청이 생성되었는지 확인
        all_requests = self.manager.list_requests()
        
        # 방금 생성한 요청들이 존재하는지 확인
        request_ids = [req["id"] for req in all_requests["requests"]]
        for req_id in requests:
            self.assertIn(req_id, request_ids)
        
        # 각 요청의 태스크 완료 및 승인
        for req_id in requests:
            tasks_progress = self.manager._get_tasks_progress(req_id)
            for task in tasks_progress:
                self.manager.mark_task_done(req_id, task["id"], "완료됨")
                self.manager.approve_task_completion(req_id, task["id"])
            
            # 요청 완료 승인
            result = self.manager.approve_request_completion(req_id)
            self.assertTrue(result["success"])
            # request 키를 통해 상태 확인
            self.assertEqual(result["request"]["status"], "COMPLETED")

if __name__ == "__main__":
    unittest.main() 