#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="PMAgent MCP Server",
    description="프로젝트 관리를 위한 MCP(Model Context Protocol) 서버",
    version="0.1.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 환경 변수에서 설정 로드
DATA_DIR = os.environ.get("DATA_DIR", "./data")
# 데이터 디렉토리 생성
Path(DATA_DIR).mkdir(exist_ok=True, parents=True)
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.json")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")

# 데이터 모델 정의
class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str

class Task(BaseModel):
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    status: str = "TODO"
    due_date: Optional[str] = None
    assignee: Optional[str] = None
    created_at: str
    updated_at: str

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "TODO"
    due_date: Optional[str] = None
    assignee: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    assignee: Optional[str] = None

# 데이터 저장 및 로드 함수
def load_projects() -> List[Dict[str, Any]]:
    """프로젝트 데이터를 로드합니다."""
    if os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"잘못된 JSON 포맷: {PROJECTS_FILE}")
                return []
    return []

def save_projects(projects: List[Dict[str, Any]]) -> None:
    """프로젝트 데이터를 저장합니다."""
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)

def load_tasks() -> List[Dict[str, Any]]:
    """태스크 데이터를 로드합니다."""
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"잘못된 JSON 포맷: {TASKS_FILE}")
                return []
    return []

def save_tasks(tasks: List[Dict[str, Any]]) -> None:
    """태스크 데이터를 저장합니다."""
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

# MCP 도구 정의
TOOLS = [
    {
        "name": "list_projects",
        "description": "프로젝트 목록을 가져옵니다.",
        "parameters": {}
    },
    {
        "name": "create_project",
        "description": "새 프로젝트를 생성합니다.",
        "parameters": {
            "name": "프로젝트 이름",
            "description": "프로젝트 설명 (선택)"
        }
    },
    {
        "name": "get_project",
        "description": "프로젝트 정보를 가져옵니다.",
        "parameters": {
            "project_id": "프로젝트 ID"
        }
    },
    {
        "name": "update_project",
        "description": "프로젝트 정보를 업데이트합니다.",
        "parameters": {
            "project_id": "프로젝트 ID",
            "name": "새 프로젝트 이름 (선택)",
            "description": "새 프로젝트 설명 (선택)"
        }
    },
    {
        "name": "delete_project",
        "description": "프로젝트를 삭제합니다.",
        "parameters": {
            "project_id": "프로젝트 ID"
        }
    },
    {
        "name": "list_tasks",
        "description": "프로젝트의 모든 태스크 목록을 가져옵니다.",
        "parameters": {
            "project_id": "프로젝트 ID"
        }
    },
    {
        "name": "create_task",
        "description": "새 태스크를 생성합니다.",
        "parameters": {
            "project_id": "프로젝트 ID",
            "name": "태스크 이름",
            "description": "태스크 설명 (선택)",
            "status": "태스크 상태 (선택, 기본값: 'TODO')",
            "due_date": "마감일 (선택, ISO 형식)",
            "assignee": "담당자 (선택)"
        }
    },
    {
        "name": "get_task",
        "description": "태스크 정보를 가져옵니다.",
        "parameters": {
            "project_id": "프로젝트 ID",
            "task_id": "태스크 ID"
        }
    },
    {
        "name": "update_task",
        "description": "태스크 정보를 업데이트합니다.",
        "parameters": {
            "project_id": "프로젝트 ID",
            "task_id": "태스크 ID",
            "name": "새 태스크 이름 (선택)",
            "description": "새 태스크 설명 (선택)",
            "status": "새 태스크 상태 (선택)",
            "due_date": "새 마감일 (선택, ISO 형식)",
            "assignee": "새 담당자 (선택)"
        }
    },
    {
        "name": "delete_task",
        "description": "태스크를 삭제합니다.",
        "parameters": {
            "project_id": "프로젝트 ID",
            "task_id": "태스크 ID"
        }
    }
]

# MCP 도구 구현 함수
def list_projects(params):
    """모든 프로젝트 목록을 가져옵니다."""
    projects = load_projects()
    return {"projects": projects}

