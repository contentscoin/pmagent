#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
에이전트 코디네이터 모듈

다양한 에이전트(PM, 디자이너, 프론트엔드, 백엔드, AI 엔지니어) 간의 협업을 조율하는 
코디네이터 클래스를 제공합니다.
"""

import os
import json
import logging
import uuid
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentCoordinator:
    """
    에이전트 코디네이터 클래스
    
    다양한 에이전트 간의 협업을 조율하고 작업 흐름을 관리합니다.
    - 에이전트 등록 및 관리
    - 작업 할당 및 라우팅
    - 작업 진행 상황 추적
    - 작업 결과 수집 및 통합
    - 에이전트 간 의존성 관리
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        에이전트 코디네이터 초기화
        
        Args:
            data_dir: 데이터 저장 디렉토리 (기본값: 환경 변수 DATA_DIR 또는 "./data")
        """
        # 데이터 디렉토리 설정
        self.data_dir = data_dir or os.environ.get("DATA_DIR", "./data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 등록된 에이전트
        self.agents = {}
        
        # 작업 데이터
        self.tasks = {}
        self.agent_tasks = {}
        self.dependencies = {}
        
        # 작업 기록
        self.task_history = []
        
        # 에이전트 상태
        self.agent_status = {}
        
        # 데이터 로드
        self._load_data()
    
    def _load_data(self) -> None:
        """데이터 파일에서 데이터를 로드합니다."""
        agents_file = os.path.join(self.data_dir, "agents.json")
        tasks_file = os.path.join(self.data_dir, "coordinator_tasks.json")
        history_file = os.path.join(self.data_dir, "task_history.json")
        
        # 에이전트 데이터 로드
        if os.path.exists(agents_file):
            try:
                with open(agents_file, "r", encoding="utf-8") as f:
                    self.agents = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"잘못된 JSON 포맷: {agents_file}")
                self.agents = {}
        
        # 작업 데이터 로드
        if os.path.exists(tasks_file):
            try:
                with open(tasks_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", {})
                    self.agent_tasks = data.get("agent_tasks", {})
                    self.dependencies = data.get("dependencies", {})
                    self.agent_status = data.get("agent_status", {})
            except json.JSONDecodeError:
                logger.error(f"잘못된 JSON 포맷: {tasks_file}")
        
        # 작업 기록 로드
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    self.task_history = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"잘못된 JSON 포맷: {history_file}")
                self.task_history = []
    
    def _save_data(self) -> None:
        """현재 데이터를 파일에 저장합니다."""
        agents_file = os.path.join(self.data_dir, "agents.json")
        tasks_file = os.path.join(self.data_dir, "coordinator_tasks.json")
        history_file = os.path.join(self.data_dir, "task_history.json")
        
        # 에이전트 데이터 저장 (인스턴스 제외)
        agents_data = {}
        for agent_id, agent_info in self.agents.items():
            # 인스턴스 객체를 제외한 복사본 생성
            agent_data = agent_info.copy()
            if "instance" in agent_data:
                del agent_data["instance"]
            agents_data[agent_id] = agent_data
        
        with open(agents_file, "w", encoding="utf-8") as f:
            json.dump(agents_data, f, ensure_ascii=False, indent=2)
        
        # 작업 데이터 저장
        tasks_data = {
            "tasks": self.tasks,
            "agent_tasks": self.agent_tasks,
            "dependencies": self.dependencies,
            "agent_status": self.agent_status
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        
        # 작업 기록 저장
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(self.task_history, f, ensure_ascii=False, indent=2)
    
    def register_agent(self, agent_type: str, agent_instance: Any, capabilities: List[str] = None) -> str:
        """
        에이전트 등록
        
        Args:
            agent_type: 에이전트 유형 (pm, designer, frontend, backend, ai_engineer)
            agent_instance: 에이전트 인스턴스
            capabilities: 에이전트 기능 목록
            
        Returns:
            str: 에이전트 ID
        """
        agent_id = str(uuid.uuid4())
        
        # 에이전트 정보 등록 (에이전트 인스턴스는 메모리에만 저장)
        self.agents[agent_id] = {
            "id": agent_id,
            "type": agent_type,
            "instance": agent_instance,  # 메모리에만 저장됨
            "capabilities": capabilities or [],
            "registered_at": datetime.now().isoformat(),
            "status": "idle"
        }
        
        # 에이전트 상태 초기화
        self.agent_status[agent_id] = "idle"
        
        # 에이전트 유형별 작업 목록 초기화
        if agent_type not in self.agent_tasks:
            self.agent_tasks[agent_type] = []
        
        logger.info(f"{agent_type.capitalize()} 에이전트 등록 완료 (ID: {agent_id})")
        self._save_data()
        
        return agent_id
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        에이전트 등록 해제
        
        Args:
            agent_id: 에이전트 ID
            
        Returns:
            bool: 성공 여부
        """
        if agent_id in self.agents:
            agent_type = self.agents[agent_id]["type"]
            del self.agents[agent_id]
            
            if agent_id in self.agent_status:
                del self.agent_status[agent_id]
            
            logger.info(f"{agent_type.capitalize()} 에이전트 등록 해제 완료 (ID: {agent_id})")
            self._save_data()
            return True
        else:
            logger.warning(f"존재하지 않는 에이전트 ID: {agent_id}")
            return False
    
    def get_agents_by_type(self, agent_type: str) -> List[Dict[str, Any]]:
        """
        지정된 유형의 에이전트 목록 조회
        
        Args:
            agent_type: 에이전트 유형
            
        Returns:
            List[Dict[str, Any]]: 에이전트 정보 목록
        """
        return [
            {
                "id": agent_id,
                "type": info["type"],
                "capabilities": info["capabilities"],
                "status": self.agent_status.get(agent_id, "unknown"),
                "registered_at": info["registered_at"]
            }
            for agent_id, info in self.agents.items()
            if info["type"] == agent_type
        ]
    
    def get_all_agents(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        모든 에이전트 목록 조회
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: 에이전트 유형별 목록
        """
        result = {}
        
        for agent_id, info in self.agents.items():
            agent_type = info["type"]
            
            if agent_type not in result:
                result[agent_type] = []
            
            # 에이전트 인스턴스 필드 제외
            agent_info = {
                "id": agent_id,
                "capabilities": info["capabilities"],
                "status": self.agent_status.get(agent_id, "unknown"),
                "registered_at": info["registered_at"]
            }
            
            result[agent_type].append(agent_info)
        
        return result
    
    def create_task(self, title: str, description: str, agent_type: str, 
                    priority: int = 1, dependencies: List[str] = None) -> str:
        """
        새 작업 생성
        
        Args:
            title: 작업 제목
            description: 작업 설명
            agent_type: 담당 에이전트 유형
            priority: 우선순위 (1-5, 높을수록 중요)
            dependencies: 의존하는 작업 ID 목록
            
        Returns:
            str: 작업 ID
        """
        task_id = str(uuid.uuid4())
        
        # 작업 생성
        self.tasks[task_id] = {
            "id": task_id,
            "title": title,
            "description": description,
            "agent_type": agent_type,
            "status": "pending",
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "assigned_to": None,
            "result": None,
            "error": None
        }
        
        # 의존성 설정
        if dependencies:
            self.dependencies[task_id] = dependencies
        
        # 에이전트 유형별 작업 목록에 추가
        if agent_type in self.agent_tasks:
            self.agent_tasks[agent_type].append(task_id)
        else:
            self.agent_tasks[agent_type] = [task_id]
        
        # 기록 추가
        self.task_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "create",
            "task_id": task_id,
            "agent_type": agent_type,
            "details": {"title": title}
        })
        
        logger.info(f"작업 생성: {title} (ID: {task_id}, 에이전트: {agent_type})")
        self._save_data()
        
        return task_id
    
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """
        에이전트에 작업 할당
        
        Args:
            task_id: 작업 ID
            agent_id: 에이전트 ID
            
        Returns:
            bool: 성공 여부
        """
        if task_id not in self.tasks:
            logger.warning(f"존재하지 않는 작업 ID: {task_id}")
            return False
        
        if agent_id not in self.agents:
            logger.warning(f"존재하지 않는 에이전트 ID: {agent_id}")
            return False
        
        # 작업 상태 업데이트
        task = self.tasks[task_id]
        if task["status"] != "pending":
            logger.warning(f"작업 {task_id}를 할당할 수 없습니다. 현재 상태: {task['status']}")
            return False
        
        # 의존성 확인
        if task_id in self.dependencies:
            for dep_id in self.dependencies[task_id]:
                if dep_id in self.tasks and self.tasks[dep_id]["status"] != "completed":
                    logger.warning(f"작업 {task_id}의 의존성 {dep_id}가 완료되지 않았습니다.")
                    return False
        
        # 작업 할당
        agent_type = self.agents[agent_id]["type"]
        
        if task["agent_type"] != agent_type:
            logger.warning(f"에이전트 유형 불일치: {agent_type} != {task['agent_type']}")
            return False
        
        task["status"] = "assigned"
        task["assigned_to"] = agent_id
        task["updated_at"] = datetime.now().isoformat()
        
        # 에이전트 상태 업데이트
        self.agent_status[agent_id] = "busy"
        
        # 기록 추가
        self.task_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "assign",
            "task_id": task_id,
            "agent_id": agent_id,
            "details": {"agent_type": agent_type}
        })
        
        logger.info(f"작업 할당: {task_id} -> {agent_id} ({agent_type} 에이전트)")
        self._save_data()
        
        return True
    
    def complete_task(self, task_id: str, result: Any = None, error: str = None) -> bool:
        """
        작업 완료 처리
        
        Args:
            task_id: 작업 ID
            result: 작업 결과
            error: 오류 메시지 (실패한 경우)
            
        Returns:
            bool: 성공 여부
        """
        if task_id not in self.tasks:
            logger.warning(f"존재하지 않는 작업 ID: {task_id}")
            return False
        
        # 작업 상태 업데이트
        task = self.tasks[task_id]
        agent_id = task["assigned_to"]
        
        if not agent_id:
            logger.warning(f"작업 {task_id}가 할당되지 않았습니다.")
            return False
        
        if task["status"] not in ["assigned", "in_progress"]:
            logger.warning(f"작업 {task_id}를 완료할 수 없습니다. 현재 상태: {task['status']}")
            return False
        
        # 작업 완료 상태로 변경
        if error:
            task["status"] = "failed"
            task["error"] = error
        else:
            task["status"] = "completed"
            task["result"] = result
        
        task["updated_at"] = datetime.now().isoformat()
        task["completed_at"] = datetime.now().isoformat()
        
        # 에이전트 상태 업데이트
        self.agent_status[agent_id] = "idle"
        
        # 기록 추가
        self.task_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "complete" if not error else "fail",
            "task_id": task_id,
            "agent_id": agent_id,
            "details": {"has_result": result is not None, "has_error": error is not None}
        })
        
        logger.info(f"작업 {'완료' if not error else '실패'}: {task_id}")
        self._save_data()
        
        # 의존성 체크 - 이 작업에 의존하는 다른 작업이 있는지 확인
        dependent_tasks = []
        for t_id, deps in self.dependencies.items():
            if task_id in deps and t_id in self.tasks:
                dependent_tasks.append(t_id)
        
        # 의존성이 있는 작업들이 실행 가능한지 확인하고 알림
        if not error and dependent_tasks:
            for dep_task_id in dependent_tasks:
                if dep_task_id in self.tasks and self.tasks[dep_task_id]["status"] == "pending":
                    # 이 작업의 모든 의존성이 완료됐는지 확인
                    all_deps_completed = True
                    if dep_task_id in self.dependencies:
                        for dep_id in self.dependencies[dep_task_id]:
                            if dep_id in self.tasks and self.tasks[dep_id]["status"] != "completed":
                                all_deps_completed = False
                                break
                    
                    if all_deps_completed:
                        logger.info(f"작업 {dep_task_id}의 모든 의존성이 완료되었습니다. 실행 가능합니다.")
        
        return True
    
    def cancel_task(self, task_id: str, reason: str = None) -> bool:
        """
        작업 취소
        
        Args:
            task_id: 작업 ID
            reason: 취소 사유
            
        Returns:
            bool: 성공 여부
        """
        if task_id not in self.tasks:
            logger.warning(f"존재하지 않는 작업 ID: {task_id}")
            return False
        
        # 작업 상태 업데이트
        task = self.tasks[task_id]
        agent_id = task["assigned_to"]
        
        if task["status"] in ["completed", "failed", "cancelled"]:
            logger.warning(f"작업 {task_id}는 이미 {task['status']} 상태입니다.")
            return False
        
        task["status"] = "cancelled"
        task["updated_at"] = datetime.now().isoformat()
        task["error"] = reason or "작업 취소됨"
        
        # 에이전트 상태 업데이트
        if agent_id and agent_id in self.agent_status:
            self.agent_status[agent_id] = "idle"
        
        # 기록 추가
        self.task_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "cancel",
            "task_id": task_id,
            "details": {"reason": reason or "Not specified"}
        })
        
        logger.info(f"작업 취소: {task_id}")
        self._save_data()
        
        return True
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        작업 정보 조회
        
        Args:
            task_id: 작업 ID
            
        Returns:
            Optional[Dict[str, Any]]: 작업 정보
        """
        if task_id not in self.tasks:
            logger.warning(f"존재하지 않는 작업 ID: {task_id}")
            return None
        
        # 작업 정보 반환
        task_data = self.tasks[task_id].copy()
        
        # 의존성 정보 추가
        task_data["dependencies"] = self.dependencies.get(task_id, [])
        
        # 에이전트 정보 추가
        agent_id = task_data["assigned_to"]
        if agent_id and agent_id in self.agents:
            agent_info = self.agents[agent_id]
            task_data["agent_info"] = {
                "id": agent_id,
                "type": agent_info["type"],
                "status": self.agent_status.get(agent_id, "unknown")
            }
        
        return task_data
    
    def get_tasks_by_agent_type(self, agent_type: str) -> List[Dict[str, Any]]:
        """
        에이전트 유형별 작업 목록 조회
        
        Args:
            agent_type: 에이전트 유형
            
        Returns:
            List[Dict[str, Any]]: 작업 정보 목록
        """
        if agent_type not in self.agent_tasks:
            return []
        
        # 작업 정보 목록 생성
        tasks = []
        for task_id in self.agent_tasks[agent_type]:
            if task_id in self.tasks:
                task_data = self.tasks[task_id].copy()
                task_data["dependencies"] = self.dependencies.get(task_id, [])
                tasks.append(task_data)
        
        # 우선순위 및 상태별 정렬
        tasks.sort(key=lambda t: (
            # 1. 상태 (pending > assigned > in_progress > completed > failed > cancelled)
            {"pending": 0, "assigned": 1, "in_progress": 2, "completed": 3, "failed": 4, "cancelled": 5}.get(t["status"], 99),
            # 2. 우선순위 (높은 값이 먼저)
            -t["priority"],
            # 3. 생성 시간 (오래된 순)
            t["created_at"]
        ))
        
        return tasks
    
    def get_next_available_task(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """
        다음 실행 가능한 작업 조회
        
        Args:
            agent_type: 에이전트 유형
            
        Returns:
            Optional[Dict[str, Any]]: 작업 정보
        """
        if agent_type not in self.agent_tasks:
            return None
        
        # 실행 가능한 작업 찾기
        for task_id in self.agent_tasks[agent_type]:
            if task_id in self.tasks and self.tasks[task_id]["status"] == "pending":
                # 의존성 확인
                if task_id in self.dependencies:
                    all_deps_completed = True
                    for dep_id in self.dependencies[task_id]:
                        if dep_id in self.tasks and self.tasks[dep_id]["status"] != "completed":
                            all_deps_completed = False
                            break
                    
                    if not all_deps_completed:
                        continue
                
                # 의존성이 모두 충족된 작업 반환
                task_data = self.tasks[task_id].copy()
                task_data["dependencies"] = self.dependencies.get(task_id, [])
                return task_data
        
        return None
    
    def execute_task_with_agent(self, task_id: str, agent_id: str = None) -> Tuple[bool, Any, Optional[str]]:
        """
        에이전트를 사용하여 작업 실행
        
        Args:
            task_id: 작업 ID
            agent_id: 에이전트 ID (지정하지 않으면 자동 선택)
            
        Returns:
            Tuple[bool, Any, Optional[str]]: (성공 여부, 작업 결과, 오류 메시지)
        """
        if task_id not in self.tasks:
            logger.warning(f"존재하지 않는 작업 ID: {task_id}")
            return False, None, "존재하지 않는 작업 ID"
        
        task = self.tasks[task_id]
        agent_type = task["agent_type"]
        
        # 에이전트 선택
        if not agent_id:
            # 해당 유형의 사용 가능한 에이전트 찾기
            available_agents = [
                aid for aid, info in self.agents.items()
                if info["type"] == agent_type and self.agent_status.get(aid) == "idle"
            ]
            
            if not available_agents:
                logger.warning(f"사용 가능한 {agent_type} 에이전트가 없습니다.")
                return False, None, f"사용 가능한 {agent_type} 에이전트가 없습니다."
            
            agent_id = available_agents[0]
        
        # 에이전트 유효성 확인
        if agent_id not in self.agents:
            logger.warning(f"존재하지 않는 에이전트 ID: {agent_id}")
            return False, None, "존재하지 않는 에이전트 ID"
        
        if self.agents[agent_id]["type"] != agent_type:
            logger.warning(f"에이전트 유형 불일치: {self.agents[agent_id]['type']} != {agent_type}")
            return False, None, "에이전트 유형 불일치"
        
        # 작업 할당
        if not self.assign_task(task_id, agent_id):
            return False, None, "작업 할당 실패"
        
        # 작업 실행
        try:
            task["status"] = "in_progress"
            task["updated_at"] = datetime.now().isoformat()
            self._save_data()
            
            # 에이전트 인스턴스 가져오기
            agent_instance = self.agents[agent_id]["instance"]
            
            # 작업 실행
            try:
                result = agent_instance.run_task({
                    "task_id": task_id,
                    "title": task["title"],
                    "description": task["description"]
                })
                
                # 작업 완료 처리
                self.complete_task(task_id, result)
                return True, result, None
            except Exception as e:
                logger.error(f"작업 실행 중 오류 발생: {str(e)}")
                # 작업 실패 처리
                self.complete_task(task_id, None, str(e))
                return False, None, str(e)
        except Exception as e:
            logger.error(f"작업 처리 중 오류 발생: {str(e)}")
            return False, None, str(e)
    
    def get_workflow_status(self, task_ids: List[str] = None) -> Dict[str, Any]:
        """
        작업 흐름 상태 조회
        
        Args:
            task_ids: 작업 ID 목록 (지정하지 않으면 전체 작업)
            
        Returns:
            Dict[str, Any]: 작업 흐름 상태 정보
        """
        # 작업 ID 목록이 지정되지 않은 경우 전체 작업
        if not task_ids:
            task_ids = list(self.tasks.keys())
        
        # 작업 상태 통계
        status_counts = {
            "pending": 0,
            "assigned": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        # 에이전트 유형별 작업 수
        agent_type_counts = {}
        
        # 작업 목록
        tasks_data = []
        
        for task_id in task_ids:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                
                # 상태 카운트 증가
                status = task["status"]
                if status in status_counts:
                    status_counts[status] += 1
                
                # 에이전트 유형별 카운트
                agent_type = task["agent_type"]
                if agent_type in agent_type_counts:
                    agent_type_counts[agent_type] += 1
                else:
                    agent_type_counts[agent_type] = 1
                
                # 작업 정보 추가
                task_data = {
                    "id": task_id,
                    "title": task["title"],
                    "status": status,
                    "agent_type": agent_type,
                    "priority": task["priority"],
                    "created_at": task["created_at"],
                    "updated_at": task["updated_at"],
                    "dependencies": self.dependencies.get(task_id, [])
                }
                tasks_data.append(task_data)
        
        # 의존성 그래프 구성
        dependency_graph = {}
        for task_id in task_ids:
            if task_id in self.dependencies:
                dependency_graph[task_id] = self.dependencies[task_id]
        
        # 결과 구성
        result = {
            "status_counts": status_counts,
            "agent_type_counts": agent_type_counts,
            "tasks": tasks_data,
            "dependency_graph": dependency_graph,
            "registered_agents": {
                agent_type: len(self.get_agents_by_type(agent_type))
                for agent_type in set(info["type"] for info in self.agents.values())
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return result
    
    def get_agent_workload(self) -> Dict[str, Dict[str, Any]]:
        """
        에이전트별 작업 부하 조회
        
        Returns:
            Dict[str, Dict[str, Any]]: 에이전트별 작업 부하 정보
        """
        result = {}
        
        for agent_id, agent_info in self.agents.items():
            agent_type = agent_info["type"]
            
            # 에이전트에 할당된 작업 목록
            assigned_tasks = []
            for task_id, task in self.tasks.items():
                if task["assigned_to"] == agent_id:
                    assigned_tasks.append({
                        "id": task_id,
                        "title": task["title"],
                        "status": task["status"],
                        "priority": task["priority"],
                        "created_at": task["created_at"],
                        "updated_at": task["updated_at"]
                    })
            
            # 에이전트가 담당할 수 있는 대기 중인 작업 목록
            pending_tasks = []
            if agent_type in self.agent_tasks:
                for task_id in self.agent_tasks[agent_type]:
                    task = self.tasks.get(task_id)
                    if task and task["status"] == "pending":
                        # 의존성 확인
                        if task_id in self.dependencies:
                            all_deps_completed = True
                            for dep_id in self.dependencies[task_id]:
                                if dep_id in self.tasks and self.tasks[dep_id]["status"] != "completed":
                                    all_deps_completed = False
                                    break
                            
                            if not all_deps_completed:
                                continue
                        
                        pending_tasks.append({
                            "id": task_id,
                            "title": task["title"],
                            "priority": task["priority"],
                            "created_at": task["created_at"]
                        })
            
            # 에이전트 작업 부하 정보
            result[agent_id] = {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "status": self.agent_status.get(agent_id, "unknown"),
                "registered_at": agent_info["registered_at"],
                "assigned_task_count": len(assigned_tasks),
                "pending_task_count": len(pending_tasks),
                "assigned_tasks": assigned_tasks,
                "pending_tasks": pending_tasks
            }
        
        return result 