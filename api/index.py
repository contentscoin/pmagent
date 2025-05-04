from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import logging
import json
import traceback
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error") # Vercel에서 FastAPI 로그를 보려면 uvicorn 로거 사용

app = FastAPI()

# 임시 데이터 저장소 (실제 구현에서는 데이터베이스로 대체됨)
projects = {}
tasks = {}
requests = {}
sessions = {}
agents = {}
design_systems = {}  # 디자인 시스템 저장소 추가
external_tool_requests = {}  # 외부 디자인 툴 연동 요청 저장소

# 외부 디자인 툴 유형 상수
EXTERNAL_TOOL_TYPES = {
    "FIGMA": "figma",
    "TWENTY_FIRST": "21st.dev",
    "SKETCH": "sketch",
    "ADOBE_XD": "adobe_xd",
    "ZEPLIN": "zeplin"
}

# 디자인 에이전트 작업 유형 상수
DESIGN_TASK_TYPES = {
    "GENERATE_COMPONENT": "generate_component",
    "GENERATE_SCREEN": "generate_screen",
    "GENERATE_THEME": "generate_theme",
    "REVIEW_DESIGN": "review_design",
    "CREATE_DESIGN_SYSTEM": "create_design_system",
    "UPDATE_DESIGN_SYSTEM": "update_design_system",
    "EXTERNAL_TOOL_DESIGN": "external_tool_design"  # 외부 툴 작업 유형 추가
}

# 기본 디자인 시스템 초기화
default_design_system = {
    "id": "default",
    "name": "기본 디자인 시스템",
    "colors": {
        "primary": "#3A86FF",
        "secondary": "#8338EC",
        "accent": "#FF006E",
        "success": "#06D6A0",
        "warning": "#FFD166",
        "error": "#EF476F",
        "background": "#F8F9FA",
        "surface": "#FFFFFF",
        "text": {
            "primary": "#212529",
            "secondary": "#6C757D",
            "disabled": "#ADB5BD"
        }
    },
    "typography": {
        "heading1": {"fontSize": 32, "fontWeight": "bold", "lineHeight": 1.2},
        "heading2": {"fontSize": 24, "fontWeight": "bold", "lineHeight": 1.3},
        "heading3": {"fontSize": 20, "fontWeight": "semibold", "lineHeight": 1.4},
        "body1": {"fontSize": 16, "fontWeight": "normal", "lineHeight": 1.5},
        "body2": {"fontSize": 14, "fontWeight": "normal", "lineHeight": 1.5},
        "caption": {"fontSize": 12, "fontWeight": "normal", "lineHeight": 1.4},
        "button": {"fontSize": 16, "fontWeight": "medium", "lineHeight": 1.4}
    },
    "spacing": {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 32,
        "xxl": 48
    },
    "borderRadius": {
        "small": 4,
        "medium": 8,
        "large": 16,
        "pill": 999
    },
    "shadows": {
        "small": "0 2px 4px rgba(0,0,0,0.1)",
        "medium": "0 4px 6px rgba(0,0,0,0.12)",
        "large": "0 10px 15px rgba(0,0,0,0.15)"
    }
}

design_systems["default"] = default_design_system

@app.get("/")
async def root():
    logger.info("루트 경로 요청 받음")
    return {"message": "PM Agent MCP Server is running!"}

# GET과 POST 요청 모두 처리할 수 있도록 수정
@app.api_route("/api", methods=["GET", "POST"])
async def api_endpoint(request: Request):
    request_id = None # id 초기화
    try:
        logger.info(f"API 요청 받음 - 메서드: {request.method}")
        
        # GET 요청 처리
        if request.method == "GET":
            logger.info("GET 요청에 대한 기본 응답 생성")
            response_data = {
                "jsonrpc": "2.0",
                "result": {
                    "name": "pmagent",
                    "version": "0.1.0",
                    "description": "PM Agent MCP Server (Test Description)",
                    "message": "이 엔드포인트는 JSON-RPC 형식의 POST 요청을 처리합니다."
                },
                "id": None
            }
            return JSONResponse(content=response_data)
        
        # POST 요청 처리
        data = await request.json()
        request_id = data.get("id")
        method = data.get("method", "")
        params = data.get("params", [])
        logger.info(f"요청된 메서드: {method}")
        
        # rpc.discover 메서드 처리
        if method == "rpc.discover":
            logger.info("rpc.discover 처리 중")
            response_data = {
                "jsonrpc": "2.0",
                "result": {
                    "name": "pmagent",
                    "version": "0.1.0",
                    "description": "PM Agent MCP Server (Test Description)",
                    "methods": [
                        {
                            "name": "test_method",
                            "description": "A simple test method.",
                            "parameters": {}
                        },
                        {
                            "name": "request_planning",
                            "description": "Register a new user request and plan its associated tasks.",
                            "parameters": {
                                "originalRequest": {"type": "string"},
                                "tasks": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "description": {"type": "string"}
                                        }
                                    }
                                },
                                "splitDetails": {"type": "string", "optional": True}
                            }
                        },
                        {
                            "name": "get_next_task",
                            "description": "Get the next pending task for a request.",
                            "parameters": {
                                "requestId": {"type": "string"}
                            }
                        },
                        {
                            "name": "mark_task_done",
                            "description": "Mark a task as completed.",
                            "parameters": {
                                "requestId": {"type": "string"},
                                "taskId": {"type": "string"},
                                "completedDetails": {"type": "string", "optional": True}
                            }
                        },
                        {
                            "name": "approve_task_completion",
                            "description": "Approve a completed task.",
                            "parameters": {
                                "requestId": {"type": "string"},
                                "taskId": {"type": "string"}
                            }
                        },
                        {
                            "name": "approve_request_completion",
                            "description": "Approve the entire request completion.",
                            "parameters": {
                                "requestId": {"type": "string"}
                            }
                        },
                        {
                            "name": "create_session",
                            "description": "Create a new session with a unique ID.",
                            "parameters": {}
                        },
                        {
                            "name": "export_data",
                            "description": "Export all session data for client-side storage.",
                            "parameters": {
                                "sessionId": {"type": "string", "optional": True}
                            }
                        },
                        {
                            "name": "import_data",
                            "description": "Import previously exported data to restore a session.",
                            "parameters": {
                                "data": {"type": "object"},
                                "sessionId": {"type": "string", "optional": True}
                            }
                        },
                        {
                            "name": "create_agent",
                            "description": "Create a new agent of specified type.",
                            "parameters": {
                                "type": {"type": "string", "enum": ["pm", "designer", "frontend", "backend", "ai_engineer"]},
                                "name": {"type": "string"},
                                "config": {"type": "object", "optional": True}
                            }
                        },
                        {
                            "name": "get_agent",
                            "description": "Get information about an agent.",
                            "parameters": {
                                "agentId": {"type": "string"}
                            }
                        },
                        {
                            "name": "list_agents",
                            "description": "List all available agents.",
                            "parameters": {
                                "type": {"type": "string", "optional": True}
                            }
                        },
                        {
                            "name": "assign_task_to_agent",
                            "description": "Assign a task to a specific agent.",
                            "parameters": {
                                "agentId": {"type": "string"},
                                "task": {"type": "object"},
                                "priority": {"type": "string", "enum": ["low", "medium", "high"], "optional": True}
                            }
                        },
                        {
                            "name": "get_agent_result",
                            "description": "Get the result of an agent's task.",
                            "parameters": {
                                "agentId": {"type": "string"},
                                "taskId": {"type": "string"}
                            }
                        },
                        {
                            "name": "request_external_tool_permission",
                            "description": "디자이너 에이전트가 외부 디자인 툴 사용 권한을 요청합니다.",
                            "parameters": {
                                "agentId": {"type": "string"},
                                "toolType": {"type": "string", "enum": ["figma", "21st.dev", "sketch", "adobe_xd", "zeplin"]},
                                "taskDescription": {"type": "string"},
                                "projectContext": {"type": "object", "optional": True}
                            }
                        },
                        {
                            "name": "approve_external_tool_request",
                            "description": "사용자/PM이 외부 디자인 툴 사용 요청을 승인합니다.",
                            "parameters": {
                                "requestId": {"type": "string"},
                                "approved": {"type": "boolean"},
                                "credentials": {"type": "object", "optional": True}
                            }
                        },
                        {
                            "name": "get_external_tool_status",
                            "description": "외부 디자인 툴 요청 상태를 조회합니다.",
                            "parameters": {
                                "requestId": {"type": "string"}
                            }
                        },
                        {
                            "name": "submit_external_design_result",
                            "description": "외부 디자인 툴에서 작업한 결과를 제출합니다.",
                            "parameters": {
                                "requestId": {"type": "string"},
                                "designData": {"type": "object"},
                                "designUrls": {"type": "array", "items": {"type": "string"}, "optional": True}
                            }
                        }
                    ]
                },
                "id": request_id
            }
            logger.info("rpc.discover 응답 생성 완료")
            return JSONResponse(content=response_data)
        
        # 프로젝트 관리 메서드들 처리
        elif method == "request_planning":
            return await handle_request_planning(params, request_id)
        elif method == "get_next_task":
            return await handle_get_next_task(params, request_id)
        elif method == "mark_task_done":
            return await handle_mark_task_done(params, request_id)
        elif method == "approve_task_completion":
            return await handle_approve_task_completion(params, request_id)
        elif method == "approve_request_completion":
            return await handle_approve_request_completion(params, request_id)
        
        # 세션 및 데이터 관리 메서드 처리
        elif method == "create_session":
            return await handle_create_session(params, request_id)
        elif method == "export_data":
            return await handle_export_data(params, request_id)
        elif method == "import_data":
            return await handle_import_data(params, request_id)
            
        # 에이전트 관련 메서드 처리
        elif method == "create_agent":
            return await handle_create_agent(params, request_id)
        elif method == "get_agent":
            return await handle_get_agent(params, request_id)
        elif method == "list_agents":
            return await handle_list_agents(params, request_id)
        elif method == "assign_task_to_agent":
            return await handle_assign_task_to_agent(params, request_id)
        elif method == "get_agent_result":
            return await handle_get_agent_result(params, request_id)
        
        # 디자인 시스템 관련 메서드 처리
        elif method == "create_design_system":
            return await handle_create_design_system(params, request_id)
        elif method == "update_design_system":
            return await handle_update_design_system(params, request_id)
        elif method == "get_design_system":
            return await handle_get_design_system(params, request_id)
        elif method == "list_design_systems":
            return await handle_list_design_systems(params, request_id)
        
        # 외부 디자인 툴 연동 관련 메서드 처리
        elif method == "request_external_tool_permission":
            return await handle_request_external_tool_permission(params, request_id)
        elif method == "approve_external_tool_request":
            return await handle_approve_external_tool_request(params, request_id)
        elif method == "get_external_tool_status":
            return await handle_get_external_tool_status(params, request_id)
        elif method == "submit_external_design_result":
            return await handle_submit_external_design_result(params, request_id)
        
        # 기본 응답
        logger.warning(f"알 수 없는 메서드 호출: {method}")
        response_data = {
            "jsonrpc": "2.0",
            "result": {
                "message": "Method not implemented",
                "method": method
            },
            "id": request_id
        }
        return JSONResponse(content=response_data)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 디코드 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Invalid JSON format"},
                "id": request_id
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"내부 서버 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal server error: {str(e)}"
                },
                "id": request_id
            },
            status_code=500
        )

