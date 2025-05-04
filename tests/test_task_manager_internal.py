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
from datetime import datetime
from types import SimpleNamespace

# 테스트를 위한 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from pmagent.task_manager import TaskManager, load_requests, load_tasks

class TestTaskManagerInternal(unittest.TestCase):
    """TaskManager 내부 로직 테스트"""
    
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
    
    def test_task_id_generation(self):
        """태스크 ID 생성 테스트"""
        # 요청 생성
        result = self.manager.request_planning("ID 생성 테스트", [
            {"title": "태스크 1", "description": "설명 1"},
            {"title": "태스크 2", "description": "설명 2"}
        ])
        request_id = result["requestId"]
        
        # 생성된 태스크 ID 확인
        request_data = self.manager.requests[request_id]
        self.assertEqual(len(request_data["tasks"]), 2)
        
        # 각 태스크 ID가 유효한 UUID 형식인지 확인
        for task_id in request_data["tasks"]:
            # UUID 형식 검증
            try:
                uuid.UUID(task_id)
                is_valid_uuid = True
            except ValueError:
                is_valid_uuid = False
            
            self.assertTrue(is_valid_uuid, f"{task_id}가 유효한 UUID가 아님")
            
            # tasks 딕셔너리에 실제로 존재하는지 확인
            self.assertIn(task_id, self.manager.tasks)
    
    def test_datetime_handling(self):
        """날짜/시간 처리 테스트"""
        # 요청 생성
        result = self.manager.request_planning("날짜 테스트", [
            {"title": "태스크", "description": "설명"}
        ])
        request_id = result["requestId"]
        
        # 요청 객체 가져오기
        request_data = self.manager.requests[request_id]
        
        # 날짜 필드가 ISO 형식으로 저장되어 있는지 확인
        created_at = request_data["createdAt"]
        updated_at = request_data["updatedAt"]
        
        # ISO 형식 검증 (간단한 방법)
        self.assertTrue("T" in created_at, "createdAt이 ISO 형식이 아님")
        self.assertTrue("T" in updated_at, "updatedAt이 ISO 형식이 아님")
        
        # datetime으로 파싱 가능한지 확인
        try:
            datetime.fromisoformat(created_at)
            datetime.fromisoformat(updated_at)
            is_valid_datetime = True
        except ValueError:
            is_valid_datetime = False
        
        self.assertTrue(is_valid_datetime, "날짜가 유효한 ISO 형식이 아님")
    
    def test_task_progress_calculation(self):
        """태스크 진행 상황 계산 테스트"""
        # 요청 계획 생성 (3개 태스크)
        result = self.manager.request_planning("진행 상황 테스트", [
            {"title": "태스크 1", "description": "설명 1"},
            {"title": "태스크 2", "description": "설명 2"},
            {"title": "태스크 3", "description": "설명 3"}
        ])
        request_id = result["requestId"]
        
        # 다음 태스크 가져오기
        next_task = self.manager.get_next_task(request_id)
        task_id1 = next_task["task"]["id"]
        
        # 첫 번째 태스크 완료 및 승인
        self.manager.mark_task_done(request_id, task_id1)
        self.manager.approve_task_completion(request_id, task_id1)
        
        # 다음 태스크 가져오기
        next_task = self.manager.get_next_task(request_id)
        task_id2 = next_task["task"]["id"]
        
        # 두 번째 태스크 완료 (승인 안 함)
        self.manager.mark_task_done(request_id, task_id2)
        
        # 태스크 진행 상황 가져오기
        tasks_progress = self.manager._get_tasks_progress(request_id)
        
        # 상태 확인
        total_tasks = len(tasks_progress)
        completed_tasks = sum(1 for task in tasks_progress if task["status"] == "DONE")
        approved_tasks = sum(1 for task in tasks_progress if task["approved"])
        
        self.assertEqual(total_tasks, 3)
        self.assertEqual(completed_tasks, 2)  # 완료된 태스크 2개
        self.assertEqual(approved_tasks, 1)   # 승인된 태스크 1개
    
    def test_non_string_task_fields(self):
        """문자열이 아닌 태스크 필드 처리 테스트"""
        # 숫자 및 불리언 필드가 있는 태스크로 요청 생성
        result = self.manager.request_planning("필드 타입 테스트", [
            {"title": 123, "description": True},
            {"title": {"key": "value"}, "description": ["item1", "item2"]}
        ])
        request_id = result["requestId"]
        
        # 태스크 가져오기
        tasks_progress = self.manager._get_tasks_progress(request_id)
        
        # 모든 필드가 문자열로 변환되었는지 확인
        for task in tasks_progress:
            self.assertIsInstance(task["title"], str)
            self.assertIsInstance(task["description"], str)
    
    def test_empty_tasks_list(self):
        """빈 태스크 목록 처리 테스트"""
        # 빈 태스크 목록으로 요청 생성 시도 (예외 발생 예상)
        with self.assertRaises(ValueError):
            self.manager.request_planning("빈 태스크 테스트", [])
    
    def test_task_status_transitions(self):
        """태스크 상태 전이 테스트"""
        # 요청 생성
        result = self.manager.request_planning("상태 전이 테스트", [
            {"title": "태스크", "description": "설명"}
        ])
        request_id = result["requestId"]
        
        # 다음 태스크 가져오기
        next_task = self.manager.get_next_task(request_id)
        task_id = next_task["task"]["id"]
        
        # 최초 상태 확인
        task = self.manager.tasks[task_id]
        self.assertEqual(task["status"], "PENDING")
        self.assertFalse(task["approved"])
        
        # 태스크 완료
        self.manager.mark_task_done(request_id, task_id)
        task = self.manager.tasks[task_id]
        self.assertEqual(task["status"], "DONE")
        self.assertFalse(task["approved"])
        
        # 태스크 승인
        self.manager.approve_task_completion(request_id, task_id)
        task = self.manager.tasks[task_id]
        self.assertEqual(task["status"], "DONE")
        self.assertTrue(task["approved"])
        
        # 승인된 태스크를 다시 완료 표시 시도 (성공하지 않음)
        result = self.manager.mark_task_done(request_id, task_id, "다시 완료")
        self.assertFalse(result["success"])
        
        # 승인된 태스크를 다시 승인 시도 (성공하지 않음)
        result = self.manager.approve_task_completion(request_id, task_id)
        self.assertFalse(result["success"])
    
    def test_request_status_transitions(self):
        """요청 상태 전이 테스트"""
        # 요청 생성
        result = self.manager.request_planning("요청 상태 테스트", [
            {"title": "태스크", "description": "설명"}
        ])
        request_id = result["requestId"]
        
        # 최초 상태 확인
        request = self.manager.requests[request_id]
        self.assertEqual(request["status"], "PENDING")
        
        # 다음 태스크 가져오기
        next_task = self.manager.get_next_task(request_id)
        task_id = next_task["task"]["id"]
        
        # 태스크 완료 및 승인
        self.manager.mark_task_done(request_id, task_id)
        self.manager.approve_task_completion(request_id, task_id)
        
        # 모든 태스크가 완료되었지만 요청은 아직 완료되지 않음
        request = self.manager.requests[request_id]
        self.assertEqual(request["status"], "PENDING")
        
        # 요청 완료 승인
        result = self.manager.approve_request_completion(request_id)
        self.assertTrue(result["success"])
        
        # 최종 상태 확인
        request = self.manager.requests[request_id]
        self.assertEqual(request["status"], "COMPLETED")
    
    def test_request_with_no_tasks(self):
        """태스크가 없는 요청 상태 테스트"""
        # 요청 생성 (정상적으로 태스크 포함)
        result = self.manager.request_planning("태스크 삭제 테스트", [
            {"title": "삭제될 태스크", "description": "설명"}
        ])
        request_id = result["requestId"]
        
        # 요청 객체 직접 수정하여 태스크 제거 (비정상 상태 시뮬레이션)
        self.manager.requests[request_id]["tasks"] = []
        
        # 다음 태스크 가져오기 시도
        next_task = self.manager.get_next_task(request_id)
        
        # 결과 확인
        self.assertFalse(next_task["hasNextTask"])
        self.assertTrue(next_task["allTasksDone"])
    
    def test_task_with_invalid_request_id(self):
        """유효하지 않은 요청 ID를 가진 태스크 처리 테스트"""
        # 요청 생성
        result = self.manager.request_planning("유효하지 않은 ID 테스트", [
            {"title": "태스크", "description": "설명"}
        ])
        request_id = result["requestId"]
        
        # 다음 태스크 가져오기
        next_task = self.manager.get_next_task(request_id)
        task_id = next_task["task"]["id"]
        
        # 태스크의 요청 ID를 존재하지 않는 값으로 변경 (비정상 상태 시뮬레이션)
        self.manager.tasks[task_id]["requestId"] = "non-existent-id"
        
        # 태스크 완료 시도 (실패 예상)
        with self.assertRaises(ValueError):
            self.manager.mark_task_done("non-existent-id", task_id)
    
    def test_custom_object_task(self):
        """커스텀 객체로 생성된 태스크 처리 테스트"""
        # SimpleNamespace 객체를 사용하여 태스크 생성
        task_obj = SimpleNamespace(title="객체 태스크", description="객체 설명")
        
        # 요청 생성 시도
        try:
            result = self.manager.request_planning("객체 태스크 테스트", [task_obj])
            self.fail("예외가 발생하지 않음")
        except Exception as e:
            # SimpleNamespace는 딕셔너리로 변환될 수 없으므로 예외 발생 예상
            self.assertIn("딕셔너리", str(e).lower())
    
    def test_task_update_validation(self):
        """태스크 업데이트 유효성 검사 테스트"""
        # 요청 생성
        result = self.manager.request_planning("업데이트 테스트", [
            {"title": "원본 제목", "description": "원본 설명"}
        ])
        request_id = result["requestId"]
        
        # 다음 태스크 가져오기
        next_task = self.manager.get_next_task(request_id)
        task_id = next_task["task"]["id"]
        
        # 빈 제목 업데이트 시도
        result = self.manager.update_task(request_id, task_id, title="")
        # 빈 제목도 허용되어야 함
        self.assertTrue(result["success"])
        self.assertEqual(result["task"]["title"], "")
        
        # 매우 긴 설명으로 업데이트
        long_desc = "매우 긴 설명" * 1000  # 대략 10,000자
        result = self.manager.update_task(request_id, task_id, description=long_desc)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["task"]["description"]), len(long_desc))
    
    def test_duplicate_task_ids(self):
        """중복된 태스크 ID 처리 테스트"""
        # 요청 생성
        result = self.manager.request_planning("중복 ID 테스트", [
            {"title": "태스크 1", "description": "설명 1"},
            {"title": "태스크 2", "description": "설명 2"}
        ])
        request_id = result["requestId"]
        
        # 다음 태스크 가져오기
        next_task = self.manager.get_next_task(request_id)
        task_id = next_task["task"]["id"]
        
        # 두 번째 태스크 가져오기 위해 첫 번째 태스크 완료 및 승인
        self.manager.mark_task_done(request_id, task_id)
        self.manager.approve_task_completion(request_id, task_id)
        
        # 두 번째 태스크 가져오기
        next_task = self.manager.get_next_task(request_id)
        task_id2 = next_task["task"]["id"]
        
        # 두 태스크 ID가 다른지 확인
        self.assertNotEqual(task_id, task_id2)
        
        # 요청의 tasks 배열에 동일한 태스크 ID가 중복되지 않았는지 확인
        task_ids = self.manager.requests[request_id]["tasks"]
        self.assertEqual(len(task_ids), len(set(task_ids)))
    
    def test_json_serialization_edge_cases(self):
        """JSON 직렬화 특수 케이스 테스트"""
        # 날짜 객체를 포함한 데이터 생성
        now = datetime.now()
        test_data = {
            "req-1": {
                "id": "req-1",
                "originalRequest": "JSON 테스트",
                "createdAt": now,  # datetime 객체
                "tasks": ["task-1"],
                "status": "PENDING"
            }
        }
        
        # 데이터 직렬화 시도 (예외 발생 예상)
        with self.assertRaises(TypeError):
            json.dumps(test_data)
        
        # TaskManager 인스턴스는 이러한 케이스를 자동으로 처리해야 함
        # 요청 생성
        result = self.manager.request_planning("JSON 테스트", [
            {"title": "태스크", "description": "설명"}
        ])
        request_id = result["requestId"]
        
        # 수동으로 datetime 객체 할당
        self.manager.requests[request_id]["customDate"] = now
        
        # _save_data 호출 시 오류가 발생하지 않아야 함
        try:
            self.manager._save_data()
            serialization_succeeded = True
        except:
            serialization_succeeded = False
        
        self.assertTrue(serialization_succeeded, "직렬화 중 예외 발생")

if __name__ == "__main__":
    unittest.main() 