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

# Vercel 핸들러는 app 객체 자체여야 합니다.
# handler = app # 이 줄은 필요 없습니다.

# 로컬 개발 환경 실행 (Vercel 배포 시에는 사용되지 않음)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082, reload=True) 