def create_project(params):
    """새 프로젝트를 생성합니다."""
    if "name" not in params:
        raise HTTPException(status_code=400, detail="프로젝트 이름이 필요합니다.")
    
    projects = load_projects()
    
    now = datetime.now().isoformat()
    new_project = {
        "id": str(uuid.uuid4()),
        "name": params["name"],
        "description": params.get("description", ""),
        "created_at": now,
        "updated_at": now
    }
    
    projects.append(new_project)
    save_projects(projects)
    
    return {"project": new_project}

def get_project(params):
    """프로젝트 정보를 가져옵니다."""
    if "project_id" not in params:
        raise HTTPException(status_code=400, detail="프로젝트 ID가 필요합니다.")
    
    project_id = params["project_id"]
    projects = load_projects()
    
    for project in projects:
        if project["id"] == project_id:
            return {"project": project}
    
    raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

def update_project(params):
    """프로젝트 정보를 업데이트합니다."""
    if "project_id" not in params:
        raise HTTPException(status_code=400, detail="프로젝트 ID가 필요합니다.")
    
    project_id = params["project_id"]
    projects = load_projects()
    
    for i, project in enumerate(projects):
        if project["id"] == project_id:
            if "name" in params:
                project["name"] = params["name"]
            if "description" in params:
                project["description"] = params["description"]
            
            project["updated_at"] = datetime.now().isoformat()
            projects[i] = project
            save_projects(projects)
            
            return {"project": project}
    
    raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")

def delete_project(params):
    """프로젝트를 삭제합니다."""
    if "project_id" not in params:
        raise HTTPException(status_code=400, detail="프로젝트 ID가 필요합니다.")
    
    project_id = params["project_id"]
    projects = load_projects()
    tasks = load_tasks()
    
    # 프로젝트의 모든 태스크도 삭제
    tasks = [task for task in tasks if task["project_id"] != project_id]
    save_tasks(tasks)
    
    # 프로젝트 삭제
    projects = [project for project in projects if project["id"] != project_id]
    save_projects(projects)
    
    return {"success": True}

def list_tasks(params):
    """프로젝트의 모든 태스크 목록을 가져옵니다."""
    if "project_id" not in params:
        raise HTTPException(status_code=400, detail="프로젝트 ID가 필요합니다.")
    
    project_id = params["project_id"]
    tasks = load_tasks()
    
    project_tasks = [task for task in tasks if task["project_id"] == project_id]
    return {"tasks": project_tasks}

def create_task(params):
    """새 태스크를 생성합니다."""
    if "project_id" not in params:
        raise HTTPException(status_code=400, detail="프로젝트 ID가 필요합니다.")
    if "name" not in params:
        raise HTTPException(status_code=400, detail="태스크 이름이 필요합니다.")
    
    project_id = params["project_id"]
    
    # 프로젝트 존재 확인
    projects = load_projects()
    project_exists = any(project["id"] == project_id for project in projects)
    
    if not project_exists:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")
    
    tasks = load_tasks()
    
    now = datetime.now().isoformat()
    new_task = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "name": params["name"],
        "description": params.get("description", ""),
        "status": params.get("status", "TODO"),
        "due_date": params.get("due_date"),
        "assignee": params.get("assignee"),
        "created_at": now,
        "updated_at": now
    }
    
    tasks.append(new_task)
    save_tasks(tasks)
    
    return {"task": new_task}

def get_task(params):
    """태스크 정보를 가져옵니다."""
    if "project_id" not in params or "task_id" not in params:
        raise HTTPException(status_code=400, detail="프로젝트 ID와 태스크 ID가 필요합니다.")
    
    project_id = params["project_id"]
    task_id = params["task_id"]
    tasks = load_tasks()
    
    for task in tasks:
        if task["id"] == task_id and task["project_id"] == project_id:
            return {"task": task}
    
    raise HTTPException(status_code=404, detail=f"태스크를 찾을 수 없습니다: {task_id}")

