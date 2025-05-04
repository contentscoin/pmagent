#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import sys
import unittest
import tempfile
import logging
from pathlib import Path
import shutil
import uuid
import importlib
import time

# 테스트를 위한 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDataPersistence(unittest.TestCase):
    """데이터 저장 및 로드 기능 테스트"""
    
    def _unload_modules(self):
        """모듈을 sys.modules에서 제거하여 환경 변수 변경이 반영되게 합니다."""
        for name in list(sys.modules.keys()):
            if name.startswith('pmagent.task_manager'):
                del sys.modules[name]
    
    def test_save_and_load_requests(self):
        """요청 저장 및 로드 테스트"""
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 환경 변수 설정
            original_data_dir = os.environ.get('DATA_DIR')
            os.environ['DATA_DIR'] = temp_dir
            
            try:
                # 모듈을 언로드하고 다시 임포트
                self._unload_modules()
                from pmagent.task_manager import load_requests, save_requests
                
                # 테스트 데이터
                test_data = {
                    "req-1": {
                        "id": "req-1",
                        "originalRequest": "테스트 요청",
                        "tasks": ["task-1", "task-2"],
                        "status": "PENDING"
                    }
                }
                
                # 데이터 저장
                save_requests(test_data)
                
                # 데이터 로드
                loaded_data = load_requests()
                
                # 검증
                self.assertEqual(loaded_data, test_data)
                
            finally:
                # 환경 변수 복원
                if original_data_dir is not None:
                    os.environ['DATA_DIR'] = original_data_dir
                else:
                    del os.environ['DATA_DIR']
    
    def test_save_and_load_tasks(self):
        """태스크 저장 및 로드 테스트"""
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 환경 변수 설정
            original_data_dir = os.environ.get('DATA_DIR')
            os.environ['DATA_DIR'] = temp_dir
            
            try:
                # 모듈을 언로드하고 다시 임포트
                self._unload_modules()
                from pmagent.task_manager import load_tasks, save_tasks
                
                # 테스트 데이터
                test_data = {
                    "task-1": {
                        "id": "task-1",
                        "requestId": "req-1",
                        "title": "테스트 태스크",
                        "description": "태스크 설명",
                        "status": "PENDING"
                    }
                }
                
                # 데이터 저장
                save_tasks(test_data)
                
                # 데이터 로드
                loaded_data = load_tasks()
                
                # 검증
                self.assertEqual(loaded_data, test_data)
                
            finally:
                # 환경 변수 복원
                if original_data_dir is not None:
                    os.environ['DATA_DIR'] = original_data_dir
                else:
                    del os.environ['DATA_DIR']
    
    def test_corrupt_json_file_handling(self):
        """손상된 JSON 파일 처리 테스트"""
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 환경 변수 설정
            original_data_dir = os.environ.get('DATA_DIR')
            os.environ['DATA_DIR'] = temp_dir
            
            try:
                # 디렉토리 생성
                os.makedirs(temp_dir, exist_ok=True)
                
                # 손상된 파일 경로
                requests_file = os.path.join(temp_dir, "requests.json")
                
                # 손상된 파일 생성
                with open(requests_file, "w") as f:
                    f.write("{invalid json")
                
                # 모듈을 언로드하고 다시 임포트
                self._unload_modules()
                from pmagent.task_manager import load_requests
                
                # 데이터 로드 시도
                loaded_data = load_requests()
                
                # 빈 딕셔너리가 반환되어야 함
                self.assertEqual(loaded_data, {})
                
                # 파일이 자동으로 재생성되었는지 확인
                # 단순하게 파일 존재 여부와 올바른 JSON 파일이 됐는지만 확인
                self.assertTrue(os.path.exists(requests_file))
                
                # 다시 로드해서 빈 딕셔너리가 반환되는지 확인
                try:
                    reloaded_data = load_requests()
                    self.assertEqual(reloaded_data, {})
                except Exception as e:
                    self.fail(f"재생성된 파일을 로드하는 중 예외 발생: {str(e)}")
                
            finally:
                # 환경 변수 복원
                if original_data_dir is not None:
                    os.environ['DATA_DIR'] = original_data_dir
                else:
                    del os.environ['DATA_DIR']
    
    def test_missing_file_handling(self):
        """파일 누락 처리 테스트"""
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 환경 변수 설정
            original_data_dir = os.environ.get('DATA_DIR')
            os.environ['DATA_DIR'] = temp_dir
            
            try:
                # 디렉토리만 생성 (파일은 생성하지 않음)
                os.makedirs(temp_dir, exist_ok=True)
                
                # 파일 경로
                tasks_file = os.path.join(temp_dir, "tasks.json")
                
                # 파일이 없는지 확인
                self.assertFalse(os.path.exists(tasks_file))
                
                # 모듈을 언로드하고 다시 임포트
                self._unload_modules()
                from pmagent.task_manager import load_tasks
                
                # 데이터 로드 시도
                loaded_data = load_tasks()
                
                # 빈 딕셔너리가 반환되어야 함
                self.assertEqual(loaded_data, {})
                
                # 파일이 자동으로 생성되었는지 확인
                self.assertTrue(os.path.exists(tasks_file))
                
            finally:
                # 환경 변수 복원
                if original_data_dir is not None:
                    os.environ['DATA_DIR'] = original_data_dir
                else:
                    del os.environ['DATA_DIR']
    
    def test_data_directory_creation(self):
        """데이터 디렉토리 생성 테스트"""
        # 임시 디렉토리 생성 (부모 디렉토리)
        with tempfile.TemporaryDirectory() as parent_dir:
            # 환경 변수 설정 - 존재하지 않는 하위 디렉토리 지정
            test_data_dir = os.path.join(parent_dir, "new_data_dir")
            original_data_dir = os.environ.get('DATA_DIR')
            os.environ['DATA_DIR'] = test_data_dir
            
            try:
                # 디렉토리가 없는지 확인
                self.assertFalse(os.path.exists(test_data_dir))
                
                # 모듈을 언로드하고 다시 임포트
                self._unload_modules()
                from pmagent.task_manager import load_requests
                
                # 데이터 로드 시도
                loaded_data = load_requests()
                
                # 빈 딕셔너리가 반환되어야 함
                self.assertEqual(loaded_data, {})
                
                # 디렉토리가 자동으로 생성되었는지 확인
                self.assertTrue(os.path.exists(test_data_dir))
                
                # 파일도 생성되었는지 확인
                self.assertTrue(os.path.exists(os.path.join(test_data_dir, "requests.json")))
                
            finally:
                # 환경 변수 복원
                if original_data_dir is not None:
                    os.environ['DATA_DIR'] = original_data_dir
                else:
                    del os.environ['DATA_DIR']
    
    def test_save_after_modification(self):
        """데이터 수정 후 저장 테스트"""
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 환경 변수 설정
            original_data_dir = os.environ.get('DATA_DIR')
            os.environ['DATA_DIR'] = temp_dir
            
            try:
                # 모듈을 언로드하고 다시 임포트
                self._unload_modules()
                from pmagent.task_manager import TaskManager
                
                # TaskManager 인스턴스 생성
                manager = TaskManager()
                
                # 요청 계획 생성
                result = manager.request_planning(
                    "수정 테스트",
                    [{"title": "태스크", "description": "설명"}]
                )
                request_id = result["requestId"]
                
                # 다음 태스크 가져오기
                next_task = manager.get_next_task(request_id)
                task_id = next_task["task"]["id"]
                
                # 태스크 완료 표시
                manager.mark_task_done(request_id, task_id, "완료됨")
                
                # 새 TaskManager 인스턴스로 확인
                new_manager = TaskManager()
                
                # 요청이 로드되었는지 확인
                self.assertIn(request_id, new_manager.requests)
                
                # 태스크가 로드되고 상태가 변경되었는지 확인
                task_found = False
                for tid, task in new_manager.tasks.items():
                    if task["requestId"] == request_id:
                        task_found = True
                        self.assertEqual(task["status"], "DONE")
                        break
                
                self.assertTrue(task_found, "태스크를 찾을 수 없음")
                
            finally:
                # 환경 변수 복원
                if original_data_dir is not None:
                    os.environ['DATA_DIR'] = original_data_dir
                else:
                    del os.environ['DATA_DIR']
    
    def test_concurrent_file_access(self):
        """병렬 파일 액세스 시뮬레이션 테스트"""
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 환경 변수 설정
            original_data_dir = os.environ.get('DATA_DIR')
            os.environ['DATA_DIR'] = temp_dir
            
            try:
                # 모듈을 언로드하고 다시 임포트
                self._unload_modules()
                from pmagent.task_manager import TaskManager, save_requests, save_tasks
                
                # 공유 테스트 데이터 생성 - 두 매니저가 공유할 데이터
                shared_request_id = "shared-req-1"
                shared_requests = {
                    shared_request_id: {
                        "id": shared_request_id,
                        "originalRequest": "공유 테스트 요청",
                        "tasks": [],
                        "status": "PENDING",
                        "createdAt": "2023-01-01T00:00:00",
                        "updatedAt": "2023-01-01T00:00:00",
                        "splitDetails": None
                    }
                }
                
                # 미리 공유 데이터 저장
                save_requests(shared_requests)
                
                # 두 개의 TaskManager 인스턴스 생성 (둘 다 공유 데이터를 볼 수 있어야 함)
                manager1 = TaskManager()
                manager2 = TaskManager()
                
                # 공유 데이터가 두 매니저 모두에게 보이는지 확인
                self.assertIn(shared_request_id, manager1.requests)
                self.assertIn(shared_request_id, manager2.requests)
                
                # 첫 번째 매니저로 요청 추가 생성
                result1 = manager1.request_planning(
                    "매니저1 요청",
                    [{"title": "태스크1", "description": "설명1"}]
                )
                request_id1 = result1["requestId"]
                
                # 두 번째 매니저로 데이터 다시 로드 (manager1의 변경사항을 볼 수 있어야 함)
                # TaskManager를 새로 생성하여 파일에서 최신 데이터를 읽도록 함
                self._unload_modules()
                from pmagent.task_manager import TaskManager
                new_manager2 = TaskManager()
                
                # 첫 번째 매니저가 추가한 요청이 두 번째 매니저에게 보이는지 확인
                self.assertIn(request_id1, new_manager2.requests)
                
            finally:
                # 환경 변수 복원
                if original_data_dir is not None:
                    os.environ['DATA_DIR'] = original_data_dir
                else:
                    del os.environ['DATA_DIR']
    
    def test_large_data_handling(self):
        """대용량 데이터 처리 테스트"""
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 환경 변수 설정
            original_data_dir = os.environ.get('DATA_DIR')
            os.environ['DATA_DIR'] = temp_dir
            
            try:
                # 모듈을 언로드하고 다시 임포트
                self._unload_modules()
                from pmagent.task_manager import load_requests, save_requests
                
                # 대용량 테스트 데이터 생성
                large_data = {}
                for i in range(50):  # 테스트 시간 단축을 위해 50개만 사용
                    request_id = f"req-{i}"
                    large_data[request_id] = {
                        "id": request_id,
                        "originalRequest": f"대용량 테스트 요청 {i}",
                        "tasks": [f"task-{i}-{j}" for j in range(2)],  # 각 요청당 2개 태스크
                        "status": "PENDING"
                    }
                
                # 데이터 저장
                save_requests(large_data)
                
                # 데이터 로드
                loaded_data = load_requests()
                
                # 검증
                self.assertEqual(len(loaded_data), 50)
                self.assertIn("req-0", loaded_data)
                self.assertIn("req-49", loaded_data)
                
            finally:
                # 환경 변수 복원
                if original_data_dir is not None:
                    os.environ['DATA_DIR'] = original_data_dir
                else:
                    del os.environ['DATA_DIR']
    
    def test_unicode_data_handling(self):
        """유니코드 데이터 처리 테스트"""
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 환경 변수 설정
            original_data_dir = os.environ.get('DATA_DIR')
            os.environ['DATA_DIR'] = temp_dir
            
            try:
                # 모듈을 언로드하고 다시 임포트
                self._unload_modules()
                from pmagent.task_manager import load_requests, save_requests
                
                # 유니코드 문자가 포함된 테스트 데이터
                unicode_data = {
                    "req-1": {
                        "id": "req-1",
                        "originalRequest": "유니코드 테스트 요청 🚀 한글 テスト",
                        "tasks": ["task-1"],
                        "status": "PENDING"
                    }
                }
                
                # 데이터 저장
                save_requests(unicode_data)
                
                # 데이터 로드
                loaded_data = load_requests()
                
                # 검증
                self.assertEqual(loaded_data["req-1"]["originalRequest"], "유니코드 테스트 요청 🚀 한글 テスト")
                
            finally:
                # 환경 변수 복원
                if original_data_dir is not None:
                    os.environ['DATA_DIR'] = original_data_dir
                else:
                    del os.environ['DATA_DIR']

if __name__ == "__main__":
    unittest.main() 