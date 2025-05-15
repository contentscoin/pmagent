#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP 서버 모듈

Model Context Protocol(MCP)를 구현하는 서버를 제공합니다.
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# MCP 도구 관련 모듈 가져오기
from pmagent.task_manager import task_manager as global_task_manager # 점진적으로 사용 줄일 예정
from pmagent.mcp_common import MCPServer
from pmagent.mcp_agent_api import create_mcp_api
import pmagent.db_manager as db_manager # 이 임포트는 이미 절대 경로 스타일임
import uuid # project_id, task_id 생성용

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Lifespan 이벤트 핸들러 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 애플리케이션 시작 시 실행될 코드
    logger.info("FastAPI application startup.")
    try:
        logger.info("Initializing databases...")
        db_manager.init_project_master_db()
        db_manager.init_agent_shared_db()
        logger.info("Databases initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing databases: {str(e)}")
        # DB 초기화 실패 시 서버를 계속 실행할지, 아니면 종료할지 결정 필요
        # 여기서는 로깅만 하고 계속 진행하도록 둡니다.

    yield # 애플리케이션 실행

    # 애플리케이션 종료 시 실행될 코드
    logger.info("FastAPI application shutting down.")
    # 기존 global_task_manager._save_data()는 이제 사용하지 않으므로 주석 처리 또는 삭제
    # try:
    #     global_task_manager._save_data() # 종료 시 데이터 저장
    #     logger.info("Task manager data saved successfully on shutdown.")
    # except Exception as e:
    #     logger.error(f"Error saving task manager data on shutdown: {str(e)}")

