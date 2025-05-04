#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 환경 변수에서 설정 로드
DATA_DIR = os.environ.get("DATA_DIR", "./data")
# 데이터 디렉토리 생성
Path(DATA_DIR).mkdir(exist_ok=True, parents=True)
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.json")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")

# 로드 및 저장 함수
def load_requests() -> Dict[str, Any]:
    """요청 데이터를 로드합니다."""
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"잘못된 JSON 포맷: {REQUESTS_FILE}")
                return {}
    else:
        # 파일이 없는 경우 빈 딕셔너리 생성 후 저장
        empty_data = {}
        save_requests(empty_data)
        return empty_data

def save_requests(requests: Dict[str, Any]) -> None:
    """요청 데이터를 저장합니다."""
    # data 디렉토리가 존재하는지 확인
    os.makedirs(os.path.dirname(REQUESTS_FILE), exist_ok=True)
    
    with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(requests, f, ensure_ascii=False, indent=2)

def load_tasks() -> Dict[str, Any]:
    """태스크 데이터를 로드합니다."""
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"잘못된 JSON 포맷: {TASKS_FILE}")
                return {}
    else:
        # 파일이 없는 경우 빈 딕셔너리 생성 후 저장
        empty_data = {}
        save_tasks(empty_data)
        return empty_data

def save_tasks(tasks: Dict[str, Any]) -> None:
    """태스크 데이터를 저장합니다."""
    # data 디렉토리가 존재하는지 확인
    os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
    
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