def update_task(params):
    """태스크 정보를 업데이트합니다."""
    if "project_id" not in params or "task_id" not in params:
        raise HTTPException(status_code=400, detail="프로젝트 ID와 태스크 ID가 필요합니다.")
    
    project_id = params["project_id"]
    task_id = params["task_id"]
    tasks = load_tasks()
    
    for i, task in enumerate(tasks):
        if task["id"] == task_id and task["project_id"] == project_id:
            if "name" in params:
                task["name"] = params["name"]
            if "description" in params:
                task["description"] = params["description"]
            if "status" in params:
                task["status"] = params["status"]
            if "due_date" in params:
                task["due_date"] = params["due_date"]
            if "assignee" in params:
                task["assignee"] = params["assignee"]
            
            task["updated_at"] = datetime.now().isoformat()
            tasks[i] = task
            save_tasks(tasks)
            
            return {"task": task}
    
    raise HTTPException(status_code=404, detail=f"태스크를 찾을 수 없습니다: {task_id}")

def delete_task(params):
    """태스크를 삭제합니다."""
    if "project_id" not in params or "task_id" not in params:
        raise HTTPException(status_code=400, detail="프로젝트 ID와 태스크 ID가 필요합니다.")
    
    project_id = params["project_id"]
    task_id = params["task_id"]
    tasks = load_tasks()
    
    tasks = [task for task in tasks if not (task["id"] == task_id and task["project_id"] == project_id)]
    save_tasks(tasks)
    
    return {"success": True}

# 도구 이름과 해당 함수의 매핑
TOOL_FUNCTIONS = {
    "list_projects": list_projects,
    "create_project": create_project,
    "get_project": get_project,
    "update_project": update_project,
    "delete_project": delete_project,
    "list_tasks": list_tasks,
    "create_task": create_task,
    "get_task": get_task,
    "update_task": update_task,
    "delete_task": delete_task
}

# MCP 엔드포인트
@app.get("/tools")
async def get_tools():
    """사용 가능한 도구 목록을 반환합니다."""
    return {"tools": TOOLS}

class ToolInvocation(BaseModel):
    name: str
    parameters: Dict[str, Any] = {}

@app.post("/invoke")
async def invoke_tool(invocation: ToolInvocation):
    """도구를 호출합니다."""
    if invocation.name not in TOOL_FUNCTIONS:
        raise HTTPException(status_code=404, detail=f"도구를 찾을 수 없습니다: {invocation.name}")
    
    try:
        result = TOOL_FUNCTIONS[invocation.name](invocation.parameters)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"도구 호출 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"도구 호출 중 오류 발생: {str(e)}")

# 기본 엔드포인트
@app.get("/")
async def root():
    """API 루트 엔드포인트."""
    return {
        "name": "PMAgent MCP Server",
        "version": "0.1.0",
        "description": "프로젝트 관리를 위한 MCP(Model Context Protocol) 서버"
    }

@app.post("/")
async def jsonrpc_endpoint(request: Request):
    data = await request.json()
    
    if data.get("method") == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": {
                "name": "pmagent-mcp-server",
                "version": "0.1.0",
                "tools": TOOLS
            }
        }
    
    if data.get("method") == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": {"tools": TOOLS}
        }
    
    if data.get("method") == "tools/invoke":
        params = data.get("params", {})
        tool_name = params.get("name")
        tool_params = params.get("parameters", {})
        
        if tool_name in TOOL_FUNCTIONS:
            try:
                result = TOOL_FUNCTIONS[tool_name](tool_params)
                return {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": result
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "error": {"message": str(e)}
                }
    
    return {
        "jsonrpc": "2.0",
        "id": data.get("id"),
        "error": {"message": "Method not found"}
    }

def main():
    """서버 실행 함수"""
    host = os.environ.get("SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("SERVER_PORT", 8080))
    
    logger.info(f"PMAgent MCP 서버 시작: http://{host}:{port}")
    
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main() 