# FastAPI 애플리케이션 생성 (lifespan 추가)
app = FastAPI(
    title="PMAgent MCP Server",
    description="프로젝트 관리를 위한 MCP(Model Context Protocol) 서버",
    version="0.1.0",
    lifespan=lifespan # lifespan 컨텍스트 매니저 등록
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 마운트
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public")
Path(static_dir).mkdir(exist_ok=True, parents=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# MCP 도구 정의
TOOLS = [
    {
        "name": "request_planning",
        "description": "새 요청을 등록하고 태스크를 계획합니다.",
        "parameters": {
            "originalRequest": "원본 요청 내용",
            "tasks": "태스크 목록 (title과 description이 포함된 객체 배열)",
            "splitDetails": "요청 분할 상세 정보 (선택)"
        }
    },
    {
        "name": "get_next_task",
        "description": "다음 대기 중인 태스크(아직 완료되지 않은)를 가져옵니다.",
        "parameters": {
            "requestId": "요청 ID",
            "agentId": "작업을 요청하는 에이전트 ID"
        }
    },
    {
        "name": "mark_task_done",
        "description": "태스크를 완료 상태로 표시합니다.",
        "parameters": {
            "requestId": "요청 ID",
            "taskId": "태스크 ID",
            "agentId": "작업을 완료하는 에이전트 ID",
            "completedDetails": "완료 상세 정보 (선택)"
        }
    },
    {
        "name": "approve_task_completion",
        "description": "완료된 태스크를 승인합니다.",
        "parameters": {
            "requestId": "요청 ID",
            "taskId": "태스크 ID"
        }
    },
    {
        "name": "approve_request_completion",
        "description": "요청 전체의 완료를 승인합니다.",
        "parameters": {
            "requestId": "요청 ID"
        }
    },
    {
        "name": "add_tasks_to_request",
        "description": "기존 요청에 새 태스크를 추가합니다.",
        "parameters": {
            "requestId": "요청 ID",
            "tasks": "추가할 태스크 목록 (title과 description이 포함된 객체 배열)"
        }
    },
    {
        "name": "update_task",
        "description": "태스크 정보를 업데이트합니다.",
        "parameters": {
            "requestId": "요청 ID",
            "taskId": "태스크 ID",
            "title": "새 태스크 제목 (선택)",
            "description": "새 태스크 설명 (선택)"
        }
    },
    {
        "name": "delete_task",
        "description": "태스크를 삭제합니다.",
        "parameters": {
            "requestId": "요청 ID",
            "taskId": "태스크 ID"
        }
    },
    {
        "name": "list_requests",
        "description": "모든 요청 목록을 가져옵니다.",
        "parameters": {}
    },
    {
        "name": "open_task_details",
        "description": "태스크 상세 정보를 가져옵니다.",
        "parameters": {
            "taskId": "태스크 ID"
        }
    },
    {
        "name": "clear_all_data",
        "description": "모든 요청 및 태스크 데이터를 초기화합니다. (테스트용)",
        "parameters": {
            "confirmation": "데이터 삭제를 확인하려면 \"CLEAR_ALL_MY_DATA\"를 입력하세요."
        }
    }
]

# MCP 도구 구현 함수
def request_planning(params: Dict[str, Any]): # 타입 힌트 명시
    """새 요청을 등록하고 태스크를 계획합니다."""
    try:
        logger.info(f"request_planning 호출됨: params={params}")
        
        original_request_content = params.get("originalRequest")
        tasks_data = params.get("tasks")
        project_name_param = params.get("projectName") # PMAgent가 project 이름을 줄 수 있도록 가정

        if not original_request_content:
            raise ValueError("Original request content (originalRequest) is required.")
        if not tasks_data or not isinstance(tasks_data, list):
            raise ValueError("Tasks list (tasks) is required and must be an array.")

        project_id_param = params.get("projectId") # PMAgent가 project ID를 전달할 경우

        if project_id_param:
            project_id = project_id_param
            # 기존 프로젝트가 있는지 확인
            if not db_manager.get_project(project_id):
                 # 프로젝트 이름 결정 (PMAgent가 전달한 이름을 우선 사용, 없으면 기본값)
                project_name = project_name_param if project_name_param else f"Project for request {datetime.now().strftime('%Y%m%d%H%M%S')}"
                logger.info(f"Attempting to add new project with provided ID: ID={project_id}, Name={project_name}")
                created_project_id = db_manager.add_project(project_id=project_id, project_name=project_name)
                if not created_project_id:
                    logger.error(f"Failed to create project with provided ID: {project_id}")
                    raise HTTPException(status_code=500, detail=f"Failed to initialize project in DB with ID: {project_id}")
            else:
                logger.info(f"Using existing project with ID: {project_id}")
                created_project_id = project_id # 이미 존재하는 프로젝트 ID 사용
        else:
            project_id = f"proj_{uuid.uuid4().hex[:8]}" # 고유한 새 프로젝트 ID 생성
            project_name = project_name_param if project_name_param else f"Project for request {datetime.now().strftime('%Y%m%d%H%M%S')}"
            logger.info(f"Attempting to add new project: ID={project_id}, Name={project_name}")
            created_project_id = db_manager.add_project(project_id=project_id, project_name=project_name)
            if not created_project_id:
                logger.error(f"Failed to create new project with ID: {project_id}")
                raise HTTPException(status_code=500, detail=f"Failed to initialize new project in DB for ID: {project_id}")

        logger.info(f"Project (ID: {created_project_id}) ready in ProjectMasterDB.")

        created_task_ids = []
        for i, task_data in enumerate(tasks_data):
            if not isinstance(task_data, dict):
                logger.warning(f"Task data at index {i} is not a dict, attempting to convert: {task_data}")
                try:
                    task_data = dict(task_data)
                except (TypeError, ValueError):
                    raise ValueError(f"Task data at index {i} could not be converted to a dict: {task_data}")

            task_title = task_data.get("title")
            if not task_title:
                raise ValueError(f"Task at index {i} is missing a 'title'.")

            task_id = task_data.get("id") or task_data.get("task_id") or f"task_{uuid.uuid4().hex[:10]}"
            description = task_data.get("description")
            status = task_data.get("status", 'pending') # PMAgent가 상태를 지정할 수 있도록
            assigned_to = task_data.get("assigned_to") or task_data.get("assigned_to_agent_type")
            dependencies = task_data.get("dependencies")

            logger.info(f"Adding task to DB: ID={task_id}, Title='{task_title}', ProjectID={created_project_id}, AssignedTo='{assigned_to}', Dependencies={dependencies}, Status='{status}'")
            
            # ID가 이미 존재하는지 확인 (PMAgent가 ID를 제공한 경우)
            if db_manager.get_master_task(task_id):
                logger.warning(f"Task with ID {task_id} already exists. Updating instead of adding.")
                # 여기서 업데이트 로직을 호출하거나, ID를 새로 생성하도록 처리할 수 있습니다.
                # 지금은 간단히 경고만 하고 넘어갑니다. 또는 add_master_task가 ID 중복 시 예외를 발생시키도록 할 수 있습니다.
                # 여기서는 add_master_task가 None을 반환하면 실패로 간주하고 다음으로 넘어가지 않도록 수정.
                # 아니면, ID가 있으면 update, 없으면 insert 하는 upsert 로직이 필요합니다.
                # 현재 db_manager.add_master_task는 ID 중복 시 None을 반환하므로, 아래 로직으로 충분합니다.
                # 다만, 이 경우 PMAgent가 생성한 ID와 다른 ID로 저장될 수 있으므로 주의가 필요합니다.
                # PMAgent가 생성한 ID를 그대로 사용하고 싶다면, add_master_task에서 ID 중복 시 예외를 발생시키고, 
                # 여기서 try-except로 잡아서 update_master_task를 호출하는 방식이 더 명확할 수 있습니다.
                # 지금은 PMAgent가 제공한 ID로 추가 시도, 실패 시 다음으로 넘어가지 않음
                pass # ID 중복 시 add_master_task가 None을 반환할 것이므로 아래에서 처리됨

            db_task_id_returned = db_manager.add_master_task(
                task_id=task_id, # PMAgent가 제공한 ID 또는 새로 생성된 ID
                project_id=created_project_id,
                title=task_title,
                description=description,
                status=status,
                assigned_to_agent_type=assigned_to,
                dependencies=dependencies
            )
            if not db_task_id_returned:
                logger.error(f"Failed to add task '{task_title}' (ID: {task_id}) to DB. It might already exist or another error occurred.")
                # raise HTTPException(status_code=500, detail=f"Failed to save task '{task_title}' to DB.")
            else:
                created_task_ids.append(db_task_id_returned) # 실제 저장된 (또는 생성된) ID 사용
        
        logger.info(f"All tasks from planning request processed for project {created_project_id}. Total tasks effectively added/updated: {len(created_task_ids)}")

        return {
            "message": "Planning request processed successfully.",
            "project_id": created_project_id,
            "task_ids": created_task_ids,
        }

    except ValueError as ve:
        logger.error(f"ValueError in request_planning: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error in request_planning: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

def get_next_task(params: Dict[str, Any]): # 타입 힌트 명시
    """다음 대기 중인 태스크를 가져옵니다."""
    try:
        logger.info(f"get_next_task 호출됨: params={params}")
        # request_id는 이제 특정 프로젝트 컨텍스트를 직접 참조하는 project_id로 해석될 수 있음
        # 또는, PMAgent가 여전히 request_id 스타일로 관리하고 서버가 project_id로 매핑할 수도 있음
        # 여기서는 params에서 project_id와 agent_type을 받는다고 가정 (PMAgent의 plan_request에서 projectId를 반환했으므로)
        project_id_param = params.get("projectId") # BackendAgent가 어떤 프로젝트의 태스크를 요청하는지
        agent_type = params.get("agentType") # 어떤 유형의 에이전트가 태스크를 요청하는지 (예: "BackendAgent")
        # agent_id = params.get("agentId") # 특정 에이전트 인스턴스 ID

        if not agent_type:
            raise ValueError("agentType is required to get the next task.")
        
        # project_id_param은 선택적일 수 있음. 없다면 해당 agent_type의 모든 프로젝트에서 태스크를 찾음.
        task = db_manager.get_pending_assignable_task_for_agent(agent_type=agent_type, project_id=project_id_param)

        if task:
            project_id = task.get("project_id")
            project_details = db_manager.get_project(project_id) if project_id else None
            project_name = project_details.get("project_name") if project_details else "Unknown Project"

            # 태스크 상태를 'assigned'로 업데이트 (선택적: 에이전트가 받으면 바로 assigned로 변경)
            # db_manager.update_master_task_status(task['task_id'], 'assigned') 
            # logger.info(f"Task {task['task_id']} assigned to {agent_type} for project {project_id}")

            return {
                "success": True, 
                "hasNextTask": True, 
                "projectId": project_id, 
                "projectName": project_name,
                "task": task
            }
        else:
            logger.info(f"No assignable tasks found for agentType '{agent_type}' (Project: {project_id_param if project_id_param else 'Any'})")
            return {"success": True, "hasNextTask": False, "message": f"No pending tasks for agentType '{agent_type}'."}
    except ValueError as ve:
        logger.error(f"ValueError in get_next_task: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error in get_next_task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

def mark_task_done(params: Dict[str, Any]): # 타입 힌트 명시
    """태스크를 완료 상태로 표시합니다."""
    try:
        if "requestId" not in params:
            raise ValueError("요청 ID가 필요합니다.")
        if "taskId" not in params:
            raise ValueError("태스크 ID가 필요합니다.")
        if "agentId" not in params:
            raise ValueError("agentId가 필요합니다.")
            
        return global_task_manager.mark_task_done(
            request_id=params["requestId"],
            task_id=params["taskId"],
            agent_id=params["agentId"],
            completed_details=params.get("completedDetails")
        )
    except Exception as e:
        logger.error(f"태스크 완료 처리 실패: {str(e)}")
        return {"success": False, "error": str(e)}

def approve_task_completion(params):
    """완료된 태스크를 승인합니다."""
    try:
        if "requestId" not in params:
            raise ValueError("요청 ID가 필요합니다.")
        if "taskId" not in params:
            raise ValueError("태스크 ID가 필요합니다.")
            
        return global_task_manager.approve_task_completion(
            request_id=params["requestId"],
            task_id=params["taskId"]
        )
    except Exception as e:
        logger.error(f"태스크 승인 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def approve_request_completion(params):
    """요청 전체의 완료를 승인합니다."""
    try:
        if "requestId" not in params:
            raise ValueError("요청 ID가 필요합니다.")
            
        return global_task_manager.approve_request_completion(
            request_id=params["requestId"]
        )
    except Exception as e:
        logger.error(f"요청 완료 승인 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def add_tasks_to_request(params):
    """기존 요청에 새 태스크를 추가합니다."""
    try:
        if "requestId" not in params:
            raise ValueError("요청 ID가 필요합니다.")
        if "tasks" not in params or not isinstance(params["tasks"], list):
            raise ValueError("유효한 태스크 목록이 필요합니다.")
            
        # 각 task가 유효한지 검증하고 필요한 경우 변환
        tasks = params["tasks"]
        validated_tasks = []
        for i, task in enumerate(tasks):
            if not isinstance(task, dict):
                # 딕셔너리가 아닌 경우 변환 시도
                try:
                    task_dict = dict(task)
                    logger.warning(f"태스크[{i}]가 딕셔너리가 아니어서 변환함: {task} -> {task_dict}")
                    task = task_dict
                except (TypeError, ValueError):
                    raise ValueError(f"태스크[{i}]를 딕셔너리로 변환할 수 없습니다: {task}")
            
            # 필수 필드 확인
            if "title" not in task:
                raise ValueError(f"태스크[{i}]에 title 필드가 없습니다: {task}")
            if "description" not in task:
                raise ValueError(f"태스크[{i}]에 description 필드가 없습니다: {task}")
                
            # 문자열 변환
            task_dict = {
                "title": str(task["title"]),
                "description": str(task["description"])
            }
            validated_tasks.append(task_dict)
            
        return global_task_manager.add_tasks_to_request(
            request_id=params["requestId"],
            tasks=validated_tasks
        )
    except Exception as e:
        logger.error(f"태스크 추가 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def update_task(params):
    """태스크 정보를 업데이트합니다."""
    try:
        if "requestId" not in params:
            raise ValueError("요청 ID가 필요합니다.")
        if "taskId" not in params:
            raise ValueError("태스크 ID가 필요합니다.")
            
        return global_task_manager.update_task(
            request_id=params["requestId"],
            task_id=params["taskId"],
            title=params.get("title"),
            description=params.get("description")
        )
    except Exception as e:
        logger.error(f"태스크 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def delete_task(params):
    """태스크를 삭제합니다."""
    try:
        if "requestId" not in params:
            raise ValueError("요청 ID가 필요합니다.")
        if "taskId" not in params:
            raise ValueError("태스크 ID가 필요합니다.")
            
        return global_task_manager.delete_task(
            request_id=params["requestId"],
            task_id=params["taskId"]
        )
    except Exception as e:
        logger.error(f"태스크 삭제 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def list_requests(params):
    """모든 요청 목록을 가져옵니다."""
    try:
        # 요청 목록 조회
        requests_data = global_task_manager.requests
        requests_list = []
        
        # 각 요청의 요약 정보 생성
        for request_id, request_info in requests_data.items():
            # 요청에 속한 태스크 정보 조회
            task_count = len(request_info.get("tasks", []))
            completed_count = 0
            
            # 완료된 태스크 수 계산
            for task_id in request_info.get("tasks", []):
                task_info = global_task_manager.tasks.get(task_id)
                if task_info.get("status") == "COMPLETED":
                    completed_count += 1
            
            # 요약 정보 추가
            request_summary = {
                "id": request_id,
                "originalRequest": request_info.get("originalRequest", ""),
                "status": request_info.get("status", "UNKNOWN"),
                "createdAt": request_info.get("createdAt", ""),
                "updatedAt": request_info.get("updatedAt", ""),
                "taskCount": task_count,
                "completedCount": completed_count,
                "progress": f"{completed_count}/{task_count}"
            }
            requests_list.append(request_summary)
        
        return {"success": True, "requests": requests_list, "count": len(requests_list)}
    except Exception as e:
        logger.error(f"요청 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def open_task_details(params: Dict[str, Any]): # 타입 힌트 명시
    """태스크 상세 정보를 가져옵니다."""
    task_id = params.get("taskId")
    if not task_id:
        raise ValueError("taskId is required.")
    
    task = db_manager.get_master_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID '{task_id}' not found.")
    return task

# clear_all_data_wrapper 함수 정의 (DB 사용하도록 수정)
def clear_all_data_wrapper(params):
    """clear_all_data MCP 도구를 위한 래퍼 함수. DB 내용을 삭제합니다."""
    try:
        confirmation = params.get("confirmation")
        required_confirmation_string = "CLEAR_ALL_MY_DATA"
        if confirmation != required_confirmation_string:
            logger.warning("데이터 초기화 확인 문자열이 일치하지 않아 작업을 취소합니다.")
            return {
                "success": False, 
                "error": f"Confirmation string mismatch. Please provide \"{required_confirmation_string}\" to confirm data deletion."
            }
        
        # DB 파일 직접 삭제 방식으로 변경 (주의!)
        # 또는 각 테이블의 모든 레코드를 삭제하는 함수를 db_manager에 만들 수 있음
        deleted_master = False
        deleted_shared = False
        if os.path.exists(db_manager.PROJECT_MASTER_DB_PATH):
            os.remove(db_manager.PROJECT_MASTER_DB_PATH)
            db_manager.init_project_master_db() # 빈 DB 파일 및 테이블 재생성
            deleted_master = True
            logger.info(f"{db_manager.PROJECT_MASTER_DB_PATH} deleted and re-initialized.")

        if os.path.exists(db_manager.AGENT_SHARED_DB_PATH):
            os.remove(db_manager.AGENT_SHARED_DB_PATH)
            db_manager.init_agent_shared_db() # 빈 DB 파일 및 테이블 재생성
            deleted_shared = True
            logger.info(f"{db_manager.AGENT_SHARED_DB_PATH} deleted and re-initialized.")

        if deleted_master or deleted_shared:
            return {"success": True, "message": "All database data has been cleared and databases re-initialized."}
        else:
            return {"success": True, "message": "No database files found to clear."}

    except Exception as e:
        logger.error(f"데이터 초기화 실패 (mcp_server - DB): {str(e)}")
        return {"success": False, "error": f"Failed to clear database data: {str(e)}"}

# 함수 매핑
TOOL_FUNCTIONS = {
    "request_planning": request_planning,
    "get_next_task": get_next_task,
    "mark_task_done": mark_task_done,
    "approve_task_completion": approve_task_completion,
    "approve_request_completion": approve_request_completion,
    "add_tasks_to_request": add_tasks_to_request,
    "update_task": update_task,
    "delete_task": delete_task,
    "list_requests": list_requests,
    "open_task_details": open_task_details,
    "clear_all_data": clear_all_data_wrapper
}

# API 엔드포인트 및 요청/응답 모델
@app.get("/tools")
async def get_tools():
    """MCP 도구 목록을 반환합니다."""
    return {"tools": TOOLS}

class ToolInvocation(BaseModel):
    name: str
    parameters: Dict[str, Any] = {}

@app.post("/invoke")
async def invoke_tool(invocation: ToolInvocation):
    """MCP 도구를 호출합니다."""
    if invocation.name not in TOOL_FUNCTIONS:
        raise HTTPException(status_code=404, detail=f"도구를 찾을 수 없음: {invocation.name}")
    
    try:
        # 파라미터 처리 로깅
        logger.info(f"도구 호출: {invocation.name}, 원본 파라미터: {invocation.parameters}")
        
        parameters = invocation.parameters
        
        # 파라미터에 tasks가 있는 경우 로깅
        if "tasks" in parameters and hasattr(parameters["tasks"], "__iter__"):
            logger.info(f"tasks 처리 중, 타입: {type(parameters['tasks'])}")
            # 각 task가 딕셔너리인지 확인하고 로깅
            for i, task in enumerate(parameters["tasks"]):
                logger.info(f"task[{i}] 타입: {type(task)}")
        
        result = TOOL_FUNCTIONS[invocation.name](parameters)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"도구 호출 실패({invocation.name}): {str(e)}")
        raise HTTPException(status_code=500, detail=f"도구 호출 실패: {str(e)}")

# JSON-RPC 응답 모델
class JsonRpcRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Union[List[Dict[str, Any]], Dict[str, Any]] = []
    id: Any

class JsonRpcResponse(BaseModel):
    jsonrpc: str
    result: Any = None
    error: Dict[str, Any] = None
    id: Any

@app.get("/")
async def root():
    """서버 상태를 확인합니다."""
    return {"status": "running", "message": "PMAgent MCP Server is running"}

@app.post("/")
async def jsonrpc_endpoint(request: Request):
    """JSON-RPC 2.0 요청을 처리합니다."""
    try:
        data = await request.json()
        logger.info(f"JSON-RPC 요청 수신: {data}")
        
        # 필수 필드 확인
        if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "잘못된 JSON-RPC 요청입니다."
                },
                "id": data.get("id")
            })
            
        if "method" not in data:
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "메소드가 지정되지 않았습니다."
                },
                "id": data.get("id")
            })
        
        method = data["method"]
        params = data.get("params", {})
        request_id = data.get("id")
        
        # params 타입 확인 및 처리
        logger.info(f"params 타입: {type(params)}")
        
        # JSON-RPC의 params가 리스트인 경우, 첫 번째 요소를 사용
        if isinstance(params, list) and len(params) > 0:
            params = params[0]
            logger.info(f"리스트 params에서 첫 번째 요소 사용: {params}")
        
        # 딕셔너리 params에 대한 로깅
        if isinstance(params, dict):
            logger.info(f"딕셔너리 params 처리: {params}")
            # tasks 키가 있고 그 값이 iterable인지 확인
            if "tasks" in params and hasattr(params["tasks"], "__iter__"):
                # 각 task가 딕셔너리인지 확인하고 로깅
                for i, task in enumerate(params["tasks"]):
                    logger.info(f"task[{i}] 타입: {type(task)}")
        else:
            logger.warning(f"params 처리 불가: {params}")
        
        # 메소드 확인
        if method not in TOOL_FUNCTIONS:
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"메서드를 찾을 수 없음: {method}"
                },
                "id": request_id
            })
        
        # 도구 호출
        logger.info(f"도구 호출: {method}, params={params}")
        result = TOOL_FUNCTIONS[method](params)
        
        # 응답 반환
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        })
    except HTTPException as e:
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "error": {
                "code": e.status_code,
                "message": str(e.detail)
            },
            "id": data.get("id") if "id" in data else None
        })
    except Exception as e:
        logger.error(f"JSON-RPC 요청 처리 실패: {str(e)}")
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"내부 오류: {str(e)}"
            },
            "id": data.get("id") if "id" in data else None
        })

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/smithery-simple.json")
async def get_smithery_simple():
    """Smithery 호환 서버 메타데이터를 반환합니다."""
    return JSONResponse(content={
        "name": "PMAgent MCP Server",
        "description": "Enable collaborative project management by integrating multiple AI agents with external tools like Unity, GitHub, and Figma through a unified MCP server. Facilitate seamless coordination among project managers, designers, developers, and AI engineers to streamline project workflows. Enhance productivity by automating interactions with diverse external resources and APIs.",
        "version": "0.1.0",
        "tools": TOOLS,  # TOOLS 변수 전체를 사용하도록 변경
        "authorization": {
            "type": "none"
        }
    })