# 태스크 관리 클래스
class TaskManager:
    def __init__(self):
        self.requests = load_requests()
        self.tasks = load_tasks()
    
    def _save_data(self):
        """현재 데이터 상태를 저장합니다."""
        save_requests(self.requests)
        save_tasks(self.tasks)
    
    def request_planning(self, original_request: str, tasks: List[Dict[str, str]], split_details: Optional[str] = None) -> Dict[str, Any]:
        """새 요청을 등록하고, 관련 태스크를 생성합니다."""
        # 입력 유효성 검사
        if not original_request:
            raise ValueError("원본 요청 내용은 필수입니다.")
        
        # 유효한 태스크 목록인지 확인
        if not tasks or not isinstance(tasks, list):
            raise ValueError("유효한 태스크 목록이 필요합니다.")
        
        logger.info(f"TaskManager.request_planning 호출됨: original_request={original_request}, tasks={tasks}")
        logger.info(f"tasks 타입: {type(tasks)}")
        
        # 태스크 검증
        validated_tasks = []
        for i, task in enumerate(tasks):
            # 각 태스크가 딕셔너리인지 확인
            if not isinstance(task, dict):
                logger.warning(f"태스크 #{i}가 딕셔너리가 아님: {type(task)}")
                try:
                    task_dict = dict(task)
                    task = task_dict
                except (TypeError, ValueError):
                    logger.error(f"태스크 #{i}를 딕셔너리로 변환할 수 없음: {task}")
                    continue
            
            # 필수 필드가 있는지 확인
            if "title" not in task or "description" not in task:
                logger.warning(f"태스크 #{i}에 필수 필드가 없음: {task}")
                # 기본값으로 설정
                if "title" not in task:
                    task["title"] = f"태스크 #{i+1}"
                if "description" not in task:
                    task["description"] = ""
            
            validated_tasks.append(task)
        
        # 검증된 태스크로 교체
        tasks = validated_tasks
        if not tasks:
            raise ValueError("유효한 태스크가 없습니다.")
        
        request_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # 새 요청 생성
        request_data = {
            "id": request_id,
            "originalRequest": original_request,
            "splitDetails": split_details,
            "createdAt": now,
            "updatedAt": now,
            "status": "PENDING",
            "tasks": []  # 명시적으로 빈 리스트로 초기화
        }
        
        # 태스크 생성 및 연결
        try:
            for task in tasks:
                logger.info(f"태스크 처리 중: {task}")
                # 각 필드에 접근하기 전에 타입 출력
                logger.info(f"task['title'] 타입: {type(task.get('title'))}")
                logger.info(f"task['description'] 타입: {type(task.get('description'))}")
                
                # 확실히 딕셔너리로 변환하여 처리
                task_dict = task
                if not isinstance(task_dict, dict):
                    try:
                        task_dict = dict(task_dict)
                        logger.warning(f"태스크가 딕셔너리가 아님: {task}, 변환됨: {task_dict}")
                    except (TypeError, ValueError) as e:
                        logger.error(f"태스크를 딕셔너리로 변환할 수 없음: {task}, 오류: {str(e)}")
                        # 기본값으로 설정
                        task_dict = {"title": "제목 없음", "description": "설명 없음"}
                
                task_id = str(uuid.uuid4())
                task_data = {
                    "id": task_id,
                    "requestId": request_id,
                    "title": str(task_dict.get("title", "")),  # 문자열로 변환 
                    "description": str(task_dict.get("description", "")),  # 문자열로 변환
                    "status": "PENDING",
                    "createdAt": now,
                    "updatedAt": now,
                    "completedAt": None,
                    "completedDetails": None,
                    "approved": False,
                    "approvedAt": None
                }
                
                # 태스크 저장
                self.tasks[task_id] = task_data
                
                # 요청에 태스크 ID 추가
                try:
                    request_data["tasks"].append(task_id)
                except Exception as e:
                    logger.error(f"태스크 ID 추가 중 오류 발생: {str(e)}")
                    # tasks가 제대로 된 리스트가 아닌 경우 초기화 후 다시 시도
                    request_data["tasks"] = [task_id]
                    logger.info(f"tasks를 새 리스트로 초기화하여 태스크 ID {task_id} 추가함")
        except Exception as e:
            logger.error(f"태스크 처리 중 오류 발생: {str(e)}")
            logger.error(f"오류 발생 위치: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
            raise ValueError(f"태스크 처리 중 오류 발생: {str(e)}")
        
        # 요청 저장
        self.requests[request_id] = request_data
        self._save_data()
        
        return {"requestId": request_id, "taskCount": len(tasks)}
    
    def get_next_task(self, request_id: str) -> Dict[str, Any]:
        """다음 대기 중인 태스크(아직 완료되지 않은)를 가져옵니다."""
        if request_id not in self.requests:
            raise ValueError(f"존재하지 않는 요청 ID: {request_id}")
        
        request = self.requests[request_id]
        
        # 요청에 tasks 속성이 있고 리스트인지 확인
        if not isinstance(request.get("tasks"), list):
            logger.warning(f"request[{request_id}]['tasks']가 리스트가 아님: {type(request.get('tasks'))}")
            # 빈 리스트로 초기화
            request["tasks"] = []
            self._save_data()
        
        # 모든 태스크가 완료되었는지 확인
        all_tasks_done = True
        next_task = None
        
        # 태스크 상태 정보를 포함한 상세 태스크 목록
        tasks_info = []
        
        for i, task_id in enumerate(request["tasks"]):
            # task_id가 문자열인지 확인
            if not isinstance(task_id, str):
                try:
                    task_id = str(task_id)
                    logger.warning(f"태스크 ID가 문자열이 아니어서 변환함: 원본={request['tasks'][i]}, 변환={task_id}")
                    # 원본 리스트도 업데이트
                    request["tasks"][i] = task_id
                except (TypeError, ValueError):
                    logger.error(f"태스크 ID를 문자열로 변환할 수 없음: {task_id}")
                    continue
            
            task = self.tasks.get(task_id)
            if not task:
                logger.warning(f"태스크 ID {task_id}에 해당하는 태스크가 없음")
                continue
            
            # 태스크 정보 추가
            tasks_info.append({
                "id": task["id"],
                "title": task["title"],
                "status": task["status"],
                "approved": task["approved"]
            })
            
            # 첫 번째 대기 중인 태스크 찾기
            if task["status"] == "PENDING" and not next_task:
                next_task = task
                all_tasks_done = False
            # 완료되었지만 승인되지 않은 태스크가 있는 경우
            elif task["status"] == "DONE" and not task["approved"]:
                all_tasks_done = False
            # 대기 중인 다른 태스크가 있는 경우
            elif task["status"] == "PENDING":
                all_tasks_done = False
        
        # 정보 반환
        if next_task:
            return {
                "hasNextTask": True,
                "allTasksDone": False,
                "task": next_task,
                "tasksProgress": tasks_info
            }
        else:
            return {
                "hasNextTask": False,
                "allTasksDone": all_tasks_done,
                "tasksProgress": tasks_info
            }
    
    def mark_task_done(self, request_id: str, task_id: str, completed_details: Optional[str] = None) -> Dict[str, Any]:
        """태스크를 완료 상태로 표시합니다."""
        if request_id not in self.requests:
            raise ValueError(f"존재하지 않는 요청 ID: {request_id}")
        
        if task_id not in self.tasks:
            raise ValueError(f"존재하지 않는 태스크 ID: {task_id}")
        
        task = self.tasks[task_id]
        
        # 태스크가 이 요청에 속하는지 확인
        if task["requestId"] != request_id:
            raise ValueError(f"태스크 {task_id}는 요청 {request_id}에 속하지 않습니다.")
        
        # 태스크가 이미 완료 상태인지 확인
        if task["status"] == "DONE":
            return {
                "success": False,
                "message": "이미 완료된 태스크입니다.",
                "task": task,
                "tasksProgress": self._get_tasks_progress(request_id)
            }
        
        # 태스크 완료 처리
        now = datetime.now().isoformat()
        task["status"] = "DONE"
        task["completedAt"] = now
        task["updatedAt"] = now
        task["completedDetails"] = completed_details or ""
        
        # 변경사항 저장
        self._save_data()
        
        # 응답 반환
        return {
            "success": True,
            "message": "태스크가 완료 처리되었습니다.",
            "task": task,
            "tasksProgress": self._get_tasks_progress(request_id)
        }
    
    def approve_task_completion(self, request_id: str, task_id: str) -> Dict[str, Any]:
        """완료된 태스크를 승인합니다."""
        if request_id not in self.requests:
            raise ValueError(f"존재하지 않는 요청 ID: {request_id}")
        
        if task_id not in self.tasks:
            raise ValueError(f"존재하지 않는 태스크 ID: {task_id}")
        
        task = self.tasks[task_id]
        
        # 태스크가 이 요청에 속하는지 확인
        if task["requestId"] != request_id:
            raise ValueError(f"태스크 {task_id}는 요청 {request_id}에 속하지 않습니다.")
        
        # 태스크가 완료 상태인지 확인
        if task["status"] != "DONE":
            return {
                "success": False,
                "message": "완료되지 않은 태스크는 승인할 수 없습니다.",
                "task": task,
                "tasksProgress": self._get_tasks_progress(request_id)
            }
        
        # 이미 승인된 태스크인지 확인
        if task["approved"]:
            return {
                "success": False,
                "message": "이미 승인된 태스크입니다.",
                "task": task,
                "tasksProgress": self._get_tasks_progress(request_id)
            }
        
        # 태스크 승인 처리
        now = datetime.now().isoformat()
        task["approved"] = True
        task["approvedAt"] = now
        task["updatedAt"] = now
        
        # 변경사항 저장
        self._save_data()
        
        # 응답 반환
        return {
            "success": True,
            "message": "태스크 완료가 승인되었습니다.",
            "task": task,
            "tasksProgress": self._get_tasks_progress(request_id)
        }
    
    def approve_request_completion(self, request_id: str) -> Dict[str, Any]:
        """요청 전체의 완료를 승인합니다."""
        if request_id not in self.requests:
            raise ValueError(f"존재하지 않는 요청 ID: {request_id}")
        
        request = self.requests[request_id]
        
        # 모든 태스크가 완료되고 승인되었는지 확인
        all_tasks_done_approved = True
        tasks_progress = []
        
        for task_id in request["tasks"]:
            task = self.tasks.get(task_id)
            if not task:
                continue
            
            tasks_progress.append({
                "id": task["id"],
                "title": task["title"],
                "status": task["status"],
                "approved": task["approved"]
            })
            
            if task["status"] != "DONE" or not task["approved"]:
                all_tasks_done_approved = False
        
        # 모든 태스크가 완료 및 승인되지 않은 경우
        if not all_tasks_done_approved:
            return {
                "success": False,
                "message": "모든 태스크가 완료 및 승인되지 않았습니다.",
                "tasksProgress": tasks_progress
            }
        
        # 요청 완료 처리
        now = datetime.now().isoformat()
        request["status"] = "COMPLETED"
        request["updatedAt"] = now
        
        # 변경사항 저장
        self._save_data()
        
        # 응답 반환
        return {
            "success": True,
            "message": "요청이 완전히 완료 처리되었습니다.",
            "request": request,
            "tasksProgress": tasks_progress
        }
    
    def add_tasks_to_request(self, request_id: str, tasks: List[Dict[str, str]]) -> Dict[str, Any]:
        """기존 요청에 새 태스크를 추가합니다."""
        if request_id not in self.requests:
            raise ValueError(f"존재하지 않는 요청 ID: {request_id}")
        
        request = self.requests[request_id]
        now = datetime.now().isoformat()
        
        # request["tasks"]가 리스트인지 확인
        if not isinstance(request.get("tasks"), list):
            logger.warning(f"request['tasks']가 리스트가 아님: {type(request.get('tasks'))}, 빈 리스트로 초기화")
            request["tasks"] = []
        
        # 새 태스크 추가
        added_tasks = []
        for task in tasks:
            # 확실히 딕셔너리로 변환하여 처리
            task_dict = task
            if not isinstance(task_dict, dict):
                try:
                    task_dict = dict(task_dict)
                    logger.warning(f"태스크가 딕셔너리가 아님: {task}, 변환됨: {task_dict}")
                except (TypeError, ValueError) as e:
                    logger.error(f"태스크를 딕셔너리로 변환할 수 없음: {task}, 오류: {str(e)}")
                    # 기본값으로 설정
                    task_dict = {"title": "제목 없음", "description": "설명 없음"}
                
            task_id = str(uuid.uuid4())
            task_data = {
                "id": task_id,
                "requestId": request_id,
                "title": str(task_dict.get("title", "")),
                "description": str(task_dict.get("description", "")),
                "status": "PENDING",
                "createdAt": now,
                "updatedAt": now,
                "completedAt": None,
                "completedDetails": None,
                "approved": False,
                "approvedAt": None
            }
            
            # 태스크 저장
            self.tasks[task_id] = task_data
            
            # 요청에 태스크 ID 추가
            try:
                request["tasks"].append(task_id)
                added_tasks.append(task_data)
            except Exception as e:
                logger.error(f"태스크 ID 추가 중 오류 발생: {str(e)}")
                # tasks가 제대로 된 리스트가 아닌 경우 초기화 후 다시 시도
                request["tasks"] = [task_id]
                added_tasks.append(task_data)
                logger.info(f"tasks를 새 리스트로 초기화하여 태스크 ID {task_id} 추가함")
        
        # 요청 업데이트
        request["updatedAt"] = now
        if request["status"] == "COMPLETED":
            request["status"] = "IN_PROGRESS"
        
        # 변경사항 저장
        self._save_data()
        
        # 응답 반환
        return {
            "success": True,
            "message": f"{len(added_tasks)}개의 태스크가 추가되었습니다.",
            "addedTasks": added_tasks,
            "tasksProgress": self._get_tasks_progress(request_id)
        }
    
    def update_task(self, request_id: str, task_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """태스크 정보를 업데이트합니다."""
        if request_id not in self.requests:
            raise ValueError(f"존재하지 않는 요청 ID: {request_id}")
        
        if task_id not in self.tasks:
            raise ValueError(f"존재하지 않는 태스크 ID: {task_id}")
        
        task = self.tasks[task_id]
        
        # 태스크가 이 요청에 속하는지 확인
        if task["requestId"] != request_id:
            raise ValueError(f"태스크 {task_id}는 요청 {request_id}에 속하지 않습니다.")
        
        # 태스크가 이미 완료 상태인지 확인
        if task["status"] == "DONE":
            return {
                "success": False,
                "message": "완료된 태스크는 업데이트할 수 없습니다.",
                "task": task,
                "tasksProgress": self._get_tasks_progress(request_id)
            }
        
        # 필드 업데이트
        updated = False
        if title is not None and title != task["title"]:
            task["title"] = title
            updated = True
        
        if description is not None and description != task["description"]:
            task["description"] = description
            updated = True
        
        # 업데이트된 경우에만 저장
        if updated:
            now = datetime.now().isoformat()
            task["updatedAt"] = now
            self._save_data()
        
        # 응답 반환
        return {
            "success": updated,
            "message": "태스크가 업데이트되었습니다." if updated else "업데이트할 내용이 없습니다.",
            "task": task,
            "tasksProgress": self._get_tasks_progress(request_id)
        }
    
    def delete_task(self, request_id: str, task_id: str) -> Dict[str, Any]:
        """태스크를 삭제합니다."""
        if request_id not in self.requests:
            raise ValueError(f"존재하지 않는 요청 ID: {request_id}")
        
        if task_id not in self.tasks:
            raise ValueError(f"존재하지 않는 태스크 ID: {task_id}")
        
        task = self.tasks[task_id]
        
        # 태스크가 이 요청에 속하는지 확인
        if task["requestId"] != request_id:
            raise ValueError(f"태스크 {task_id}는 요청 {request_id}에 속하지 않습니다.")
        
        # 태스크가 이미 완료 상태인지 확인
        if task["status"] == "DONE" and task["approved"]:
            return {
                "success": False,
                "message": "완료 및 승인된 태스크는 삭제할 수 없습니다.",
                "tasksProgress": self._get_tasks_progress(request_id)
            }
        
        # 요청에서 태스크 ID 제거
        request = self.requests[request_id]
        if task_id in request["tasks"]:
            request["tasks"].remove(task_id)
        
        # 태스크 삭제
        del self.tasks[task_id]
        
        # 변경사항 저장
        now = datetime.now().isoformat()
        request["updatedAt"] = now
        self._save_data()
        
        # 응답 반환
        return {
            "success": True,
            "message": "태스크가 삭제되었습니다.",
            "tasksProgress": self._get_tasks_progress(request_id)
        }
    
    def list_requests(self) -> Dict[str, Any]:
        """모든 요청 목록을 가져옵니다."""
        requests_list = []
        
        for request_id, request in self.requests.items():
            # 태스크 진행 상황 계산
            total_tasks = len(request["tasks"])
            done_tasks = sum(1 for task_id in request["tasks"] if self.tasks.get(task_id, {}).get("status") == "DONE")
            approved_tasks = sum(1 for task_id in request["tasks"] if self.tasks.get(task_id, {}).get("approved", False))
            
            # 요약 정보 생성
            request_summary = {
                "id": request_id,
                "originalRequest": request["originalRequest"],
                "status": request["status"],
                "createdAt": request["createdAt"],
                "updatedAt": request["updatedAt"],
                "totalTasks": total_tasks,
                "doneTasks": done_tasks,
                "approvedTasks": approved_tasks
            }
            
            requests_list.append(request_summary)
        
        return {"requests": requests_list}
    
    def open_task_details(self, task_id: str) -> Dict[str, Any]:
        """태스크 상세 정보를 가져옵니다."""
        if task_id not in self.tasks:
            raise ValueError(f"존재하지 않는 태스크 ID: {task_id}")
        
        return {"task": self.tasks[task_id]}
    
    def _get_tasks_progress(self, request_id: str) -> List[Dict[str, Any]]:
        """요청에 속한 태스크들의 진행 상황을 가져옵니다."""
        if request_id not in self.requests:
            return []
        
        request = self.requests[request_id]
        tasks_progress = []
        
        # tasks가 리스트인지 확인
        if not isinstance(request.get("tasks"), list):
            logger.warning(f"request['tasks']가 리스트가 아님: {type(request.get('tasks'))}, 빈 리스트로 처리")
            return []
        
        for i, task_id in enumerate(request["tasks"]):
            # 디버깅 정보 추가
            logger.debug(f"태스크 ID 처리 중: {task_id}, 타입: {type(task_id)}")
            
            # task_id가 문자열인지 확인
            if not isinstance(task_id, str):
                try:
                    task_id = str(task_id)
                    logger.warning(f"태스크 ID가 문자열이 아니어서 변환함: 원본={request['tasks'][i]}, 변환={task_id}")
                except (TypeError, ValueError):
                    logger.error(f"태스크 ID를 문자열로 변환할 수 없음: {task_id}")
                    continue
            
            # 태스크가 존재하는지 확인
            task = self.tasks.get(task_id)
            if not task:
                logger.warning(f"태스크 ID {task_id}에 해당하는 태스크가 없음")
                continue
            
            # 태스크 상태 정보 추가
            tasks_progress.append({
                "id": task["id"],
                "title": task["title"],
                "description": task["description"],
                "status": task["status"],
                "approved": task["approved"]
            })
        
        return tasks_progress

# 전역 태스크 관리자 인스턴스
task_manager = TaskManager() 