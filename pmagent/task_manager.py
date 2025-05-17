#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
# from pmagent.task_manager import task_manager as global_task_manager

logger = logging.getLogger(__name__)

# 환경 변수에서 설정 로드
DATA_DIR = os.environ.get("DATA_DIR", "./data")
# 데이터 디렉토리 생성
Path(DATA_DIR).mkdir(exist_ok=True, parents=True)
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.json")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")

# 태스크 상태 정의 (상수로 관리하면 더 명확)
TASK_STATUS_PENDING = "PENDING"
TASK_STATUS_ASSIGNED = "ASSIGNED" # 새로운 상태
TASK_STATUS_DONE = "DONE"
TASK_STATUS_APPROVED = "APPROVED"

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
        # 데이터 파일 존재 확인 및 초기화
        if not os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            logger.info(f"새 요청 데이터 파일 생성됨: {REQUESTS_FILE}")
            
        if not os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            logger.info(f"새 태스크 데이터 파일 생성됨: {TASKS_FILE}")
        
        self.requests = load_requests()
        self.tasks = load_tasks()
        
        logger.info(f"TaskManager 초기화: {len(self.requests)} 요청, {len(self.tasks)} 태스크 로드됨")
    
    def _save_data(self):
        """현재 데이터 상태를 저장합니다."""
        try:
            save_requests(self.requests)
            save_tasks(self.tasks)
            logger.debug("데이터 저장 완료")
        except Exception as e:
            logger.error(f"데이터 저장 중 오류 발생: {str(e)}")
    
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
                    "title": str(task_dict.get("title", "")),
                    "description": str(task_dict.get("description", "")),
                    "agent_type_hint": task_dict.get("agent_type_hint"),
                    "status": TASK_STATUS_PENDING,
                    "assignedAgentId": None,
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
    
    def get_next_task(self, request_id: str, agent_id: str) -> Dict[str, Any]:
        """특정 에이전트를 위해 다음 실행 가능한 작업을 찾아 할당합니다."""
        if not agent_id:
            raise ValueError("agent_id is required to assign a task.")
            
        if request_id not in self.requests:
            raise ValueError(f"존재하지 않는 요청 ID: {request_id}")
        
        request = self.requests[request_id]
        
        if not isinstance(request.get("tasks"), list):
            logger.warning(f"request[{request_id}]['tasks']가 리스트가 아님: {type(request.get('tasks'))}")
            request["tasks"] = []
            # self._save_data() # 변경 시점에 저장
        
        # 에이전트 유형 추론 (agentId prefix 기반)
        requesting_agent_type: Optional[str] = None
        if agent_id.startswith("pm-agent-"):
            requesting_agent_type = "pm"
        elif agent_id.startswith("backend-agent-"):
            requesting_agent_type = "backend"
        elif agent_id.startswith("frontend-agent-"):
            requesting_agent_type = "frontend"
        # 다른 에이전트 유형 prefix 추가 가능
        logger.debug(f"Requesting agent: {agent_id}, inferred type: {requesting_agent_type}")

        assignable_task = None
        pending_tasks_for_agent_type = []
        pending_general_tasks = []
        first_pending_task_overall = None # 호환성 또는 fallback 용

        all_tasks_done_or_assigned_to_others = True # 현재 요청 에이전트 기준
        tasks_info = self._get_tasks_progress(request_id) # 진행 상황은 여기서 미리 가져옴

        for task_summary in tasks_info: # tasks_info는 이미 self.tasks.get()을 수행한 결과임
            task_id_from_summary = task_summary["id"]
            task = self.tasks.get(task_id_from_summary) # 상세 정보 다시 가져오기
            if not task: continue # 혹시 모를 불일치

            if task["status"] == TASK_STATUS_PENDING and task.get("assignedAgentId") is None:
                all_tasks_done_or_assigned_to_others = False # 할당 가능한 PENDING 작업이 하나라도 있음
                task_agent_hint = task.get("agent_type_hint")

                if not first_pending_task_overall:
                    first_pending_task_overall = task

                # 우선순위 1: 요청 에이전트 타입과 태스크 힌트가 정확히 일치
                if requesting_agent_type and task_agent_hint == requesting_agent_type:
                    assignable_task = task
                    break # 가장 높은 우선순위이므로 바로 선택
                
                # 우선순위 2를 위해 목록에 추가 (요청 에이전트 타입이 있고, 태스크 힌트는 없음)
                if requesting_agent_type and task_agent_hint is None:
                    pending_general_tasks.append(task)
                
                # 우선순위 3을 위해 목록에 추가 (요청 에이전트가 PM이고, 태스크 힌트가 pm 또는 없음)
                if requesting_agent_type == "pm" and (task_agent_hint == "pm" or task_agent_hint is None):
                    # PM은 자신의 힌트 또는 일반 작업을 가져갈 수 있음 (이미 우선순위 1에서 걸러졌을 수 있음)
                    if task not in pending_general_tasks: # 중복 방지
                         pending_general_tasks.append(task) 
            
            elif task.get("assignedAgentId") != agent_id and task["status"] != TASK_STATUS_DONE and task["status"] != TASK_STATUS_APPROVED : # 다른 에이전트에게 할당되었거나, 내가 처리할 수 없는 상태
                pass # all_tasks_done_or_assigned_to_others는 True로 유지될 수 있음
            else: # 내가 이미 할당받았거나, 완료/승인된 작업 등
                all_tasks_done_or_assigned_to_others = False # 내가 관여된 작업이 있으므로 False
        
        if not assignable_task: # 우선순위 1에서 못 찾음
            if pending_general_tasks: # 우선순위 2 또는 3에 해당되는 태스크가 있다면 그 중 첫번째 선택
                 # PM의 경우, 힌트 없는 일반 작업보다 PM 힌트가 있는 작업을 먼저 고려할 수 있도록 정렬 (선택적)
                if requesting_agent_type == "pm":
                    pending_general_tasks.sort(key=lambda t: (t.get("agent_type_hint") != "pm")) # None이 뒤로 가도록
                assignable_task = pending_general_tasks[0]
            elif requesting_agent_type is None and first_pending_task_overall: # 우선순위 4: 타입 추론 안되고, 전체 PENDING 작업 중 첫번째
                 assignable_task = first_pending_task_overall

        if assignable_task:
            assignable_task["status"] = TASK_STATUS_ASSIGNED
            assignable_task["assignedAgentId"] = agent_id
            assignable_task["updatedAt"] = datetime.now().isoformat()
            self._save_data()
            logger.info(f"Task {assignable_task['id']} ({assignable_task['title']}) assigned to agent {agent_id} (type: {requesting_agent_type})")
            return {
                "success": True,
                "hasNextTask": True,
                "task": assignable_task,
                "message": f"Task {assignable_task['id']} assigned to agent {agent_id}.",
                "progressTableData": self._get_tasks_progress(request_id)
            }
        else:
            # 할당할 작업이 없는 경우, 모든 작업이 완료/승인되었는지 또는 다른 에이전트에게 할당되었는지 확인
            # all_tasks_done_or_assigned_to_others는 현재 agent_id 기준으로 판단해야함.
            # 더 정확하게는, PENDING 이면서 assignedAgentId가 None인 작업이 아예 없는지 봐야함.
            no_pending_unassigned_tasks = True
            for task_summary in tasks_info:
                task_lookup = self.tasks.get(task_summary["id"])
                if task_lookup and task_lookup["status"] == TASK_STATUS_PENDING and task_lookup.get("assignedAgentId") is None:
                    no_pending_unassigned_tasks = False
                    break
            
            logger.info(f"No assignable task found for agent {agent_id} (type: {requesting_agent_type}) for request {request_id}. All tasks done or assigned to others: {no_pending_unassigned_tasks}")
            return {
                "success": True,
                "hasNextTask": False,
                "allTasksDone": no_pending_unassigned_tasks, 
                "message": "No assignable task found for this agent for this request.",
                "tasksProgress": tasks_info, # 현재 상태의 진행상황
                "progressTableData": self._get_tasks_progress(request_id)
            }
    
    def mark_task_done(self, request_id: str, task_id: str, agent_id: str, completed_details: Optional[str] = None) -> Dict[str, Any]:
        """특정 에이전트가 작업을 완료했음을 표시하고, 완료 세부 정보를 기록합니다."""
        logger.info(f"mark_task_done 호출됨: requestId={request_id}, taskId={task_id}, agentId={agent_id}")

        if not agent_id:
            logger.error("agent_id가 제공되지 않았습니다.")
            raise ValueError("agent_id는 작업을 완료하기 위해 필수입니다.")

        if request_id not in self.requests:
            logger.error(f"존재하지 않는 요청 ID: {request_id}")
            raise ValueError(f"존재하지 않는 요청 ID: {request_id}")

        if task_id not in self.tasks:
            logger.error(f"존재하지 않는 태스크 ID: {task_id}")
            raise ValueError(f"존재하지 않는 태스크 ID: {task_id}")

        task_data = self.tasks[task_id]

        # 작업이 해당 요청에 속하는지 확인
        if task_data.get("requestId") != request_id:
            logger.error(f"태스크 {task_id}가 요청 {request_id}에 속하지 않습니다.")
            raise ValueError(f"태스크 {task_id}가 요청 {request_id}에 속하지 않습니다.")

        # 이미 완료되었거나 승인된 작업인지 확인
        if task_data["status"] == TASK_STATUS_DONE:
            logger.warning(f"태스크 {task_id}는 이미 완료되었습니다.")
            return {"message": f"태스크 {task_id}는 이미 완료되었습니다.", "status": task_data["status"]}
        if task_data["status"] == TASK_STATUS_APPROVED:
            logger.warning(f"태스크 {task_id}는 이미 승인되었습니다.")
            return {"message": f"태스크 {task_id}는 이미 승인되었으며, 더 이상 변경할 수 없습니다.", "status": task_data["status"]}


        # 작업이 'ASSIGNED' 상태인지 확인
        if task_data["status"] != TASK_STATUS_ASSIGNED:
            logger.error(f"태스크 {task_id}는 현재 {task_data['status']} 상태이므로 완료할 수 없습니다. 먼저 할당되어야 합니다.")
            raise ValueError(f"태스크 {task_id}는 현재 {task_data['status']} 상태이므로 완료할 수 없습니다. 먼저 할당되어야 합니다.")
        
        # 할당된 에이전트와 현재 에이전트가 일치하는지 확인
        if task_data["assignedAgentId"] != agent_id:
            logger.error(f"태스크 {task_id}는 에이전트 {task_data['assignedAgentId']}에게 할당되었지만, 에이전트 {agent_id}가 완료하려고 시도했습니다.")
            raise ValueError(f"태스크 {task_id}는 다른 에이전트에게 할당되었습니다.")

        task_data["status"] = TASK_STATUS_DONE
        task_data["completedAt"] = datetime.now().isoformat()
        task_data["completedDetails"] = completed_details
        task_data["updatedAt"] = task_data["completedAt"]
        
        self.tasks[task_id] = task_data # 변경된 태스크 정보 업데이트
        self._save_data()
        
        logger.info(f"태스크 {task_id} 완료됨: {completed_details}")
        
        # 요청의 모든 태스크가 완료되었는지 확인하고, 그렇다면 요청 상태 변경
        all_tasks_done_or_approved = True
        request_tasks = self.requests[request_id].get("tasks", [])
        if not request_tasks: # 태스크가 없는 요청은 바로 완료 처리될 수 없음
            all_tasks_done_or_approved = False

        for tid in request_tasks:
            if tid in self.tasks and self.tasks[tid]["status"] not in [TASK_STATUS_DONE, TASK_STATUS_APPROVED]:
                all_tasks_done_or_approved = False
                break
        
        if all_tasks_done_or_approved and request_tasks: # 태스크가 있는 경우에만
            self.requests[request_id]["status"] = "COMPLETED" # 요청의 모든 태스크가 완료되면 요청 상태 변경
            self.requests[request_id]["updatedAt"] = datetime.now().isoformat()
            logger.info(f"요청 {request_id}의 모든 태스크가 완료되어 요청 상태가 COMPLETED로 변경됨")
            self._save_data()

        return {"message": f"태스크 {task_id}가 완료되었습니다.", "status": task_data["status"]}
    
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
                "agent_type_hint": task_dict.get("agent_type_hint"),
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
            total_tasks = 0
            done_tasks = 0
            approved_tasks = 0
            assigned_tasks = 0 # 할당된 태스크 수
            
            if isinstance(request.get("tasks"), list): # tasks 필드가 리스트인지 확인
                total_tasks = len(request["tasks"])
                for task_id in request["tasks"]:
                    task = self.tasks.get(task_id)
                    if task: # 태스크가 실제로 존재하는지 확인
                        if task.get("status") == TASK_STATUS_DONE:
                            done_tasks += 1
                        if task.get("approved", False):
                            approved_tasks += 1
                        if task.get("status") == TASK_STATUS_ASSIGNED:
                            assigned_tasks += 1
            else:
                logger.warning(f"Request {request_id} has no 'tasks' list or it's not a list.")


            # 요약 정보 생성
            request_summary = {
                "id": request_id,
                "originalRequest": request["originalRequest"],
                "status": request["status"],
                "createdAt": request["createdAt"],
                "updatedAt": request["updatedAt"],
                "totalTasks": total_tasks,
                "assignedTasks": assigned_tasks, # 추가된 필드
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
                "assignedAgentId": task.get("assignedAgentId"),
                "approved": task["approved"]
            })
        
        return tasks_progress

    def _internal_clear_all_data(self) -> Dict[str, Any]:
        """
        모든 요청 및 태스크 데이터를 초기화하고,
        파일을 비우고 메모리 내 객체도 초기화합니다.
        (내부용 메서드로 이름 변경)
        """
        self.requests = {}
        self.tasks = {}
        save_requests(self.requests)
        save_tasks(self.tasks)
        logger.info("TaskManager: 모든 데이터가 내부적으로 초기화되었습니다.")
        return {"success": True, "message": "모든 데이터가 내부적으로 성공적으로 초기화되었습니다."}

# 전역 태스크 관리자 인스턴스
task_manager = TaskManager() 