# WebSocket 연결 관리
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket 연결 수락됨: {id(websocket)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket 연결 종료됨: {id(websocket)}")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 연결을 처리합니다."""
    await manager.connect(websocket)
    try:
        while True:
            # 메시지 수신
            data = await websocket.receive_text()
            logger.debug(f"WebSocket 메시지 수신: {data}")
            
            try:
                # JSON-RPC 요청 파싱
                request_data = json.loads(data)
                
                # 필수 필드 확인
                if "jsonrpc" not in request_data or request_data["jsonrpc"] != "2.0":
                    await websocket.send_json({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": "잘못된 JSON-RPC 요청입니다."
                        },
                        "id": request_data.get("id")
                    })
                    continue
                    
                if "method" not in request_data:
                    await websocket.send_json({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": "메소드가 지정되지 않았습니다."
                        },
                        "id": request_data.get("id")
                    })
                    continue
                
                method = request_data["method"]
                params = request_data.get("params", {})
                request_id = request_data.get("id")
                
                # params 타입 확인 및 처리
                logger.info(f"params 타입: {type(params)}")
                
                # JSON-RPC의 params가 리스트인 경우, 첫 번째 요소를 사용
                if isinstance(params, list) and len(params) > 0:
                    params = params[0]
                    logger.info(f"리스트 params에서 첫 번째 요소 사용: {params}")
                
                # 딕셔너리 params에 대한 로깅
                if isinstance(params, dict):
                    logger.info(f"딕셔너리 params 처리: {params}")
                    # tasks 키가 있고 그 값이 iterable인지 확인
                    if "tasks" in params and hasattr(params["tasks"], "__iter__"):
                        # 각 task가 딕셔너리인지 확인하고 로깅
                        for i, task in enumerate(params["tasks"]):
                            logger.info(f"task[{i}] 타입: {type(task)}")
                else:
                    logger.warning(f"params 처리 불가: {params}")
                
                # 메소드 확인
                if method not in TOOL_FUNCTIONS:
                    await websocket.send_json({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": f"메서드를 찾을 수 없음: {method}"
                        },
                        "id": request_id
                    })
                    continue
                
                # 도구 호출
                logger.info(f"도구 호출: {method}, params={params}")
                result = TOOL_FUNCTIONS[method](params)
                
                # 응답 전송
                await websocket.send_json({
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id
                })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "잘못된 JSON 형식입니다."
                    },
                    "id": None
                })
            except Exception as e:
                logger.error(f"WebSocket 요청 처리 실패: {str(e)}")
                await websocket.send_json({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"내부 오류: {str(e)}"
                    },
                    "id": request_data.get("id") if "request_data" in locals() else None
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 연결 오류: {str(e)}")
        if websocket in manager.active_connections:
            manager.disconnect(websocket)

@app.websocket("/mcp")
async def mcp_endpoint(websocket: WebSocket):
    """MCP 전용 WebSocket 연결을 처리합니다."""
    await websocket_endpoint(websocket)

def start_server(host: str = "0.0.0.0", port: int = 8082, config: Optional[Dict[str, Any]] = None) -> None:
    """
    MCP 서버 시작
    
    Args:
        host: 호스트 (기본값: "0.0.0.0")
        port: 포트 (기본값: 8082)
        config: 설정 (기본값: None)
    """
    # MCP API 생성
    mcp_api = create_mcp_api(config)
    
    # API 앱 가져오기
    api_app = mcp_api.api_app
    
    # API 앱 시작
    logger.info(f"PMAgent MCP 서버를 시작합니다 (http://{host}:{port})")
    uvicorn.run(api_app, host=host, port=port)

# 서버 실행 (uvicorn 직접 사용)
if __name__ == "__main__":
    # start_server() 함수를 사용하거나 아래처럼 직접 uvicorn.run 호출
    # start_server(host="0.0.0.0", port=8083)
    
    logger.info(f"pmagent.mcp_server 직접 실행: Uvicorn으로 FastAPI 앱 (app) 실행 준비...")
    uvicorn.run(
        "pmagent.mcp_server:app", 
        host="0.0.0.0", 
        port=8083, 
        reload=True, # 개발 중에는 reload=True가 유용
        log_level="info" # Uvicorn 자체 로그 레벨 설정
    ) 