# 각 메서드 핸들러 구현
async def handle_request_planning(params, request_id):
    try:
        original_request = params[0].get("originalRequest", "")
        tasks_data = params[0].get("tasks", [])
        split_details = params[0].get("splitDetails", "")
        
        # 새 요청 생성
        request_id_str = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        tasks_list = []
        for task_data in tasks_data:
            task_id = str(uuid.uuid4())
            task = {
                "id": task_id,
                "title": task_data.get("title", ""),
                "description": task_data.get("description", ""),
                "status": "pending",
                "created_at": now,
                "completed_at": None,
                "approved_at": None
            }
            tasks_list.append(task)
            tasks[task_id] = task
        
        new_request = {
            "id": request_id_str,
            "original_request": original_request,
            "split_details": split_details,
            "tasks": tasks_list,
            "status": "in_progress",
            "created_at": now,
            "completed_at": None
        }
        
        requests[request_id_str] = new_request
        
        # 응답 생성
        response = {
            "jsonrpc": "2.0",
            "result": {
                "requestId": request_id_str,
                "message": "Request registered successfully",
                "tasksCreated": len(tasks_list),
                "progressTable": generate_progress_table(request_id_str)
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"request_planning 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in request_planning: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_get_next_task(params, request_id):
    try:
        request_id_str = params[0].get("requestId", "")
        
        if request_id_str not in requests:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Request not found"},
                    "id": request_id
                },
                status_code=404
            )
        
        user_request = requests[request_id_str]
        next_task = None
        
        # 다음 보류 중인 작업 찾기
        for task in user_request["tasks"]:
            if task["status"] == "pending":
                next_task = task
                break
        
        # 모든 작업이 완료되었는지 확인
        all_tasks_done = all(task["status"] in ["completed", "approved"] for task in user_request["tasks"])
        
        response = {
            "jsonrpc": "2.0",
            "result": {
                "requestId": request_id_str,
                "progressTable": generate_progress_table(request_id_str),
                "allTasksDone": all_tasks_done
            },
            "id": request_id
        }
        
        if all_tasks_done:
            response["result"]["message"] = "All tasks are completed. Awaiting request completion approval."
        elif next_task:
            response["result"]["nextTask"] = {
                "taskId": next_task["id"],
                "title": next_task["title"],
                "description": next_task["description"]
            }
        else:
            response["result"]["message"] = "No pending tasks found. Some tasks may be waiting for approval."
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"get_next_task 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in get_next_task: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_mark_task_done(params, request_id):
    try:
        request_id_str = params[0].get("requestId", "")
        task_id = params[0].get("taskId", "")
        completed_details = params[0].get("completedDetails", "")
        
        if request_id_str not in requests:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Request not found"},
                    "id": request_id
                },
                status_code=404
            )
        
        task_found = False
        for task in requests[request_id_str]["tasks"]:
            if task["id"] == task_id:
                if task["status"] != "pending":
                    return JSONResponse(
                        content={
                            "jsonrpc": "2.0",
                            "error": {"code": -32000, "message": f"Task is already {task['status']}"},
                            "id": request_id
                        },
                        status_code=400
                    )
                
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                if task_id in tasks:
                    tasks[task_id]["status"] = "completed"
                    tasks[task_id]["completed_at"] = task["completed_at"]
                
                task_found = True
                break
        
        if not task_found:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Task not found in the request"},
                    "id": request_id
                },
                status_code=404
            )
        
        response = {
            "jsonrpc": "2.0",
            "result": {
                "requestId": request_id_str,
                "taskId": task_id,
                "message": "Task marked as done",
                "progressTable": generate_progress_table(request_id_str)
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"mark_task_done 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in mark_task_done: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_approve_task_completion(params, request_id):
    try:
        request_id_str = params[0].get("requestId", "")
        task_id = params[0].get("taskId", "")
        
        if request_id_str not in requests:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Request not found"},
                    "id": request_id
                },
                status_code=404
            )
        
        task_found = False
        for task in requests[request_id_str]["tasks"]:
            if task["id"] == task_id:
                if task["status"] != "completed":
                    return JSONResponse(
                        content={
                            "jsonrpc": "2.0",
                            "error": {"code": -32000, "message": "Task must be completed first"},
                            "id": request_id
                        },
                        status_code=400
                    )
                
                task["status"] = "approved"
                task["approved_at"] = datetime.now().isoformat()
                if task_id in tasks:
                    tasks[task_id]["status"] = "approved"
                    tasks[task_id]["approved_at"] = task["approved_at"]
                
                task_found = True
                break
        
        if not task_found:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Task not found in the request"},
                    "id": request_id
                },
                status_code=404
            )
        
        response = {
            "jsonrpc": "2.0",
            "result": {
                "requestId": request_id_str,
                "taskId": task_id,
                "message": "Task completion approved",
                "progressTable": generate_progress_table(request_id_str)
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"approve_task_completion 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in approve_task_completion: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_approve_request_completion(params, request_id):
    try:
        request_id_str = params[0].get("requestId", "")
        
        if request_id_str not in requests:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Request not found"},
                    "id": request_id
                },
                status_code=404
            )
        
        user_request = requests[request_id_str]
        
        # 모든 작업이 승인되었는지 확인
        all_approved = all(task["status"] == "approved" for task in user_request["tasks"])
        
        if not all_approved:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "All tasks must be approved first"},
                    "id": request_id
                },
                status_code=400
            )
        
        user_request["status"] = "completed"
        user_request["completed_at"] = datetime.now().isoformat()
        
        response = {
            "jsonrpc": "2.0",
            "result": {
                "requestId": request_id_str,
                "message": "Request completion approved",
                "progressTable": generate_progress_table(request_id_str)
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"approve_request_completion 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in approve_request_completion: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

# 세션 및 데이터 관리 메서드 구현
async def handle_create_session(params, request_id):
    try:
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # 가벼운 세션 정보만 서버에 보관
        sessions[session_id] = {
            "created_at": now,
            "last_activity": now
        }
        
        response = {
            "jsonrpc": "2.0",
            "result": {
                "sessionId": session_id,
                "message": "Session created successfully"
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"create_session 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in create_session: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_export_data(params, request_id):
    try:
        session_id = params[0].get("sessionId", None) if params else None
        
        # 세션 ID가 제공되었으면 확인
        if session_id and session_id not in sessions:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Session not found"},
                    "id": request_id
                },
                status_code=404
            )
        
        # 세션 ID가 유효하면 해당 세션의 마지막 활동 시간 업데이트
        if session_id:
            sessions[session_id]["last_activity"] = datetime.now().isoformat()
        
        # 현재 세션의 모든 데이터를 구조화된 형태로 반환
        exported_data = {
            "projects": projects,
            "tasks": tasks,
            "requests": requests,
            "agents": agents,
            "export_time": datetime.now().isoformat(),
            "session_id": session_id
        }
        
        # 파일 시스템에 데이터 저장 (비동기 처리)
        from api.data_persistence import save_data_to_file
        if session_id:
            try:
                file_path = await save_data_to_file(session_id, exported_data)
                exported_data["saved_file_path"] = file_path
            except Exception as e:
                logger.warning(f"데이터 파일 저장 실패, 인메모리 데이터만 반환합니다: {str(e)}")
        
        response = {
            "jsonrpc": "2.0",
            "result": {
                "data": exported_data,
                "message": "Data exported successfully"
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"export_data 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in export_data: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_import_data(params, request_id):
    try:
        imported_data = params[0].get("data", {})
        session_id = params[0].get("sessionId", None)
        from_file = params[0].get("fromFile", False)
        
        # 파일에서 데이터 불러오기
        if from_file and session_id:
            from api.data_persistence import load_data_from_file
            file_data = await load_data_from_file(session_id)
            if file_data:
                imported_data = file_data
                logger.info(f"파일에서 세션 데이터를 불러왔습니다: {session_id}")
            else:
                logger.warning(f"파일에서 세션 데이터를 불러오지 못했습니다: {session_id}")
        
        # 세션 ID가 제공되었으면 확인
        if session_id and session_id not in sessions:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Session not found"},
                    "id": request_id
                },
                status_code=404
            )
        
        # 기본적인 데이터 구조 확인
        required_keys = ["projects", "tasks", "requests"]
        missing_keys = [key for key in required_keys if key not in imported_data]
        
        if missing_keys:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000, 
                        "message": f"Invalid data format. Missing keys: {', '.join(missing_keys)}"
                    },
                    "id": request_id
                },
                status_code=400
            )
        
        # 데이터 적용
        global projects, tasks, requests, agents
        projects.update(imported_data["projects"])
        tasks.update(imported_data["tasks"])
        requests.update(imported_data["requests"])
        
        # 에이전트 데이터가 있으면 적용
        if "agents" in imported_data:
            agents.update(imported_data["agents"])
        
        # 세션 ID가 유효하면 해당 세션의 마지막 활동 시간 업데이트
        if session_id:
            sessions[session_id]["last_activity"] = datetime.now().isoformat()
            
            # 가져온 데이터를 다시 파일에 저장 (최신 상태 유지)
            try:
                from api.data_persistence import save_data_to_file
                current_data = {
                    "projects": projects,
                    "tasks": tasks,
                    "requests": requests,
                    "agents": agents,
                    "import_time": datetime.now().isoformat(),
                    "session_id": session_id
                }
                await save_data_to_file(session_id, current_data)
                logger.info(f"가져온 데이터를 파일에 다시 저장했습니다: {session_id}")
            except Exception as e:
                logger.warning(f"가져온 데이터 파일 저장 실패: {str(e)}")
        
        response = {
            "jsonrpc": "2.0",
            "result": {
                "message": "Data imported successfully",
                "projects_count": len(projects),
                "tasks_count": len(tasks),
                "requests_count": len(requests),
                "agents_count": len(agents)
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"import_data 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in import_data: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

# 진행 상황 테이블 생성 헬퍼 함수
def generate_progress_table(request_id_str):
    if request_id_str not in requests:
        return {"error": "Request not found"}
    
    user_request = requests[request_id_str]
    tasks_summary = []
    
    for task in user_request["tasks"]:
        tasks_summary.append({
            "id": task["id"],
            "title": task["title"],
            "status": task["status"],
            "created_at": task["created_at"],
            "completed_at": task["completed_at"],
            "approved_at": task["approved_at"]
        })
    
    return {
        "request": {
            "id": user_request["id"],
            "original_request": user_request["original_request"],
            "status": user_request["status"],
            "created_at": user_request["created_at"],
            "completed_at": user_request["completed_at"]
        },
        "tasks": tasks_summary
    }

# 에이전트 관련 메서드 구현
async def handle_create_agent(params, request_id):
    try:
        agent_type = params[0].get("type", "")
        agent_name = params[0].get("name", "")
        agent_config = params[0].get("config", {})
        
        # 에이전트 타입 유효성 검사
        valid_types = ["pm", "designer", "frontend", "backend", "ai_engineer"]
        if agent_type not in valid_types:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": f"Invalid agent type. Must be one of: {', '.join(valid_types)}"
                    },
                    "id": request_id
                },
                status_code=400
            )
        
        # 새 에이전트 생성
        agent_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # 디자이너 에이전트의 경우 추가 속성 설정
        if agent_type == "designer":
            # 디자인 시스템 설정
            design_system_id = agent_config.get("design_system_id", "default")
            if design_system_id not in design_systems:
                design_system_id = "default"  # 존재하지 않으면 기본 시스템 사용
                
            agent_config["design_system_id"] = design_system_id
            
            # 디자이너 특화 속성
            agent_config["capabilities"] = agent_config.get("capabilities", [
                "ui_components", "screens", "themes", "icons", "design_review"
            ])
            
            # 스타일 선호도 설정
            if "style_preferences" not in agent_config:
                agent_config["style_preferences"] = {
                    "style": "modern",
                    "color_scheme": "light",
                    "layout_density": "comfortable"
                }
        
        agent = {
            "id": agent_id,
            "type": agent_type,
            "name": agent_name,
            "config": agent_config,
            "status": "idle",
            "created_at": now,
            "last_active": now,
            "tasks": [],
            "results": {}
        }
        
        # 에이전트 저장
        agents[agent_id] = agent
        
        response = {
            "jsonrpc": "2.0",
            "result": {
                "agentId": agent_id,
                "message": f"{agent_type.capitalize()} agent '{agent_name}' created successfully"
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"create_agent 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in create_agent: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_get_agent(params, request_id):
    try:
        agent_id = params[0].get("agentId", "")
        
        if agent_id not in agents:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Agent not found"},
                    "id": request_id
                },
                status_code=404
            )
        
        agent = agents[agent_id]
        
        response = {
            "jsonrpc": "2.0",
            "result": {
                "agent": {
                    "id": agent["id"],
                    "type": agent["type"],
                    "name": agent["name"],
                    "status": agent["status"],
                    "created_at": agent["created_at"],
                    "last_active": agent["last_active"],
                    "task_count": len(agent["tasks"])
                }
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"get_agent 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in get_agent: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_list_agents(params, request_id):
    try:
        agent_type = params[0].get("type", None) if params else None
        
        agent_list = []
        for agent_id, agent in agents.items():
            if agent_type is None or agent["type"] == agent_type:
                agent_list.append({
                    "id": agent["id"],
                    "type": agent["type"],
                    "name": agent["name"],
                    "status": agent["status"],
                    "created_at": agent["created_at"]
                })
        
        response = {
            "jsonrpc": "2.0",
            "result": {
                "agents": agent_list,
                "count": len(agent_list)
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"list_agents 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in list_agents: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_assign_task_to_agent(params, request_id):
    try:
        agent_id = params[0].get("agentId", "")
        task_data = params[0].get("task", {})
        priority = params[0].get("priority", "medium")
        
        if agent_id not in agents:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Agent not found"},
                    "id": request_id
                },
                status_code=404
            )
        
        # 작업 생성
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        task = {
            "id": task_id,
            "agent_id": agent_id,
            "data": task_data,
            "priority": priority,
            "status": "pending",
            "created_at": now,
            "started_at": None,
            "completed_at": None,
            "result": None
        }
        
        # 에이전트에 작업 할당
        agents[agent_id]["tasks"].append(task_id)
        agents[agent_id]["status"] = "assigned"
        agents[agent_id]["last_active"] = now
        
        # 작업 저장
        if "agent_tasks" not in globals():
            globals()["agent_tasks"] = {}
        globals()["agent_tasks"][task_id] = task
        
        # 에이전트 타입별 특화 처리
        agent_type = agents[agent_id]["type"]
        task_result = None
        
        if agent_type == "designer":
            # 디자이너 에이전트 작업 처리
            task_result = process_designer_task(agents[agent_id], task_data)
        elif agent_type == "frontend":
            # 프론트엔드 에이전트 작업 예시
            if "type" in task_data and task_data["type"] == "generate_component":
                task_result = {
                    "code": f"// React component for {task_data.get('name', 'Component')}\nfunction {task_data.get('name', 'Component')}() {{\n  return <div>Hello World</div>;\n}}",
                    "status": "generated"
                }
        
        # 결과가 있으면 즉시 완료 처리
        if task_result:
            agents[agent_id]["results"][task_id] = task_result
            agents[agent_id]["status"] = "idle"
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            task["result"] = task_result
        
        response = {
            "jsonrpc": "2.0",
            "result": {
                "taskId": task_id,
                "agentId": agent_id,
                "message": f"Task assigned to {agent_type} agent '{agents[agent_id]['name']}'",
                "status": task["status"]
            },
            "id": request_id
        }
        
        # 즉시 처리된 결과가 있으면 포함
        if task_result:
            response["result"]["result"] = task_result
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"assign_task_to_agent 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in assign_task_to_agent: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

# 디자이너 에이전트 작업 처리 함수
def process_designer_task(agent, task_data):
    """
    디자이너 에이전트의 작업을 처리하는 함수
    """
    task_type = task_data.get("type", "")
    design_system_id = agent["config"].get("design_system_id", "default")
    design_system = design_systems.get(design_system_id, design_systems["default"])
    
    # 작업 유형에 따른 처리
    if task_type == DESIGN_TASK_TYPES["GENERATE_COMPONENT"]:
        return generate_component_design(task_data, design_system)
    
    elif task_type == DESIGN_TASK_TYPES["GENERATE_SCREEN"]:
        return generate_screen_design(task_data, design_system)
    
    elif task_type == DESIGN_TASK_TYPES["GENERATE_THEME"]:
        return generate_theme(task_data)
    
    elif task_type == DESIGN_TASK_TYPES["REVIEW_DESIGN"]:
        return review_design(task_data)
    
    elif task_type == DESIGN_TASK_TYPES["CREATE_DESIGN_SYSTEM"]:
        return create_design_system(task_data)
    
    elif task_type == DESIGN_TASK_TYPES["UPDATE_DESIGN_SYSTEM"]:
        return update_design_system(task_data, design_system_id)
    
    elif task_type == DESIGN_TASK_TYPES["EXTERNAL_TOOL_DESIGN"]:
        return process_external_tool_design(agent, task_data)
    
    # 기본 응답 (지원되지 않는 작업 유형)
    return {
        "status": "error",
        "message": f"Unsupported task type: {task_type}",
        "supportedTypes": list(DESIGN_TASK_TYPES.values())
    }

# 외부 디자인 툴 작업 처리 함수
def process_external_tool_design(agent, task_data):
    """
    외부 디자인 툴을 사용한 작업을 처리하는 함수
    """
    tool_type = task_data.get("tool_type", "")
    design_request = task_data.get("design_request", "")
    
    if not tool_type or not design_request:
        return {
            "status": "error",
            "message": "Missing required parameters: tool_type and design_request"
        }
    
    # 외부 툴 요청 정보 생성
    return {
        "status": "pending",
        "message": "External tool design request needs user approval",
        "action": "request_external_tool_permission",
        "parameters": {
            "agentId": agent["id"],
            "toolType": tool_type,
            "taskDescription": design_request
        },
        "next_steps": "Please call 'request_external_tool_permission' with the provided parameters to continue."
    }

# 컴포넌트 디자인 생성 함수
def generate_component_design(task_data, design_system):
    """
    UI 컴포넌트 디자인을 생성하는 함수
    """
    component_type = task_data.get("component_type", "button")
    variant = task_data.get("variant", "primary")
    label = task_data.get("label", "Button")
    size = task_data.get("size", "medium")
    custom_styles = task_data.get("custom_styles", {})
    
    # 컴포넌트 유형별 처리
    if component_type == "button":
        return generate_button_design(label, variant, size, custom_styles, design_system)
    
    elif component_type == "card":
        return generate_card_design(task_data, design_system)
    
    elif component_type == "input":
        return generate_input_design(task_data, design_system)
    
    elif component_type == "navbar":
        return generate_navbar_design(task_data, design_system)
    
    elif component_type == "modal":
        return generate_modal_design(task_data, design_system)
    
    # 지원되지 않는 컴포넌트 유형
    return {
        "status": "error",
        "message": f"Unsupported component type: {component_type}",
        "supportedTypes": ["button", "card", "input", "navbar", "modal"]
    }

# 버튼 디자인 생성 함수
def generate_button_design(label, variant, size, custom_styles, design_system):
    """
    버튼 디자인을 생성하는 함수
    """
    # 버튼 크기에 따른 패딩 결정
    size_padding_map = {
        "small": f"{design_system['spacing']['xs']}px {design_system['spacing']['sm']}px",
        "medium": f"{design_system['spacing']['sm']}px {design_system['spacing']['md']}px",
        "large": f"{design_system['spacing']['md']}px {design_system['spacing']['lg']}px"
    }
    
    # 버튼 크기에 따른 폰트 크기 결정
    size_font_map = {
        "small": design_system['typography']['caption']['fontSize'],
        "medium": design_system['typography']['button']['fontSize'],
        "large": design_system['typography']['body1']['fontSize']
    }
    
    # 버튼 유형별 색상 설정
    variant_colors = {
        "primary": {
            "background": design_system['colors']['primary'],
            "text": "#FFFFFF",
            "border": "none",
            "hover_background": "#3169c6"  # 약간 어두운 primary
        },
        "secondary": {
            "background": design_system['colors']['secondary'],
            "text": "#FFFFFF", 
            "border": "none",
            "hover_background": "#6929c4"  # 약간 어두운 secondary
        },
        "outline": {
            "background": "transparent",
            "text": design_system['colors']['primary'],
            "border": f"1px solid {design_system['colors']['primary']}",
            "hover_background": "rgba(58, 134, 255, 0.05)"  # 연한 primary
        },
        "text": {
            "background": "transparent",
            "text": design_system['colors']['primary'],
            "border": "none",
            "hover_background": "rgba(58, 134, 255, 0.05)"  # 연한 primary
        }
    }
    
    # 기본 버튼 생성
    button_design = {
        "type": "button",
        "label": label,
        "variant": variant,
        "size": size,
        "styles": {
            "padding": size_padding_map.get(size, size_padding_map["medium"]),
            "fontSize": f"{size_font_map.get(size, size_font_map['medium'])}px",
            "fontWeight": design_system['typography']['button']['fontWeight'],
            "borderRadius": f"{design_system['borderRadius']['medium']}px",
            "backgroundColor": variant_colors.get(variant, variant_colors["primary"])["background"],
            "color": variant_colors.get(variant, variant_colors["primary"])["text"],
            "border": variant_colors.get(variant, variant_colors["primary"])["border"],
            "boxShadow": design_system['shadows']['small'] if variant != "text" else "none",
            "cursor": "pointer",
            "transition": "all 0.3s ease",
            "hover": {
                "backgroundColor": variant_colors.get(variant, variant_colors["primary"])["hover_background"],
                "boxShadow": design_system['shadows']['medium'] if variant != "text" else "none",
            }
        },
        "css": "",  # CSS 스타일은 아래에서 생성
        "react": "",  # React 컴포넌트 코드는 아래에서 생성
        "html": ""   # HTML 코드는 아래에서 생성
    }
    
    # 커스텀 스타일 적용
    if custom_styles:
        for key, value in custom_styles.items():
            button_design["styles"][key] = value
    
    # CSS 생성
    style_css = f"""
.button-{variant}-{size} {{
    padding: {button_design["styles"]["padding"]};
    font-size: {button_design["styles"]["fontSize"]};
    font-weight: {button_design["styles"]["fontWeight"]};
    border-radius: {button_design["styles"]["borderRadius"]};
    background-color: {button_design["styles"]["backgroundColor"]};
    color: {button_design["styles"]["color"]};
    border: {button_design["styles"]["border"]};
    box-shadow: {button_design["styles"]["boxShadow"]};
    cursor: pointer;
    transition: all 0.3s ease;
}}

.button-{variant}-{size}:hover {{
    background-color: {button_design["styles"]["hover"]["backgroundColor"]};
    box-shadow: {button_design["styles"]["hover"]["boxShadow"]};
}}
"""
    button_design["css"] = style_css.strip()
    
    # React 컴포넌트 생성
    react_component = f"""
import React from 'react';

// {variant.capitalize()} {size.capitalize()} Button Component
export const Button = ({{ label = "{label}", onClick }}) => {{
  return (
    <button
      className="button-{variant}-{size}"
      onClick={onClick}
    >
      {label}
    </button>
  );
}};

// 인라인 스타일 사용 예시
export const ButtonInline = ({{ label = "{label}", onClick }}) => {{
  const buttonStyle = {{
    padding: "{button_design["styles"]["padding"]}",
    fontSize: "{button_design["styles"]["fontSize"]}",
    fontWeight: "{button_design["styles"]["fontWeight"]}",
    borderRadius: "{button_design["styles"]["borderRadius"]}",
    backgroundColor: "{button_design["styles"]["backgroundColor"]}",
    color: "{button_design["styles"]["color"]}",
    border: "{button_design["styles"]["border"]}",
    boxShadow: "{button_design["styles"]["boxShadow"]}",
    cursor: "pointer",
    transition: "all 0.3s ease"
  }};
  
  const hoverStyle = {{
    backgroundColor: "{button_design["styles"]["hover"]["backgroundColor"]}",
    boxShadow: "{button_design["styles"]["hover"]["boxShadow"]}"
  }};
  
  return (
    <button
      style={buttonStyle}
      onClick={onClick}
      onMouseOver={(e) => {{
        Object.assign(e.target.style, hoverStyle);
      }}}
      onMouseOut={(e) => {{
        Object.assign(e.target.style, buttonStyle);
      }}}
    >
      {label}
    </button>
  );
}};
"""
    button_design["react"] = react_component.strip()
    
    # HTML 생성
    html_code = f"""
<button class="button-{variant}-{size}">{label}</button>

<style>
{button_design["css"]}
</style>
"""
    button_design["html"] = html_code.strip()
    
    return {
        "status": "generated",
        "component": button_design
    }

# 카드 디자인 생성 함수
def generate_card_design(task_data, design_system):
    """
    카드 컴포넌트 디자인을 생성하는 함수
    """
    variant = task_data.get("variant", "basic")
    title = task_data.get("title", "Card Title")
    content = task_data.get("content", "Card content goes here.")
    has_image = task_data.get("has_image", False)
    has_footer = task_data.get("has_footer", False)
    custom_styles = task_data.get("custom_styles", {})
    
    # 카드 디자인 생성
    card_design = {
        "type": "card",
        "variant": variant,
        "title": title,
        "content": content,
        "has_image": has_image,
        "has_footer": has_footer,
        "styles": {
            "width": "100%",
            "maxWidth": "320px",
            "backgroundColor": design_system['colors']['surface'],
            "borderRadius": f"{design_system['borderRadius']['medium']}px",
            "boxShadow": design_system['shadows']['medium'],
            "overflow": "hidden",
            "padding": "0" if variant == "flush" else f"{design_system['spacing']['md']}px",
            "border": f"1px solid {design_system['colors']['text']['disabled']}",
            "title": {
                "fontSize": f"{design_system['typography']['heading3']['fontSize']}px",
                "fontWeight": design_system['typography']['heading3']['fontWeight'],
                "color": design_system['colors']['text']['primary'],
                "marginBottom": f"{design_system['spacing']['sm']}px"
            },
            "content": {
                "fontSize": f"{design_system['typography']['body1']['fontSize']}px",
                "lineHeight": design_system['typography']['body1']['lineHeight'],
                "color": design_system['colors']['text']['secondary']
            },
            "image": {
                "width": "100%",
                "height": "160px",
                "objectFit": "cover",
                "marginBottom": "0" if variant == "flush" else f"{design_system['spacing']['sm']}px"
            },
            "footer": {
                "marginTop": f"{design_system['spacing']['md']}px",
                "paddingTop": f"{design_system['spacing']['sm']}px",
                "borderTop": f"1px solid {design_system['colors']['text']['disabled']}",
                "display": "flex",
                "justifyContent": "flex-end",
                "alignItems": "center"
            }
        },
        "css": "",
        "react": "",
        "html": ""
    }
    
    # 커스텀 스타일 적용
    if custom_styles:
        for key, value in custom_styles.items():
            if key in card_design["styles"]:
                if isinstance(card_design["styles"][key], dict) and isinstance(value, dict):
                    card_design["styles"][key].update(value)
                else:
                    card_design["styles"][key] = value
    
    # CSS 생성 (간략화)
    card_design["css"] = f"""
.card-{variant} {{
    width: {card_design["styles"]["width"]};
    max-width: {card_design["styles"]["maxWidth"]};
    background-color: {card_design["styles"]["backgroundColor"]};
    border-radius: {card_design["styles"]["borderRadius"]};
    box-shadow: {card_design["styles"]["boxShadow"]};
    overflow: {card_design["styles"]["overflow"]};
    padding: {card_design["styles"]["padding"]};
    border: {card_design["styles"]["border"]};
}}

.card-{variant} .card-title {{
    font-size: {card_design["styles"]["title"]["fontSize"]};
    font-weight: {card_design["styles"]["title"]["fontWeight"]};
    color: {card_design["styles"]["title"]["color"]};
    margin-bottom: {card_design["styles"]["title"]["marginBottom"]};
}}

.card-{variant} .card-content {{
    font-size: {card_design["styles"]["content"]["fontSize"]};
    line-height: {card_design["styles"]["content"]["lineHeight"]};
    color: {card_design["styles"]["content"]["color"]};
}}

.card-{variant} .card-image {{
    width: {card_design["styles"]["image"]["width"]};
    height: {card_design["styles"]["image"]["height"]};
    object-fit: {card_design["styles"]["image"]["objectFit"]};
    margin-bottom: {card_design["styles"]["image"]["marginBottom"]};
}}

.card-{variant} .card-footer {{
    margin-top: {card_design["styles"]["footer"]["marginTop"]};
    padding-top: {card_design["styles"]["footer"]["paddingTop"]};
    border-top: {card_design["styles"]["footer"]["borderTop"]};
    display: {card_design["styles"]["footer"]["display"]};
    justify-content: {card_design["styles"]["footer"]["justifyContent"]};
    align-items: {card_design["styles"]["footer"]["alignItems"]};
}}
"""
    
    # React 컴포넌트 생성 - 변수들을 미리 계산
    img_url = "https://via.placeholder.com/320x160" if has_image else "null"
    footer_content = "Card Footer" if has_footer else "null"
    
    # f-string 대신 일반 문자열 사용
    react_code = """
import React from 'react';

export const Card = ({ 
  title = "TITLE_PLACEHOLDER", 
  content = "CONTENT_PLACEHOLDER", 
  imageUrl = IMAGE_URL_PLACEHOLDER, 
  footerContent = FOOTER_CONTENT_PLACEHOLDER 
}) => {
  return (
    <div className="card-VARIANT_PLACEHOLDER">
      IMAGE_COMPONENT_PLACEHOLDER
      <div className="card-title">{title}</div>
      <div className="card-content">{content}</div>
      FOOTER_COMPONENT_PLACEHOLDER
    </div>
  );
};
"""
    
    # 플레이스홀더 값 대체
    react_code = react_code.replace("TITLE_PLACEHOLDER", title)
    react_code = react_code.replace("CONTENT_PLACEHOLDER", content)
    react_code = react_code.replace("IMAGE_URL_PLACEHOLDER", img_url)
    react_code = react_code.replace("FOOTER_CONTENT_PLACEHOLDER", footer_content)
    react_code = react_code.replace("VARIANT_PLACEHOLDER", variant)
    
    # 이미지와 푸터 컴포넌트 조건부 추가
    img_component = '<img src={imageUrl} alt={title} className="card-image" />'
    react_code = react_code.replace("IMAGE_COMPONENT_PLACEHOLDER", img_component if has_image else "")
    
    footer_component = '<div className="card-footer">{footerContent}</div>'
    react_code = react_code.replace("FOOTER_COMPONENT_PLACEHOLDER", footer_component if has_footer else "")
    
    card_design["react"] = react_code.strip()
    
    # HTML 생성도 유사하게
    html_code = """
<div class="card-VARIANT_PLACEHOLDER">
  IMAGE_HTML_PLACEHOLDER
  <div class="card-title">TITLE_PLACEHOLDER</div>
  <div class="card-content">CONTENT_PLACEHOLDER</div>
  FOOTER_HTML_PLACEHOLDER
</div>
<style>
CSS_PLACEHOLDER
</style>
"""
    
    # 플레이스홀더 값 대체
    html_code = html_code.replace("TITLE_PLACEHOLDER", title)
    html_code = html_code.replace("CONTENT_PLACEHOLDER", content)
    html_code = html_code.replace("VARIANT_PLACEHOLDER", variant)
    html_code = html_code.replace("CSS_PLACEHOLDER", card_design["css"])
    
    # 이미지와 푸터 HTML 조건부 추가
    img_html = '<img src="https://via.placeholder.com/320x160" alt="' + title + '" class="card-image" />'
    html_code = html_code.replace("IMAGE_HTML_PLACEHOLDER", img_html if has_image else "")
    
    footer_html = '<div class="card-footer">Card Footer</div>'
    html_code = html_code.replace("FOOTER_HTML_PLACEHOLDER", footer_html if has_footer else "")
    
    card_design["html"] = html_code.strip()
    
    return {
        "status": "generated",
        "component": card_design
    }

# 간략화된 구현을 위한 다른 디자인 생성 함수들
def generate_input_design(task_data, design_system):
    # 간략한 구현
    return {
        "status": "generated",
        "component": {
            "type": "input",
            "variant": task_data.get("variant", "outline"),
            "placeholder": task_data.get("placeholder", "Enter text..."),
            "label": task_data.get("label", "Input label"),
            "styles": {
                "input": {
                    "width": "100%",
                    "padding": f"{design_system['spacing']['sm']}px {design_system['spacing']['md']}px",
                    "fontSize": f"{design_system['typography']['body1']['fontSize']}px",
                    "borderRadius": f"{design_system['borderRadius']['medium']}px",
                    "border": f"1px solid {design_system['colors']['text']['disabled']}",
                    "outline": "none",
                    "transition": "all 0.3s ease"
                },
                "label": {
                    "fontSize": f"{design_system['typography']['body2']['fontSize']}px",
                    "fontWeight": "medium",
                    "marginBottom": f"{design_system['spacing']['xs']}px",
                    "color": design_system['colors']['text']['primary']
                }
            }
        }
    }

def generate_navbar_design(task_data, design_system):
    # 간략한 구현
    return {
        "status": "generated",
        "component": {
            "type": "navbar",
            "variant": task_data.get("variant", "fixed"),
            "title": task_data.get("title", "Brand Name"),
            "links": task_data.get("links", ["Home", "Features", "Pricing", "About"]),
            "styles": {
                "navbar": {
                    "backgroundColor": design_system['colors']['primary'],
                    "color": "#FFFFFF",
                    "padding": f"{design_system['spacing']['md']}px",
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center"
                }
            }
        }
    }

def generate_modal_design(task_data, design_system):
    # 간략한 구현
    return {
        "status": "generated",
        "component": {
            "type": "modal",
            "title": task_data.get("title", "Modal Title"),
            "content": task_data.get("content", "Modal content goes here."),
            "hasCloseButton": task_data.get("hasCloseButton", True),
            "hasFooter": task_data.get("hasFooter", True),
            "styles": {
                "modal": {
                    "backgroundColor": design_system['colors']['surface'],
                    "borderRadius": f"{design_system['borderRadius']['medium']}px",
                    "boxShadow": design_system['shadows']['large'],
                    "width": "90%",
                    "maxWidth": "500px",
                    "padding": f"{design_system['spacing']['lg']}px"
                }
            }
        }
    }

def generate_screen_design(task_data, design_system):
    """
    전체 화면 디자인을 생성하는 함수
    """
    screen_type = task_data.get("screen_type", "login")
    theme = task_data.get("theme", "light")
    
    # 화면 유형에 따른 구성요소 생성
    if screen_type == "login":
        return generate_login_screen(task_data, design_system, theme)
    elif screen_type == "dashboard":
        return generate_dashboard_screen(task_data, design_system, theme)
    elif screen_type == "product_list":
        return generate_product_list_screen(task_data, design_system, theme)
    elif screen_type == "detail":
        return generate_detail_screen(task_data, design_system, theme)
    else:
        return {
            "status": "error",
            "message": f"Unsupported screen type: {screen_type}",
            "supportedTypes": ["login", "dashboard", "product_list", "detail"]
        }

def generate_login_screen(task_data, design_system, theme):
    # 간략한 구현
    background = design_system['colors']['background'] if theme == "light" else "#1A1A1A"
    
    return {
        "status": "generated",
        "screen": {
            "type": "login",
            "theme": theme,
            "title": task_data.get("title", "로그인"),
            "components": [
                {"type": "logo", "size": "large"},
                {"type": "heading", "text": "로그인", "level": 1},
                {"type": "input", "label": "이메일", "placeholder": "email@example.com", "type": "email"},
                {"type": "input", "label": "비밀번호", "placeholder": "비밀번호 입력", "type": "password"},
                {"type": "button", "text": "로그인", "variant": "primary", "size": "large", "width": "100%"},
                {"type": "link", "text": "계정이 없으신가요? 회원가입", "align": "center"}
            ],
            "layout": "centered",
            "background": background
        }
    }

# 간략화된 구현을 위한 다른 화면 디자인 생성 함수들
def generate_dashboard_screen(task_data, design_system, theme):
    # 간략한 구현
    return {
        "status": "generated",
        "screen": {
            "type": "dashboard",
            "theme": theme,
            "layout": "sidebar"
        }
    }

def generate_product_list_screen(task_data, design_system, theme):
    # 간략한 구현
    return {
        "status": "generated",
        "screen": {
            "type": "product_list",
            "theme": theme,
            "layout": "grid"
        }
    }

def generate_detail_screen(task_data, design_system, theme):
    # 간략한 구현
    return {
        "status": "generated",
        "screen": {
            "type": "detail",
            "theme": theme,
            "layout": "stacked"
        }
    }

def generate_theme(task_data):
    """
    디자인 테마를 생성하는 함수
    """
    # 간략한 구현
    theme_name = task_data.get("name", "Custom Theme")
    base_color = task_data.get("base_color", "#3A86FF")
    
    return {
        "status": "generated",
        "theme": {
            "name": theme_name,
            "colors": {
                "primary": base_color,
                "secondary": task_data.get("secondary_color", "#8338EC"),
                "background": task_data.get("background_color", "#F8F9FA"),
                "text": {
                    "primary": task_data.get("text_primary_color", "#212529"),
                    "secondary": task_data.get("text_secondary_color", "#6C757D")
                }
            }
        }
    }

def review_design(task_data):
    """
    디자인을 검토하고 피드백을 제공하는 함수
    """
    # 간략한 구현
    return {
        "status": "completed",
        "review": {
            "feedback": "디자인 검토 완료",
            "suggestions": [
                "컬러 대비를 높여 접근성 개선",
                "모바일 화면 레이아웃 최적화",
                "일관된 여백과 정렬 적용"
            ]
        }
    }

# 디자인 시스템 관련 메서드 구현
async def handle_create_design_system(params, request_id):
    try:
        # 파라미터 추출
        name = params[0].get("name", "Custom Design System")
        colors = params[0].get("colors", {})
        typography = params[0].get("typography", {})
        spacing = params[0].get("spacing", {})
        border_radius = params[0].get("borderRadius", {})
        shadows = params[0].get("shadows", {})
        
        # 디자인 시스템 ID 생성
        design_system_id = str(uuid.uuid4())
        
        # 기본 디자인 시스템 복사하여 새로운 시스템 생성
        new_system = dict(design_systems["default"])
        new_system["id"] = design_system_id
        new_system["name"] = name
        
        # 사용자 제공 값으로 업데이트
        if colors:
            for key, value in colors.items():
                if key in new_system["colors"]:
                    if isinstance(new_system["colors"][key], dict) and isinstance(value, dict):
                        new_system["colors"][key].update(value)
                    else:
                        new_system["colors"][key] = value
        
        if typography:
            for key, value in typography.items():
                if key in new_system["typography"]:
                    if isinstance(new_system["typography"][key], dict) and isinstance(value, dict):
                        new_system["typography"][key].update(value)
                    else:
                        new_system["typography"][key] = value
        
        if spacing:
            new_system["spacing"].update(spacing)
        
        if border_radius:
            new_system["borderRadius"].update(border_radius)
        
        if shadows:
            new_system["shadows"].update(shadows)
        
        # 생성된 디자인 시스템 저장
        design_systems[design_system_id] = new_system
        
        # 응답 생성
        response = {
            "jsonrpc": "2.0",
            "result": {
                "design_system_id": design_system_id,
                "name": name,
                "message": "디자인 시스템이 성공적으로 생성되었습니다."
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"create_design_system 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in create_design_system: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_update_design_system(params, request_id):
    try:
        # 파라미터 추출
        design_system_id = params[0].get("design_system_id", "")
        name = params[0].get("name", None)
        colors = params[0].get("colors", {})
        typography = params[0].get("typography", {})
        spacing = params[0].get("spacing", {})
        border_radius = params[0].get("borderRadius", {})
        shadows = params[0].get("shadows", {})
        
        # 디자인 시스템 존재 확인
        if design_system_id not in design_systems:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "디자인 시스템을 찾을 수 없습니다."},
                    "id": request_id
                },
                status_code=404
            )
        
        # 디자인 시스템 가져오기
        design_system = design_systems[design_system_id]
        
        # 이름 업데이트
        if name:
            design_system["name"] = name
        
        # 색상 업데이트
        if colors:
            for key, value in colors.items():
                if key in design_system["colors"]:
                    if isinstance(design_system["colors"][key], dict) and isinstance(value, dict):
                        design_system["colors"][key].update(value)
                    else:
                        design_system["colors"][key] = value
        
        # 타이포그래피 업데이트
        if typography:
            for key, value in typography.items():
                if key in design_system["typography"]:
                    if isinstance(design_system["typography"][key], dict) and isinstance(value, dict):
                        design_system["typography"][key].update(value)
                    else:
                        design_system["typography"][key] = value
        
        # 간격 업데이트
        if spacing:
            design_system["spacing"].update(spacing)
        
        # 테두리 반경 업데이트
        if border_radius:
            design_system["borderRadius"].update(border_radius)
        
        # 그림자 업데이트
        if shadows:
            design_system["shadows"].update(shadows)
        
        # 업데이트된 디자인 시스템 저장
        design_systems[design_system_id] = design_system
        
        # 응답 생성
        response = {
            "jsonrpc": "2.0",
            "result": {
                "design_system_id": design_system_id,
                "name": design_system["name"],
                "message": "디자인 시스템이 성공적으로 업데이트되었습니다."
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"update_design_system 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in update_design_system: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_get_design_system(params, request_id):
    try:
        # 파라미터 추출
        design_system_id = params[0].get("design_system_id", "")
        
        # 디자인 시스템 존재 확인
        if design_system_id not in design_systems:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "디자인 시스템을 찾을 수 없습니다."},
                    "id": request_id
                },
                status_code=404
            )
        
        # 디자인 시스템 가져오기
        design_system = design_systems[design_system_id]
        
        # 응답 생성
        response = {
            "jsonrpc": "2.0",
            "result": {
                "design_system": design_system
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"get_design_system 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in get_design_system: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_list_design_systems(params, request_id):
    try:
        # 디자인 시스템 목록 생성
        design_system_list = []
        for design_system_id, design_system in design_systems.items():
            design_system_list.append({
                "id": design_system_id,
                "name": design_system["name"]
            })
        
        # 응답 생성
        response = {
            "jsonrpc": "2.0",
            "result": {
                "design_systems": design_system_list,
                "count": len(design_system_list)
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"list_design_systems 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in list_design_systems: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )
def create_design_system(task_data):
    """
    새로운 디자인 시스템을 생성하는 함수
    """
    system_id = str(uuid.uuid4())
    name = task_data.get("name", "New Design System")
    
    # 기본 디자인 시스템 기반으로 생성
    new_system = dict(design_systems["default"])
    new_system["id"] = system_id
    new_system["name"] = name
    
    # 사용자 제공 값으로 업데이트
    if "colors" in task_data:
        for key, value in task_data["colors"].items():
            if key in new_system["colors"]:
                if isinstance(new_system["colors"][key], dict) and isinstance(value, dict):
                    new_system["colors"][key].update(value)
                else:
                    new_system["colors"][key] = value
    
    # 생성된 디자인 시스템 저장
    design_systems[system_id] = new_system
    
    return {
        "status": "created",
        "design_system": {
            "id": system_id,
            "name": name,
            "message": "새로운 디자인 시스템이 생성되었습니다."
        }
    }

def update_design_system(task_data, design_system_id):
    """
    기존 디자인 시스템을 업데이트하는 함수
    """
    if design_system_id not in design_systems:
        return {
            "status": "error",
            "message": f"Design system not found: {design_system_id}"
        }
    
    # 현재 디자인 시스템 가져오기
    design_system = design_systems[design_system_id]
    
    # 업데이트 필드 처리
    if "colors" in task_data:
        for key, value in task_data["colors"].items():
            if key in design_system["colors"]:
                if isinstance(design_system["colors"][key], dict) and isinstance(value, dict):
                    design_system["colors"][key].update(value)
                else:
                    design_system["colors"][key] = value
    
    if "typography" in task_data:
        for key, value in task_data["typography"].items():
            if key in design_system["typography"]:
                if isinstance(design_system["typography"][key], dict) and isinstance(value, dict):
                    design_system["typography"][key].update(value)
                else:
                    design_system["typography"][key] = value
    
    if "spacing" in task_data:
        design_system["spacing"].update(task_data["spacing"])
    
    if "borderRadius" in task_data:
        design_system["borderRadius"].update(task_data["borderRadius"])
    
    if "shadows" in task_data:
        design_system["shadows"].update(task_data["shadows"])
    
    # 업데이트된 디자인 시스템 저장
    design_systems[design_system_id] = design_system
    
    return {
        "status": "updated",
        "design_system": {
            "id": design_system_id,
            "name": design_system["name"],
            "message": "디자인 시스템이 업데이트되었습니다."
        }
    }

# Vercel 핸들러는 app 객체 자체여야 합니다.
# handler = app # 이 줄은 필요 없습니다.

# 로컬 개발 환경 실행 (Vercel 배포 시에는 사용되지 않음)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082, reload=True) 

# 외부 디자인 툴 연동 관련 메서드 구현
async def handle_request_external_tool_permission(params, request_id):
    """
    디자이너 에이전트가 외부 디자인 툴 사용 권한을 요청하는 핸들러
    """
    try:
        # 파라미터 추출
        agent_id = params[0].get("agentId", "")
        tool_type = params[0].get("toolType", "")
        task_description = params[0].get("taskDescription", "")
        project_context = params[0].get("projectContext", {})
        
        # 에이전트 존재 확인
        if agent_id not in agents:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Agent not found"},
                    "id": request_id
                },
                status_code=404
            )
        
        agent = agents[agent_id]
        
        # 해당 에이전트가 디자이너인지 확인
        if agent["type"] != "designer":
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Only designer agents can request external tool permissions"},
                    "id": request_id
                },
                status_code=400
            )
        
        # 외부 툴 요청 ID 생성
        tool_request_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # 요청 정보 생성
        tool_request = {
            "id": tool_request_id,
            "agent_id": agent_id,
            "tool_type": tool_type,
            "task_description": task_description,
            "project_context": project_context,
            "status": "pending",
            "created_at": now,
            "updated_at": now,
            "result": None,
            "credentials": None,
            "design_urls": []
        }
        
        # 요청 저장
        external_tool_requests[tool_request_id] = tool_request
        
        # 에이전트에 요청 정보 업데이트
        if "external_tool_requests" not in agent:
            agent["external_tool_requests"] = []
        agent["external_tool_requests"].append(tool_request_id)
        agents[agent_id] = agent
        
        # 응답 생성
        response = {
            "jsonrpc": "2.0",
            "result": {
                "requestId": tool_request_id,
                "status": "pending",
                "message": f"External tool ({tool_type}) permission requested",
                "userPrompt": f"디자이너 에이전트 '{agent['name']}'가 '{tool_type}' 디자인 툴을 사용하여 '{task_description}' 작업을 수행하려고 합니다. 허용하시겠습니까?"
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"request_external_tool_permission 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in request_external_tool_permission: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_approve_external_tool_request(params, request_id):
    """
    사용자/PM이 외부 디자인 툴 사용 요청을 승인하는 핸들러
    """
    try:
        # 파라미터 추출
        tool_request_id = params[0].get("requestId", "")
        approved = params[0].get("approved", False)
        credentials = params[0].get("credentials", {})
        
        # 요청 존재 확인
        if tool_request_id not in external_tool_requests:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "External tool request not found"},
                    "id": request_id
                },
                status_code=404
            )
        
        # 요청 정보 가져오기
        tool_request = external_tool_requests[tool_request_id]
        now = datetime.now().isoformat()
        
        # 승인 상태 업데이트
        if approved:
            tool_request["status"] = "approved"
            tool_request["credentials"] = credentials
            message = "External tool permission approved"
        else:
            tool_request["status"] = "rejected"
            message = "External tool permission rejected"
        
        tool_request["updated_at"] = now
        
        # 업데이트된 요청 저장
        external_tool_requests[tool_request_id] = tool_request
        
        # 응답 생성
        response = {
            "jsonrpc": "2.0",
            "result": {
                "requestId": tool_request_id,
                "status": tool_request["status"],
                "message": message,
                "toolType": tool_request["tool_type"],
                "nextSteps": "approved" if approved else "rejected"
            },
            "id": request_id
        }
        
        # 승인된 경우 관련 MCP 정보 추가
        if approved:
            mcp_info = get_mcp_info_for_tool(tool_request["tool_type"])
            if mcp_info:
                response["result"]["mcpInfo"] = mcp_info
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"approve_external_tool_request 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in approve_external_tool_request: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_get_external_tool_status(params, request_id):
    """
    외부 디자인 툴 요청 상태를 조회하는 핸들러
    """
    try:
        # 파라미터 추출
        tool_request_id = params[0].get("requestId", "")
        
        # 요청 존재 확인
        if tool_request_id not in external_tool_requests:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "External tool request not found"},
                    "id": request_id
                },
                status_code=404
            )
        
        # 요청 정보 가져오기
        tool_request = external_tool_requests[tool_request_id]
        
        # 응답 생성
        response = {
            "jsonrpc": "2.0",
            "result": {
                "requestId": tool_request_id,
                "status": tool_request["status"],
                "toolType": tool_request["tool_type"],
                "agentId": tool_request["agent_id"],
                "createdAt": tool_request["created_at"],
                "updatedAt": tool_request["updated_at"],
                "hasResult": tool_request["result"] is not None,
                "designUrls": tool_request.get("design_urls", [])
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"get_external_tool_status 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in get_external_tool_status: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

async def handle_submit_external_design_result(params, request_id):
    """
    외부 디자인 툴에서 작업한 결과를 제출하는 핸들러
    """
    try:
        # 파라미터 추출
        tool_request_id = params[0].get("requestId", "")
        design_data = params[0].get("designData", {})
        design_urls = params[0].get("designUrls", [])
        
        # 요청 존재 확인
        if tool_request_id not in external_tool_requests:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "External tool request not found"},
                    "id": request_id
                },
                status_code=404
            )
        
        # 요청 정보 가져오기
        tool_request = external_tool_requests[tool_request_id]
        
        # 승인된 요청인지 확인
        if tool_request["status"] != "approved":
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Cannot submit result for non-approved request"},
                    "id": request_id
                },
                status_code=400
            )
        
        now = datetime.now().isoformat()
        
        # 결과 업데이트
        tool_request["result"] = design_data
        tool_request["design_urls"] = design_urls
        tool_request["status"] = "completed"
        tool_request["updated_at"] = now
        
        # 업데이트된 요청 저장
        external_tool_requests[tool_request_id] = tool_request
        
        # 에이전트에게 결과 알림
        agent_id = tool_request["agent_id"]
        if agent_id in agents:
            agent = agents[agent_id]
            
            # 실제 구현에서는 여기에 에이전트에게 결과를 알리는 로직이 추가될 수 있음
            # 예: 에이전트의 메시지 큐에 알림 추가
            
            # 에이전트의 결과 저장
            if "external_tool_results" not in agent:
                agent["external_tool_results"] = {}
            agent["external_tool_results"][tool_request_id] = {
                "result": design_data,
                "design_urls": design_urls,
                "completed_at": now
            }
            agents[agent_id] = agent
        
        # 응답 생성
        response = {
            "jsonrpc": "2.0",
            "result": {
                "requestId": tool_request_id,
                "status": "completed",
                "message": "Design result submitted successfully",
                "toolType": tool_request["tool_type"],
                "designUrlCount": len(design_urls)
            },
            "id": request_id
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"submit_external_design_result 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"Error in submit_external_design_result: {str(e)}"},
                "id": request_id
            },
            status_code=500
        )

