#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

# MCP 도구 관련 모듈 가져오기
from .task_manager import task_manager

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
            "requestId": "요청 ID"
        }
    },
    {
        "name": "mark_task_done",
        "description": "태스크를 완료 상태로 표시합니다.",
        "parameters": {
            "requestId": "요청 ID",
            "taskId": "태스크 ID",
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
    }
]

# MCP 도구 구현 함수
def request_planning(params):
    """새 요청을 등록하고 태스크를 계획합니다."""
    try:
        logger.info(f"request_planning 호출됨: params={params}")
        logger.info(f"params 타입: {type(params)}")
        
        if "originalRequest" not in params:
            raise ValueError("원본 요청 내용이 필요합니다.")
        if "tasks" not in params:
            raise ValueError("태스크 목록이 필요합니다.")
            
        # params["tasks"] 값을 확인하고 list 타입으로 확실하게 처리
        tasks = params["tasks"]
        if not isinstance(tasks, list):
            raise ValueError(f"태스크 목록은 배열이어야 합니다. 현재 타입: {type(tasks)}")
            
        logger.info(f"태스크 목록: {tasks}")
        
        # 각 task가 유효한지 검증하고 필요한 경우 변환
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
            
        return task_manager.request_planning(
            original_request=params["originalRequest"],
            tasks=validated_tasks,
            split_details=params.get("splitDetails")
        )
    except Exception as e:
        logger.error(f"요청 계획 생성 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def get_next_task(params):
    """다음 대기 중인 태스크를 가져옵니다."""
    try:
        if "requestId" not in params:
            raise ValueError("요청 ID가 필요합니다.")
            
        return task_manager.get_next_task(request_id=params["requestId"])
    except Exception as e:
        logger.error(f"다음 태스크 조회 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def mark_task_done(params):
    """태스크를 완료 상태로 표시합니다."""
    try:
        if "requestId" not in params:
            raise ValueError("요청 ID가 필요합니다.")
        if "taskId" not in params:
            raise ValueError("태스크 ID가 필요합니다.")
            
        return task_manager.mark_task_done(
            request_id=params["requestId"],
            task_id=params["taskId"],
            completed_details=params.get("completedDetails")
        )
    except Exception as e:
        logger.error(f"태스크 완료 처리 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def approve_task_completion(params):
    """완료된 태스크를 승인합니다."""
    try:
        if "requestId" not in params:
            raise ValueError("요청 ID가 필요합니다.")
        if "taskId" not in params:
            raise ValueError("태스크 ID가 필요합니다.")
            
        return task_manager.approve_task_completion(
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
            
        return task_manager.approve_request_completion(
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
            
        return task_manager.add_tasks_to_request(
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
            
        return task_manager.update_task(
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
            
        return task_manager.delete_task(
            request_id=params["requestId"],
            task_id=params["taskId"]
        )
    except Exception as e:
        logger.error(f"태스크 삭제 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def list_requests(params):
    """모든 요청 목록을 가져옵니다."""
    try:
        return task_manager.list_requests()
    except Exception as e:
        logger.error(f"요청 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

def open_task_details(params):
    """태스크 상세 정보를 가져옵니다."""
    try:
        if "taskId" not in params:
            raise ValueError("태스크 ID가 필요합니다.")
            
        return task_manager.open_task_details(task_id=params["taskId"])
    except Exception as e:
        logger.error(f"태스크 상세 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

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
    "open_task_details": open_task_details
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

@app.get("/smithery-simple.json")
async def get_smithery_simple():
    """Smithery 호환 서버 메타데이터를 반환합니다."""
    return JSONResponse(content={
        "name": "PMAgent MCP Server",
        "description": "프로젝트 관리를 위한 MCP(Model Context Protocol) 서버",
        "version": "0.1.0",
        "tools": [tool["name"] for tool in TOOLS],
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

def start_server(host: str = "0.0.0.0", port: int = 8082):
    """서버를 시작합니다."""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server() 