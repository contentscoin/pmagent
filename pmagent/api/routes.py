#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent API 라우트 모듈

에이전트 협업 시스템을 위한 RESTful API 라우트를 제공합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
import uuid
from datetime import datetime

# PMAgent 모듈 가져오기
from ..auth import AuthManager
from ..agent_coordinator import AgentCoordinator
from ..distributed_storage import DistributedStorage

# 라우터 및 인증 설정
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# 로거 설정
logger = logging.getLogger(__name__)

# 인증 관리자, 에이전트 코디네이터, 저장소 인스턴스
# 사용 전에 초기화 필요
auth_manager = None
agent_coordinator = None
storage = None

# 의존성 주입을 위한 함수들
def get_auth_manager():
    if auth_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인증 관리자가 초기화되지 않았습니다."
        )
    return auth_manager

def get_agent_coordinator():
    if agent_coordinator is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="에이전트 코디네이터가 초기화되지 않았습니다."
        )
    return agent_coordinator

def get_storage():
    if storage is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="분산 저장소가 초기화되지 않았습니다."
        )
    return storage

# 토큰 확인
async def verify_token(token: str = Depends(oauth2_scheme)):
    auth = get_auth_manager()
    result = auth.validate_token(token)
    
    if not result["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return result

# 관리자 권한 확인
async def verify_admin(token_info: Dict[str, Any] = Depends(verify_token)):
    if token_info.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return token_info

# 모델 정의
class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    role: str = "user"

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

class AgentRegister(BaseModel):
    agent_type: str
    capabilities: List[str] = []

class AgentBulkRegister(BaseModel):
    agents: List[AgentRegister]

class TaskCreate(BaseModel):
    title: str
    description: str
    agent_type: str
    priority: int = 1
    dependencies: List[str] = []

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None

class TaskBulkCreate(BaseModel):
    tasks: List[TaskCreate]

class WorkflowCreate(BaseModel):
    name: str
    description: str
    tasks: List[TaskCreate]

# API 라우트
# 인증 관련 엔드포인트
@router.post("/auth/token", response_model=Dict[str, Any])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), auth: AuthManager = Depends(get_auth_manager)):
    user_id = auth.authenticate_user(form_data.username, form_data.password)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 사용자명 또는 비밀번호입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = auth.generate_auth_tokens(user_id)
    return tokens

@router.post("/auth/refresh", response_model=Dict[str, Any])
async def refresh_token(refresh_token: str = Body(..., embed=True), auth: AuthManager = Depends(get_auth_manager)):
    new_tokens = auth.refresh_access_token(refresh_token)
    
    if not new_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return new_tokens

@router.post("/auth/revoke", response_model=Dict[str, Any])
async def revoke_token(token_info: Dict[str, Any] = Depends(verify_token), auth: AuthManager = Depends(get_auth_manager)):
    token = token_info.get("token")
    success = auth.revoke_token(token)
    
    return {"success": success}

# 사용자 관련 엔드포인트
@router.post("/users", response_model=Dict[str, Any], dependencies=[Depends(verify_admin)])
async def create_user(user: UserCreate, auth: AuthManager = Depends(get_auth_manager)):
    try:
        user_id = auth.create_user(
            username=user.username,
            password=user.password,
            email=user.email,
            role=user.role
        )
        
        return {"user_id": user_id, "username": user.username, "role": user.role}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/users/me", response_model=Dict[str, Any])
async def get_current_user(token_info: Dict[str, Any] = Depends(verify_token), auth: AuthManager = Depends(get_auth_manager)):
    user_id = token_info.get("user_id")
    user_info = auth.get_user_info(user_id)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    
    return user_info

@router.get("/users", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_admin)])
async def list_users(auth: AuthManager = Depends(get_auth_manager)):
    return auth.list_users()

@router.get("/users/{user_id}", response_model=Dict[str, Any], dependencies=[Depends(verify_admin)])
async def get_user(user_id: str, auth: AuthManager = Depends(get_auth_manager)):
    user_info = auth.get_user_info(user_id)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    
    return user_info