# 외부 디자인 툴 MCP 정보 조회 헬퍼 함수
def get_mcp_info_for_tool(tool_type):
    """
    외부 디자인 툴 타입에 따른 MCP 정보를 반환하는 함수
    """
    mcp_info_map = {
        "figma": {
            "toolName": "Figma",
            "mcpServer": "smithery-ai/figma-mcp-server",
            "description": "Figma API를 사용하여 디자인 작업을 수행합니다.",
            "methods": ["create_design", "modify_design", "export_design", "create_component"],
            "setupInstructions": "Figma 계정과 개인 액세스 토큰이 필요합니다."
        },
        "21st.dev": {
            "toolName": "21st.dev",
            "mcpServer": "mcp_magic_21st_magic_component_builder",
            "description": "21st.dev를 통해 React 컴포넌트와 디자인 요소를 생성합니다.",
            "methods": ["magic_component_builder", "magic_component_inspiration", "magic_component_refiner"],
            "setupInstructions": "21st.dev 연동을 위한 설정이 필요합니다."
        },
        "sketch": {
            "toolName": "Sketch",
            "mcpServer": "sketch-mcp-server",
            "description": "Sketch를 통해 디자인 작업을 수행합니다.",
            "methods": ["create_artboard", "export_asset"],
            "setupInstructions": "Sketch 앱과 API 액세스가 필요합니다."
        }
    }
    
    return mcp_info_map.get(tool_type, None)