#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent MCP 서버

프로젝트 관리 기능을 제공하는 MCP(Model Context Protocol) 서버입니다.
"""

import os
import uuid
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="PMAgent MCP Server")

# 메모리 스토리지 (실제 구현에서는 데이터베이스를 사용할 수 있습니다)
projects = {}
tasks = {}

# 모델 정의
class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: str

class Task(BaseModel):
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    status: str = "TODO"
    due_date: Optional[str] = None
    assignee: Optional[str] = None
    created_at: str

class ToolCall(BaseModel):
    name: str
    parameters: Dict[str, Any]

# 도구 정의
tools = [
    {
        "name": "list_projects",
        "description": "모든 프로젝트 목록을 가져옵니다.",
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

# 도구 처리 함수
def list_projects(params):
    return {"projects": list(projects.values())}

def create_project(params):
    name = params.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="프로젝트 이름은 필수 항목입니다.")
    
    project_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    
    project = {
        "id": project_id,
        "name": name,
        "description": params.get("description", ""),
        "created_at": created_at
    }
    
    projects[project_id] = project
    return {"project": project}

def get_project(params):
    project_id = params.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="프로젝트 ID는 필수 항목입니다.")
    
    project = projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")
    
    return {"project": project}

def update_project(params):
    project_id = params.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="프로젝트 ID는 필수 항목입니다.")
    
    project = projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")
    
    if "name" in params:
        project["name"] = params["name"]
    if "description" in params:
        project["description"] = params["description"]
    
    return {"project": project}

def delete_project(params):
    project_id = params.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="프로젝트 ID는 필수 항목입니다.")
    
    if project_id not in projects:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")
    
    # 프로젝트 관련 태스크 삭제
    project_tasks = [t for t in tasks.values() if t["project_id"] == project_id]
    for task in project_tasks:
        del tasks[task["id"]]
    
    # 프로젝트 삭제
    del projects[project_id]
    
    return {"success": True}

def list_tasks(params):
    project_id = params.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="프로젝트 ID는 필수 항목입니다.")
    
    if project_id not in projects:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")
    
    project_tasks = [t for t in tasks.values() if t["project_id"] == project_id]
    return {"tasks": project_tasks}

def create_task(params):
    project_id = params.get("project_id")
    name = params.get("name")
    
    if not project_id:
        raise HTTPException(status_code=400, detail="프로젝트 ID는 필수 항목입니다.")
    if not name:
        raise HTTPException(status_code=400, detail="태스크 이름은 필수 항목입니다.")
    
    if project_id not in projects:
        raise HTTPException(status_code=404, detail=f"프로젝트를 찾을 수 없습니다: {project_id}")
    
    task_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    
    task = {
        "id": task_id,
        "project_id": project_id,
        "name": name,
        "description": params.get("description", ""),
        "status": params.get("status", "TODO"),
        "due_date": params.get("due_date"),
        "assignee": params.get("assignee"),
        "created_at": created_at
    }
    
    tasks[task_id] = task
    return {"task": task}

def get_task(params):
    project_id = params.get("project_id")
    task_id = params.get("task_id")
    
    if not project_id:
        raise HTTPException(status_code=400, detail="프로젝트 ID는 필수 항목입니다.")
    if not task_id:
        raise HTTPException(status_code=400, detail="태스크 ID는 필수 항목입니다.")
    
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"태스크를 찾을 수 없습니다: {task_id}")
    
    if task["project_id"] != project_id:
        raise HTTPException(status_code=400, detail="태스크가 지정된 프로젝트에 속하지 않습니다.")
    
    return {"task": task}

def update_task(params):
    project_id = params.get("project_id")
    task_id = params.get("task_id")
    
    if not project_id:
        raise HTTPException(status_code=400, detail="프로젝트 ID는 필수 항목입니다.")
    if not task_id:
        raise HTTPException(status_code=400, detail="태스크 ID는 필수 항목입니다.")
    
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"태스크를 찾을 수 없습니다: {task_id}")
    
    if task["project_id"] != project_id:
        raise HTTPException(status_code=400, detail="태스크가 지정된 프로젝트에 속하지 않습니다.")
    
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
    
    return {"task": task}

def delete_task(params):
    project_id = params.get("project_id")
    task_id = params.get("task_id")
    
    if not project_id:
        raise HTTPException(status_code=400, detail="프로젝트 ID는 필수 항목입니다.")
    if not task_id:
        raise HTTPException(status_code=400, detail="태스크 ID는 필수 항목입니다.")
    
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"태스크를 찾을 수 없습니다: {task_id}")
    
    if task["project_id"] != project_id:
        raise HTTPException(status_code=400, detail="태스크가 지정된 프로젝트에 속하지 않습니다.")
    
    del tasks[task_id]
    return {"success": True}

# 도구 매핑
tool_handlers = {
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

# 라우트 정의
@app.get("/")
async def root():
    return {"message": "PMAgent MCP 서버에 오신 것을 환영합니다!"}

@app.get("/tools")
async def get_tools():
    return {"tools": tools}

@app.post("/invoke")
async def invoke_tool(tool_call: ToolCall):
    logger.info(f"도구 호출: {tool_call.name}")
    
    if tool_call.name not in tool_handlers:
        raise HTTPException(status_code=400, detail=f"존재하지 않는 도구: {tool_call.name}")
    
    try:
        handler = tool_handlers[tool_call.name]
        result = handler(tool_call.parameters)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"도구 실행 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"도구 실행 오류: {str(e)}")

# 서버 실행
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"PMAgent MCP 서버를 http://localhost:{port} 에서 시작합니다.")
    uvicorn.run(app, host="0.0.0.0", port=port) 