@router.put("/users/{user_id}", response_model=Dict[str, Any], dependencies=[Depends(verify_admin)])
async def update_user(user_id: str, user: UserUpdate, auth: AuthManager = Depends(get_auth_manager)):
    try:
        data = user.dict(exclude_unset=True)
        success = auth.update_user(user_id, data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        return {"user_id": user_id, "success": True}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/users/{user_id}", response_model=Dict[str, Any], dependencies=[Depends(verify_admin)])
async def delete_user(user_id: str, auth: AuthManager = Depends(get_auth_manager)):
    try:
        success = auth.delete_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        return {"success": True}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# 에이전트 관련 엔드포인트
@router.post("/agents/register", response_model=Dict[str, Any])
async def register_agent(
    agent: AgentRegister,
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    # 인증된 에이전트나 관리자만 에이전트 등록 가능
    if token_info.get("token_type") != "agent" and token_info.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="에이전트 등록 권한이 없습니다."
        )
    
    # 에이전트 등록
    try:
        # 실제 구현에서는 에이전트 인스턴스 생성 필요
        # 지금은 모의 객체 사용
        agent_instance = {"type": agent.agent_type}
        
        agent_id = coordinator.register_agent(
            agent_type=agent.agent_type,
            agent_instance=agent_instance,
            capabilities=agent.capabilities
        )
        
        # 에이전트 토큰 생성
        auth = get_auth_manager()
        token = auth.create_agent_token(agent_id, agent.agent_type, agent.capabilities)
        
        return {
            "agent_id": agent_id,
            "agent_type": agent.agent_type,
            "token": token
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"에이전트 등록 중 오류 발생: {str(e)}"
        )

@router.post("/agents/bulk-register", response_model=List[Dict[str, Any]], dependencies=[Depends(verify_admin)])
async def bulk_register_agents(
    agents: AgentBulkRegister,
    coordinator: AgentCoordinator = Depends(get_agent_coordinator),
    auth: AuthManager = Depends(get_auth_manager)
):
    results = []
    
    for agent_data in agents.agents:
        try:
            # 실제 구현에서는 에이전트 인스턴스 생성 필요
            agent_instance = {"type": agent_data.agent_type}
            
            agent_id = coordinator.register_agent(
                agent_type=agent_data.agent_type,
                agent_instance=agent_instance,
                capabilities=agent_data.capabilities
            )
            
            # 에이전트 토큰 생성
            token = auth.create_agent_token(agent_id, agent_data.agent_type, agent_data.capabilities)
            
            results.append({
                "agent_id": agent_id,
                "agent_type": agent_data.agent_type,
                "token": token,
                "success": True
            })
        except Exception as e:
            results.append({
                "agent_type": agent_data.agent_type,
                "error": str(e),
                "success": False
            })
    
    return results

@router.get("/agents", response_model=Dict[str, List[Dict[str, Any]]])
async def list_agents(
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    # 인증된 사용자면 에이전트 목록 조회 가능
    return coordinator.get_all_agents()

@router.get("/agents/{agent_type}", response_model=List[Dict[str, Any]])
async def get_agents_by_type(
    agent_type: str,
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    return coordinator.get_agents_by_type(agent_type)

@router.delete("/agents/{agent_id}", response_model=Dict[str, Any], dependencies=[Depends(verify_admin)])
async def unregister_agent(
    agent_id: str,
    coordinator: AgentCoordinator = Depends(get_agent_coordinator),
    auth: AuthManager = Depends(get_auth_manager)
):
    # 에이전트 등록 해제
    success = coordinator.unregister_agent(agent_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="에이전트를 찾을 수 없습니다."
        )
    
    # 에이전트 토큰 취소
    auth.revoke_agent_token(agent_id)
    
    return {"success": True}

# 작업 관련 엔드포인트
@router.post("/tasks", response_model=Dict[str, Any])
async def create_task(
    task: TaskCreate,
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    # 작업 생성
    try:
        task_id = coordinator.create_task(
            title=task.title,
            description=task.description,
            agent_type=task.agent_type,
            priority=task.priority,
            dependencies=task.dependencies
        )
        
        return {
            "task_id": task_id,
            "title": task.title,
            "agent_type": task.agent_type
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"작업 생성 중 오류 발생: {str(e)}"
        )

@router.post("/tasks/bulk", response_model=List[Dict[str, Any]])
async def bulk_create_tasks(
    tasks: TaskBulkCreate,
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    results = []
    
    for task_data in tasks.tasks:
        try:
            task_id = coordinator.create_task(
                title=task_data.title,
                description=task_data.description,
                agent_type=task_data.agent_type,
                priority=task_data.priority,
                dependencies=task_data.dependencies
            )
            
            results.append({
                "task_id": task_id,
                "title": task_data.title,
                "agent_type": task_data.agent_type,
                "success": True
            })
        except Exception as e:
            results.append({
                "title": task_data.title,
                "agent_type": task_data.agent_type,
                "error": str(e),
                "success": False
            })
    
    return results

@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task(
    task_id: str,
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    task = coordinator.get_task(task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작업을 찾을 수 없습니다."
        )
    
    return task

@router.put("/tasks/{task_id}", response_model=Dict[str, Any])
async def update_task(
    task_id: str,
    task: TaskUpdate,
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    # 작업 정보 가져오기
    current_task = coordinator.get_task(task_id)
    
    if not current_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작업을 찾을 수 없습니다."
        )
    
    # 작업 업데이트 (실제로는 구현 필요)
    # 여기서는 작업이 있는지만 확인
    
    return {
        "task_id": task_id,
        "success": True
    }

@router.post("/tasks/{task_id}/assign/{agent_id}", response_model=Dict[str, Any])
async def assign_task(
    task_id: str,
    agent_id: str,
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    success = coordinator.assign_task(task_id, agent_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="작업 할당에 실패했습니다."
        )
    
    return {
        "task_id": task_id,
        "agent_id": agent_id,
        "success": True
    }

@router.post("/tasks/{task_id}/execute", response_model=Dict[str, Any])
async def execute_task(
    task_id: str,
    agent_id: Optional[str] = None,
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    success, result, error = coordinator.execute_task_with_agent(task_id, agent_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"작업 실행에 실패했습니다: {error}"
        )
    
    return {
        "task_id": task_id,
        "success": True,
        "result": result
    }

@router.post("/tasks/{task_id}/complete", response_model=Dict[str, Any])
async def complete_task(
    task_id: str,
    result: Any = Body(None),
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    success = coordinator.complete_task(task_id, result)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="작업 완료 처리에 실패했습니다."
        )
    
    return {
        "task_id": task_id,
        "success": True
    }

@router.post("/tasks/{task_id}/fail", response_model=Dict[str, Any])
async def fail_task(
    task_id: str,
    error: str = Body(..., embed=True),
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    success = coordinator.complete_task(task_id, None, error)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="작업 실패 처리에 실패했습니다."
        )
    
    return {
        "task_id": task_id,
        "success": True
    }

@router.get("/tasks/{agent_type}/next", response_model=Optional[Dict[str, Any]])
async def get_next_task(
    agent_type: str,
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    # 토큰이 해당 에이전트 유형과 일치하는지 확인
    if token_info.get("token_type") == "agent" and token_info.get("agent_type") != agent_type:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다."
        )
    
    task = coordinator.get_next_available_task(agent_type)
    
    return task

@router.get("/tasks/agent/{agent_type}", response_model=List[Dict[str, Any]])
async def get_tasks_by_agent_type(
    agent_type: str,
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    return coordinator.get_tasks_by_agent_type(agent_type)

@router.get("/workflow/status", response_model=Dict[str, Any])
async def get_workflow_status(
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    return coordinator.get_workflow_status()

@router.get("/agents/workload", response_model=Dict[str, Dict[str, Any]])
async def get_agent_workload(
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    return coordinator.get_agent_workload()

# 워크플로우 관련 엔드포인트
@router.post("/workflow", response_model=Dict[str, Any])
async def create_workflow(
    workflow: WorkflowCreate,
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator),
    db: DistributedStorage = Depends(get_storage)
):
    try:
        # 작업 목록 생성
        task_ids = []
        for task_data in workflow.tasks:
            task_id = coordinator.create_task(
                title=task_data.title,
                description=task_data.description,
                agent_type=task_data.agent_type,
                priority=task_data.priority,
                dependencies=task_data.dependencies
            )
            task_ids.append(task_id)
        
        # 워크플로우 정보 저장
        workflow_id = str(uuid.uuid4())
        workflow_data = {
            "id": workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "task_ids": task_ids,
            "created_at": datetime.now().isoformat(),
            "created_by": token_info.get("user_id") or token_info.get("agent_id"),
            "status": "active"
        }
        
        db.put(f"workflows:{workflow_id}", workflow_data)
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "task_count": len(task_ids)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"워크플로우 생성 중 오류 발생: {str(e)}"
        )

@router.get("/workflow/{workflow_id}", response_model=Dict[str, Any])
async def get_workflow(
    workflow_id: str,
    token_info: Dict[str, Any] = Depends(verify_token),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator),
    db: DistributedStorage = Depends(get_storage)
):
    workflow_data = db.get(f"workflows:{workflow_id}")
    
    if not workflow_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="워크플로우를 찾을 수 없습니다."
        )
    
    # 작업 정보 추가
    tasks = []
    for task_id in workflow_data.get("task_ids", []):
        task = coordinator.get_task(task_id)
        if task:
            tasks.append(task)
    
    workflow_data["tasks"] = tasks
    
    return workflow_data

@router.get("/workflows", response_model=List[Dict[str, Any]])
async def list_workflows(
    token_info: Dict[str, Any] = Depends(verify_token),
    db: DistributedStorage = Depends(get_storage)
):
    workflow_keys = db.list_keys("workflows:")
    workflows = []
    
    for key in workflow_keys:
        workflow_data = db.get(key)
        if workflow_data:
            # 상세 정보는 제외하고 기본 정보만 포함
            workflows.append({
                "id": workflow_data.get("id"),
                "name": workflow_data.get("name"),
                "description": workflow_data.get("description"),
                "created_at": workflow_data.get("created_at"),
                "status": workflow_data.get("status"),
                "task_count": len(workflow_data.get("task_ids", []))
            })
    
    return workflows 