#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent MCP API 확장 모듈

PMAgent를 MCP(Model Context Protocol) 서버로 확장하여 에이전트 간 협업 기능을 제공합니다.
"""

import os
import logging
import json
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Union
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# task_manager를 직접 임포트 (점진적으로 사용 줄일 예정)
from pmagent.task_manager import task_manager as global_task_manager
import pmagent.db_manager as db_manager # DB 매니저 임포트

from .auth import AuthManager
from .agent_coordinator import AgentCoordinator
from .distributed_storage import DistributedStorage
from .mcp_common import MCPServer
from .api import create_api_app

# 에이전트 팩토리 가져오기
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.agent_factory import AgentFactory

logger = logging.getLogger(__name__)

class PMAgentMCPAPI:
    """
    PMAgent MCP API 클래스
    
    PMAgent 에이전트 협업 시스템을 MCP 서버로 확장하는 클래스입니다.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        PMAgentMCPAPI 초기화
        
        Args:
            config: 설정 (기본값: None)
        """
        self.config = config or {}
        
        # 데이터 디렉토리 설정
        self.data_dir = self.config.get("data_dir", "./data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # API 앱 생성
        self.api_app = create_api_app({"data_dir": self.data_dir})
        
        # 인증 관리자, 에이전트 코디네이터, 저장소 가져오기
        from .api.routes import auth_manager, agent_coordinator, storage
        self.auth_manager = auth_manager
        self.agent_coordinator = agent_coordinator
        
        # 저장소 초기화 확인
        self.storage = storage
        if self.storage is None:
            logger.warning("저장소 객체가 초기화되지 않음. 새로 생성합니다.")
            from .distributed_storage import DistributedStorage, FileSystemBackend
            self.storage = DistributedStorage()
            # 파일 시스템 백엔드 추가
            file_backend = FileSystemBackend(os.path.join(self.data_dir, "storage"))
            self.storage.add_backend("file", file_backend)
            self.storage.set_current_backend("file")
            logger.info("저장소 초기화 완료")
            
            # 모듈 수준에서 저장소 객체 업데이트
            if "pmagent.api.routes" in sys.modules:
                sys.modules["pmagent.api.routes"].storage = self.storage
                logger.info("routes 모듈의 저장소 참조 업데이트됨")
        else:
            logger.info("기존 저장소 객체 사용")
        
        # MCP 서버 생성
        mcp_tools = self._create_mcp_tools()
        self.mcp_server = MCPServer(
            server_name="pmagent-mcp-server",
            server_version="0.1.0",
            tools=mcp_tools,
            description="프로젝트 관리 에이전트 협업 시스템 MCP 서버",
            tools_data_path=os.path.join(self.data_dir, "mcp_tools.json")
        )
        
        # API 앱에 MCP 엔드포인트 추가
        self._add_mcp_endpoints()
        
        # CORS 미들웨어 추가
        self.api_app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.get("cors_origins", ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _create_mcp_tools(self) -> List[Dict[str, Any]]:
        """
        MCP 서버용 도구 목록을 생성합니다.
        
        Returns:
            List[Dict[str, Any]]: MCP 도구 목록
        """
        tools = [
            # 에이전트 등록 도구
            {
                "name": "register_agent",
                "description": "새 에이전트를 등록합니다.",
                "parameters": {
                    "type": "object",
                    "required": ["agent_type", "capabilities"],
                    "properties": {
                        "agent_type": {
                            "type": "string",
                            "description": "에이전트 유형 (pm, designer, frontend, backend, ai_engineer)"
                        },
                        "capabilities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "에이전트 기능 목록"
                        }
                    }
                },
                "function": self._mcp_register_agent
            },
            
            # 작업 관리 도구들
            {
                "name": "request_planning",
                "description": "새 요청을 계획하고 작업을 생성합니다.",
                "parameters": {
                    "type": "object",
                    "required": ["originalRequest", "tasks"],
                    "properties": {
                        "originalRequest": {
                            "type": "string",
                            "description": "원본 요청 설명"
                        },
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["title", "description"],
                                "properties": {
                                    "title": {"type": "string"},
                                    "description": {"type": "string"}
                                }
                            },
                            "description": "작업 목록"
                        },
                        "splitDetails": {
                            "type": "string",
                            "description": "작업 분할 세부 정보 (선택)"
                        }
                    }
                },
                "function": self._mcp_request_planning
            },
            
            {
                "name": "get_next_task",
                "description": "다음 실행 가능한 작업을 가져옵니다.",
                "parameters": {
                    "type": "object",
                    "required": ["requestId", "agentId"],
                    "properties": {
                        "requestId": {
                            "type": "string",
                            "description": "요청 ID"
                        },
                        "agentId": {
                            "type": "string",
                            "description": "작업을 요청하는 에이전트 ID"
                        }
                    }
                },
                "function": self._mcp_get_next_task
            },
            
            {
                "name": "mark_task_done",
                "description": "작업을 완료 처리합니다.",
                "parameters": {
                    "type": "object",
                    "required": ["requestId", "taskId", "agentId"],
                    "properties": {
                        "requestId": {
                            "type": "string",
                            "description": "요청 ID"
                        },
                        "taskId": {
                            "type": "string",
                            "description": "작업 ID"
                        },
                        "agentId": {
                            "type": "string",
                            "description": "작업을 완료한 에이전트 ID"
                        },
                        "completedDetails": {
                            "type": "string",
                            "description": "완료 세부 정보 (선택)"
                        }
                    }
                },
                "function": self._mcp_mark_task_done
            },
            
            {
                "name": "approve_task_completion",
                "description": "작업 완료를 승인합니다.",
                "parameters": {
                    "type": "object",
                    "required": ["requestId", "taskId"],
                    "properties": {
                        "requestId": {
                            "type": "string",
                            "description": "요청 ID"
                        },
                        "taskId": {
                            "type": "string",
                            "description": "작업 ID"
                        }
                    }
                },
                "function": self._mcp_approve_task_completion
            },
            
            {
                "name": "approve_request_completion",
                "description": "요청 완료를 승인합니다.",
                "parameters": {
                    "type": "object",
                    "required": ["requestId"],
                    "properties": {
                        "requestId": {
                            "type": "string",
                            "description": "요청 ID"
                        }
                    }
                },
                "function": self._mcp_approve_request_completion
            },
            
            {
                "name": "open_task_details",
                "description": "작업 세부 정보를 조회합니다.",
                "parameters": {
                    "type": "object",
                    "required": ["taskId"],
                    "properties": {
                        "taskId": {
                            "type": "string",
                            "description": "작업 ID"
                        }
                    }
                },
                "function": self._mcp_open_task_details
            },
            
            {
                "name": "list_requests",
                "description": "모든 요청 목록을 조회합니다.",
                "parameters": {
                    "type": "object",
                    "required": ["random_string"],
                    "properties": {
                        "random_string": {
                            "type": "string",
                            "description": "무작위 문자열 (파라미터 없는 도구용)"
                        }
                    }
                },
                "function": self._mcp_list_requests
            },
            
            {
                "name": "add_tasks_to_request",
                "description": "기존 요청에 작업을 추가합니다.",
                "parameters": {
                    "type": "object",
                    "required": ["requestId", "tasks"],
                    "properties": {
                        "requestId": {
                            "type": "string",
                            "description": "요청 ID"
                        },
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["title", "description"],
                                "properties": {
                                    "title": {"type": "string"},
                                    "description": {"type": "string"}
                                }
                            },
                            "description": "작업 목록"
                        }
                    }
                },
                "function": self._mcp_add_tasks_to_request
            },
            
            {
                "name": "update_task",
                "description": "작업 정보를 업데이트합니다.",
                "parameters": {
                    "type": "object",
                    "required": ["requestId", "taskId"],
                    "properties": {
                        "requestId": {
                            "type": "string",
                            "description": "요청 ID"
                        },
                        "taskId": {
                            "type": "string",
                            "description": "작업 ID"
                        },
                        "title": {
                            "type": "string",
                            "description": "작업 제목 (선택)"
                        },
                        "description": {
                            "type": "string",
                            "description": "작업 설명 (선택)"
                        }
                    }
                },
                "function": self._mcp_update_task
            },
            
            {
                "name": "delete_task",
                "description": "작업을 삭제합니다.",
                "parameters": {
                    "type": "object",
                    "required": ["requestId", "taskId"],
                    "properties": {
                        "requestId": {
                            "type": "string",
                            "description": "요청 ID"
                        },
                        "taskId": {
                            "type": "string",
                            "description": "작업 ID"
                        }
                    }
                },
                "function": self._mcp_delete_task
            },
            {
                "name": "clear_all_data",
                "description": "모든 요청 및 태스크 데이터를 초기화합니다. (테스트용)",
                "parameters": {
                    "type": "object",
                    "required": ["confirmation"], # 의도하지 않은 실행 방지를 위해 간단한 확인 파라미터 추가
                    "properties": {
                        "confirmation": {
                            "type": "string",
                            "description": "데이터 삭제를 확인하려면 \"CLEAR_ALL_MY_DATA\"를 입력하세요."
                        }
                    }
                },
                "function": self._mcp_clear_all_data
            }
        ]
        
        return tools
    
    def _add_mcp_endpoints(self) -> None:
        """
        MCP 서버 엔드포인트를 API 앱에 추가합니다.
        """
        @self.api_app.post("/mcp/invoke")
        async def invoke_mcp_tool(request: Request) -> Response:
            try:
                body = await request.json()
                tool_name = body.get("name")
                parameters = body.get("parameters", {})
                
                # MCP 도구 호출
                result = await self.mcp_server.invoke_tool(tool_name, parameters)
                return JSONResponse(content=result)
            except Exception as e:
                logger.error(f"MCP 도구 호출 중 오류 발생: {str(e)}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"error": str(e)}
                )
        
        @self.api_app.get("/mcp/tools")
        async def get_mcp_tools() -> Response:
            try:
                tools = self.mcp_server.get_tools()
                return JSONResponse(content={"tools": tools})
            except Exception as e:
                logger.error(f"MCP 도구 목록 조회 중 오류 발생: {str(e)}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"error": str(e)}
                )
    
    # MCP 도구 구현
    async def _mcp_register_agent(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        에이전트를 등록하는 MCP 도구 구현
        
        Args:
            parameters: 파라미터
            
        Returns:
            Dict[str, Any]: 결과
        """
        try:
            agent_type = parameters.get("agent_type")
            capabilities = parameters.get("capabilities", [])
            
            # 에이전트 팩토리 초기화
            agent_factory = AgentFactory()
            
            # 실제 에이전트 인스턴스 생성
            agent_instance = agent_factory.create_agent(
                agent_type=agent_type,
                ollama_model="llama3:latest",
                use_mcp=True
            )
            
            # 에이전트 인스턴스가 None이면 에러 반환
            if agent_instance is None:
                logger.error(f"에이전트 인스턴스 생성 실패: {agent_type}")
                return {"success": False, "error": f"에이전트 인스턴스 생성 실패: {agent_type}"}
            
            # 에이전트 등록
            agent_id = self.agent_coordinator.register_agent(
                agent_type=agent_type,
                agent_instance=agent_instance,
                capabilities=capabilities
            )
            
            # 에이전트 토큰 생성
            token = self.auth_manager.create_agent_token(agent_id, agent_type, capabilities)
            
            return {
                "success": True,
                "agent_id": agent_id,
                "agent_type": agent_type,
                "token": token
            }
        except Exception as e:
            logger.error(f"에이전트 등록 중 오류 발생: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _mcp_request_planning(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """새 요청을 계획하고 작업을 생성합니다. (DB 사용 버전)"""
        try:
            logger.info(f"MCP API _mcp_request_planning 호출됨 (DB 사용): params={parameters}")
            
            original_request_content = parameters.get("originalRequest")
            tasks_data = parameters.get("tasks")
            project_name_param = parameters.get("projectName")

            if not original_request_content:
                raise ValueError("Original request content (originalRequest) is required.")
            if not tasks_data or not isinstance(tasks_data, list):
                raise ValueError("Tasks list (tasks) is required and must be an array.")

            project_id_param = parameters.get("projectId")

            if project_id_param:
                project_id = project_id_param
                if not db_manager.get_project(project_id):
                    project_name = project_name_param if project_name_param else f"Project for request {datetime.now().strftime('%Y%m%d%H%M%S')}"
                    created_project_id = db_manager.add_project(project_id=project_id, project_name=project_name)
                    if not created_project_id:
                        raise HTTPException(status_code=500, detail=f"Failed to initialize project in DB with ID: {project_id}")
                else:
                    created_project_id = project_id
            else:
                project_id = f"proj_{uuid.uuid4().hex[:8]}"
                project_name = project_name_param if project_name_param else f"Project for request {datetime.now().strftime('%Y%m%d%H%M%S')}"
                created_project_id = db_manager.add_project(project_id=project_id, project_name=project_name)
                if not created_project_id:
                    raise HTTPException(status_code=500, detail=f"Failed to initialize new project in DB for ID: {project_id}")

            logger.info(f"Project (ID: {created_project_id}) ready in ProjectMasterDB via MCP API.")

            created_task_ids = []
            for i, task_data in enumerate(tasks_data):
                if not isinstance(task_data, dict):
                    task_data = dict(task_data)

                task_title = task_data.get("title")
                if not task_title:
                    raise ValueError(f"Task at index {i} is missing a 'title'.")

                task_id = task_data.get("id") or task_data.get("task_id") or f"task_{uuid.uuid4().hex[:10]}"
                description = task_data.get("description")
                status = task_data.get("status", 'pending')
                assigned_to = task_data.get("assigned_to") or task_data.get("assigned_to_agent_type")
                dependencies = task_data.get("dependencies")

                db_task_id_returned = db_manager.add_master_task(
                    task_id=task_id,
                    project_id=created_project_id,
                    title=task_title,
                    description=description,
                    status=status,
                    assigned_to_agent_type=assigned_to,
                    dependencies=dependencies
                )
                if not db_task_id_returned:
                    logger.error(f"MCP API: Failed to add task '{task_title}' (ID: {task_id}) to DB.")
                else:
                    created_task_ids.append(db_task_id_returned)
            
            logger.info(f"MCP API: All tasks processed for project {created_project_id}. Tasks added/updated: {len(created_task_ids)}")
            return {
                "message": "Planning request processed successfully via MCP API (DB).",
                "project_id": created_project_id,
                "task_ids": created_task_ids,
            }

        except ValueError as ve:
            logger.error(f"ValueError in MCP API _mcp_request_planning: {str(ve)}")
            # 클라이언트에게는 일반적인 오류 메시지 또는 Pydantic 모델을 통한 오류 응답 반환이 더 적절할 수 있음
            return {"success": False, "error": str(ve), "details": "Invalid input parameters."}
        except HTTPException as he: # FastAPI의 HTTPException은 그대로 re-raise
            raise he
        except Exception as e:
            logger.error(f"Unexpected error in MCP API _mcp_request_planning: {str(e)}", exc_info=True)
            # 프로덕션에서는 상세 오류를 클라이언트에게 노출하지 않는 것이 좋음
            return {"success": False, "error": "An unexpected server error occurred during planning.", "details": str(e)}

    def _create_progress_table_from_task_manager_details(self, tasks_details: List[Dict[str, Any]]) -> str:
        """
        task_manager._get_tasks_progress()가 반환하는 상세 태스크 목록을 기반으로
        진행 상황 테이블을 생성합니다.
        
        Args:
            tasks_details: 태스크 상세 정보 목록
            
        Returns:
            str: 마크다운 형식의 진행 상황 테이블
        """
        if not tasks_details:
            return "진행 중인 태스크가 없습니다."
        
        # 헤더: ID, 제목, 상태, 승인
        table = "| # | ID | 작업 제목 | 상태 | 승인 |\\n"
        table += "|---|----|-----------|------|------|\\n"
        
        status_map = {
            "PENDING": "⏳ 대기 중",
            "DONE": "✅ 완료됨",
            "COMPLETED": "✅ 완료됨", # task_manager 내부 상태와 맞춤
            # 필요한 다른 상태들 추가
        }
        
        for i, task_info in enumerate(tasks_details):
            task_id_short = task_info.get("id", "N/A")[:8] # ID 일부만 표시
            title = task_info.get("title", "제목 없음")
            status_raw = task_info.get("status", "UNKNOWN")
            status_text = status_map.get(status_raw, status_raw)
            approved_text = "✓" if task_info.get("approved") else "✗"
            
            table += f"| {i+1} | {task_id_short} | {title} | {status_text} | {approved_text} |\\n"
        
        return table
            
    async def _mcp_list_requests(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        모든 요청 목록을 조회합니다. (task_manager 사용)
        
        Args:
            parameters: 파라미터 (현재 사용 안함, random_string은 무시)
            
        Returns:
            Dict[str, Any]: 응답
        """
        logger.info(f"MCP list_requests 호출됨 (API, task_manager 사용)")
        
        try:
            # global_task_manager (pmagent.task_manager.task_manager) 사용
            # task_manager.list_requests()는 {"requests": requests_list} 형태를 반환
            result = global_task_manager.list_requests()
            
            # 성공 여부 필드 추가
            response_data = {
                "success": True,
                "requests": result.get("requests", []),
                "count": len(result.get("requests", []))
            }
            return response_data
        
        except Exception as e:
            logger.error(f"MCP list_requests (API) 중 예상치 못한 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}", "requests": [], "count": 0}
    
    async def _mcp_get_next_task(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """MCP: 다음 실행 가능한 작업을 가져옵니다."""
        try:
            request_id = parameters.get("requestId")
            agent_id = parameters.get("agentId") # agentId 가져오기
            
            if not request_id:
                return {"success": False, "error": "requestId 파라미터가 필요합니다."}
            if not agent_id: # agentId 확인
                return {"success": False, "error": "agentId 파라미터가 필요합니다."}
            
            # TaskManager의 get_next_task 호출 (agent_id 전달)
            result = global_task_manager.get_next_task(request_id=request_id, agent_id=agent_id)
            
            # 결과에 프로그레스 테이블 추가
            if result.get("success") and result.get("tasksProgress"):
                table = self._create_progress_table_from_task_manager_details(result["tasksProgress"])
                result["progressTable"] = table
            elif result.get("success") and result.get("message") == "No assignable task found for this request.":
                # 할당할 작업이 없는 경우에도 tasksProgress는 반환됨
                if result.get("tasksProgress"):
                    table = self._create_progress_table_from_task_manager_details(result["tasksProgress"])
                    result["progressTable"] = table
                else:
                    result["progressTable"] = "진행 중인 태스크가 없습니다."

            return result
        except ValueError as ve:
            logger.error(f"get_next_task 처리 중 ValueError: {str(ve)}")
            return {"success": False, "error": str(ve)}
        except Exception as e:
            logger.error(f"get_next_task 처리 중 예외 발생: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": f"다음 작업 가져오기 실패: {str(e)}"}
    
    async def _mcp_mark_task_done(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        작업을 완료 처리하는 MCP 도구 구현 (task_manager 사용)
        
        Args:
            parameters: 파라미터 (requestId, taskId, agentId, completedDetails? 포함)
            
        Returns:
            Dict[str, Any]: 결과
        """
        logger.info(f"MCP mark_task_done 호출됨 (API, task_manager 사용): {parameters}")
        request_id = parameters.get("requestId")
        task_id = parameters.get("taskId")
        agent_id = parameters.get("agentId") # agentId 가져오기
        completed_details = parameters.get("completedDetails")

        if not request_id or not task_id or not agent_id: # agentId 확인 추가
            missing_params = []
            if not request_id: missing_params.append("requestId")
            if not task_id: missing_params.append("taskId")
            if not agent_id: missing_params.append("agentId")
            return {"success": False, "error": f"{', '.join(missing_params)} 파라미터가 필요합니다."}

        try:
            # global_task_manager 사용
            result = global_task_manager.mark_task_done(
                request_id=request_id,
                task_id=task_id,
                agent_id=agent_id, # agentId 전달
                completed_details=completed_details
            )
            
            response_data = {"success": result.get("success", False)}
            response_data.update(result)
            
            # progressTable 생성 (tasksProgress 기반)
            tasks_progress_details = result.get("tasksProgress", [])
            progress_table_str = self._create_progress_table_from_task_manager_details(tasks_progress_details)
            response_data["progressTable"] = progress_table_str
            
            # task_manager가 반환하는 success 필드가 이미 있으므로 별도 처리 필요 없음.
            # 실패 시 message 필드도 task_manager가 제공.

            return response_data

        except ValueError as ve: # task_manager에서 발생할 수 있는 유효성 오류
            logger.error(f"MCP mark_task_done (API) 중 ValueError: {str(ve)}")
            empty_progress_table = self._create_progress_table_from_task_manager_details([])
            return {"success": False, "error": str(ve), "progressTable": empty_progress_table}
        except Exception as e:
            logger.error(f"MCP mark_task_done (API) 중 예상치 못한 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            empty_progress_table = self._create_progress_table_from_task_manager_details([])
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}", "progressTable": empty_progress_table}
    
    async def _mcp_approve_task_completion(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        작업 완료를 승인하는 MCP 도구 구현 (task_manager 사용)
        
        Args:
            parameters: 파라미터 (requestId, taskId 포함)
            
        Returns:
            Dict[str, Any]: 결과
        """
        logger.info(f"MCP approve_task_completion 호출됨 (API, task_manager 사용): {parameters}")
        request_id = parameters.get("requestId")
        task_id = parameters.get("taskId")

        if not request_id or not task_id:
            return {"success": False, "error": "requestId and taskId are required."}

        try:
            # global_task_manager 사용
            # task_manager.approve_task_completion() 반환 값:
            # {
            #     "success": True/False,
            #     "message": "...",
            #     "task": updated_task, (있을 경우)
            #     "tasksProgress": tasks_info (List[Dict])
            # }
            result = global_task_manager.approve_task_completion(
                request_id=request_id,
                task_id=task_id
            )
            
            response_data = {"success": result.get("success", False)}
            response_data.update(result)
            
            tasks_progress_details = result.get("tasksProgress", [])
            progress_table_str = self._create_progress_table_from_task_manager_details(tasks_progress_details)
            response_data["progressTable"] = progress_table_str
            
            return response_data

        except ValueError as ve:
            logger.error(f"MCP approve_task_completion (API) 중 ValueError: {str(ve)}")
            empty_progress_table = self._create_progress_table_from_task_manager_details([])
            return {"success": False, "error": str(ve), "progressTable": empty_progress_table}
        except Exception as e:
            logger.error(f"MCP approve_task_completion (API) 중 예상치 못한 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            empty_progress_table = self._create_progress_table_from_task_manager_details([])
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}", "progressTable": empty_progress_table}
    
    async def _mcp_approve_request_completion(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        요청 완료를 승인하는 MCP 도구 구현 (task_manager 사용)
        
        Args:
            parameters: 파라미터 (requestId 포함)
            
        Returns:
            Dict[str, Any]: 결과
        """
        logger.info(f"MCP approve_request_completion 호출됨 (API, task_manager 사용): {parameters}")
        request_id = parameters.get("requestId")

        if not request_id:
            return {"success": False, "error": "requestId is required."}

        try:
            # global_task_manager 사용
            # task_manager.approve_request_completion() 반환 값:
            # {
            #     "success": True/False,
            #     "message": "...",
            #     "request": updated_request, (있을 경우, 거의 없음)
            #     "tasksProgress": tasks_info (List[Dict])
            # }
            result = global_task_manager.approve_request_completion(request_id)
            
            response_data = {"success": result.get("success", False)}
            response_data.update(result)
            
            tasks_progress_details = result.get("tasksProgress", [])
            progress_table_str = self._create_progress_table_from_task_manager_details(tasks_progress_details)
            response_data["progressTable"] = progress_table_str
            
            return response_data

        except ValueError as ve:
            logger.error(f"MCP approve_request_completion (API) 중 ValueError: {str(ve)}")
            empty_progress_table = self._create_progress_table_from_task_manager_details([])
            return {"success": False, "error": str(ve), "progressTable": empty_progress_table}
        except Exception as e:
            logger.error(f"MCP approve_request_completion (API) 중 예상치 못한 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            empty_progress_table = self._create_progress_table_from_task_manager_details([])
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}", "progressTable": empty_progress_table}
    
    async def _mcp_open_task_details(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        작업 세부 정보를 조회하는 MCP 도구 구현 (task_manager 사용)
        
        Args:
            parameters: 파라미터 (taskId 포함)
            
        Returns:
            Dict[str, Any]: 결과 ({"success": True/False, "task": task_details} 또는 {"success": False, "error": ...})
        """
        logger.info(f"MCP open_task_details 호출됨 (API, task_manager 사용): {parameters}")
        task_id = parameters.get("taskId")

        if not task_id:
            return {"success": False, "error": "taskId is required."}

        try:
            # global_task_manager 사용
            # task_manager.open_task_details()는 태스크 객체 또는 ValueError 발생
            task_details = global_task_manager.open_task_details(task_id)
            return {"success": True, "task": task_details.get("task")}
        
        except ValueError as ve: # task_manager에서 태스크를 찾지 못하면 ValueError 발생
            logger.warning(f"MCP open_task_details (API) 중 ValueError: {str(ve)}")
            return {"success": False, "error": str(ve)}
        except Exception as e:
            logger.error(f"MCP open_task_details (API) 중 예상치 못한 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}
    
    async def _mcp_add_tasks_to_request(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        요청에 작업을 추가하는 MCP 도구 구현 (task_manager 사용)
        
        Args:
            parameters: 파라미터 (requestId, tasks 포함)
            
        Returns:
            Dict[str, Any]: 결과
        """
        logger.info(f"MCP add_tasks_to_request 호출됨 (API, task_manager 사용): {parameters}")
        request_id = parameters.get("requestId")
        tasks_data = parameters.get("tasks", [])

        if not request_id:
            return {"success": False, "error": "requestId is required."}
        if not isinstance(tasks_data, list) or not tasks_data:
            return {"success": False, "error": "tasks must be a non-empty list."}

        # 태스크 유효성 검사 (request_planning과 유사하게)
        validated_tasks = []
        for i, task_param in enumerate(tasks_data):
            if not isinstance(task_param, dict):
                try: task_param = dict(task_param)
                except: return {"success": False, "error": f"Task #{i} is not a valid dictionary-like object."}
            
            if "title" not in task_param or "description" not in task_param:
                return {"success": False, "error": f"Task #{i} must have title and description."}
            validated_tasks.append({
                "title": str(task_param["title"]),
                "description": str(task_param["description"])
            })

        try:
            # global_task_manager 사용
            # task_manager.add_tasks_to_request() 반환 값:
            # {
            #     "success": True/False,
            #     "message": "...",
            #     "addedTasks": added_tasks_details (List[Dict]),
            #     "tasksProgress": tasks_info (List[Dict])
            # }
            result = global_task_manager.add_tasks_to_request(
                request_id=request_id,
                tasks=validated_tasks
            )
            
            response_data = {"success": result.get("success", False)}
            response_data.update(result)
            
            tasks_progress_details = result.get("tasksProgress", [])
            progress_table_str = self._create_progress_table_from_task_manager_details(tasks_progress_details)
            response_data["progressTable"] = progress_table_str
            
            return response_data

        except ValueError as ve:
            logger.error(f"MCP add_tasks_to_request (API) 중 ValueError: {str(ve)}")
            empty_progress_table = self._create_progress_table_from_task_manager_details([])
            return {"success": False, "error": str(ve), "progressTable": empty_progress_table}
        except Exception as e:
            logger.error(f"MCP add_tasks_to_request (API) 중 예상치 못한 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            empty_progress_table = self._create_progress_table_from_task_manager_details([])
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}", "progressTable": empty_progress_table}
    
    async def _mcp_update_task(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        작업 정보를 업데이트하는 MCP 도구 구현 (task_manager 사용)
        
        Args:
            parameters: 파라미터 (requestId, taskId, title?, description? 포함)
            
        Returns:
            Dict[str, Any]: 결과
        """
        logger.info(f"MCP update_task 호출됨 (API, task_manager 사용): {parameters}")
        request_id = parameters.get("requestId")
        task_id = parameters.get("taskId")
        title = parameters.get("title") # Optional
        description = parameters.get("description") # Optional

        if not request_id or not task_id:
            return {"success": False, "error": "requestId and taskId are required."}
        
        # 업데이트할 내용이 있는지 확인 (둘 다 None이면 업데이트할 필요 없음)
        if title is None and description is None:
            # task_manager.update_task가 이를 처리하므로, 그대로 전달해도 됨.
            # 여기서는 API 레벨에서 빠른 반환을 원하면 추가 가능.
            # return {"success": False, "error": "Nothing to update. Provide title or description."}
            pass

        try:
            # global_task_manager 사용
            # task_manager.update_task() 반환 값:
            # {
            #     "success": True/False,
            #     "message": "...",
            #     "task": updated_task, (있을 경우)
            #     "tasksProgress": tasks_info (List[Dict])
            # }
            result = global_task_manager.update_task(
                request_id=request_id,
                task_id=task_id,
                title=title,
                description=description
            )
            
            response_data = {"success": result.get("success", False)}
            response_data.update(result)
            
            tasks_progress_details = result.get("tasksProgress", [])
            progress_table_str = self._create_progress_table_from_task_manager_details(tasks_progress_details)
            response_data["progressTable"] = progress_table_str
            
            return response_data

        except ValueError as ve:
            logger.error(f"MCP update_task (API) 중 ValueError: {str(ve)}")
            # task_manager.update_task는 tasksProgress를 반환하므로, 실패 시에도 progressTable 제공 시도
            current_progress = global_task_manager._get_tasks_progress(request_id) 
            empty_progress_table = self._create_progress_table_from_task_manager_details(current_progress)
            return {"success": False, "error": str(ve), "progressTable": empty_progress_table}
        except Exception as e:
            logger.error(f"MCP update_task (API) 중 예상치 못한 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # 요청 ID가 있다면 현재 진행 상황이라도 보여주도록 시도
            progress_table_on_error = "Error generating progress table."
            if request_id:
                try:
                    current_progress_on_error = global_task_manager._get_tasks_progress(request_id)
                    progress_table_on_error = self._create_progress_table_from_task_manager_details(current_progress_on_error)
                except: pass # 실패 시 그냥 기본 오류 메시지 사용
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}", "progressTable": progress_table_on_error}
    
    async def _mcp_delete_task(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        작업을 삭제하는 MCP 도구 구현 (task_manager 사용)
        
        Args:
            parameters: 파라미터 (requestId, taskId 포함)
            
        Returns:
            Dict[str, Any]: 결과
        """
        logger.info(f"MCP delete_task 호출됨 (API, task_manager 사용): {parameters}")
        request_id = parameters.get("requestId")
        task_id = parameters.get("taskId")

        if not request_id or not task_id:
            return {"success": False, "error": "requestId and taskId are required."}

        try:
            # global_task_manager 사용
            # task_manager.delete_task() 반환 값:
            # {
            #     "success": True/False,
            #     "message": "...",
            #     "tasksProgress": tasks_info (List[Dict])
            # }
            result = global_task_manager.delete_task(
                request_id=request_id,
                task_id=task_id
            )
            
            response_data = {"success": result.get("success", False)}
            response_data.update(result)
            
            tasks_progress_details = result.get("tasksProgress", [])
            progress_table_str = self._create_progress_table_from_task_manager_details(tasks_progress_details)
            response_data["progressTable"] = progress_table_str
            
            return response_data

        except ValueError as ve:
            logger.error(f"MCP delete_task (API) 중 ValueError: {str(ve)}")
            current_progress = global_task_manager._get_tasks_progress(request_id)
            empty_progress_table = self._create_progress_table_from_task_manager_details(current_progress)
            return {"success": False, "error": str(ve), "progressTable": empty_progress_table}
        except Exception as e:
            logger.error(f"MCP delete_task (API) 중 예상치 못한 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            progress_table_on_error = "Error generating progress table."
            if request_id:
                try:
                    current_progress_on_error = global_task_manager._get_tasks_progress(request_id)
                    progress_table_on_error = self._create_progress_table_from_task_manager_details(current_progress_on_error)
                except: pass
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}", "progressTable": progress_table_on_error}
    
    async def _mcp_clear_all_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """모든 요청 및 태스크 데이터를 초기화하는 MCP 도구 구현 (task_manager 사용)"""
        logger.info(f"MCP clear_all_data 호출됨 (API, task_manager 사용): {parameters}")
        confirmation = parameters.get("confirmation")

        required_confirmation_string = "CLEAR_ALL_MY_DATA"
        if confirmation != required_confirmation_string:
            logger.warning("데이터 초기화 확인 문자열이 일치하지 않아 작업을 취소합니다.")
            return {
                "success": False, 
                "error": f"Confirmation string mismatch. Please provide \"{required_confirmation_string}\" to confirm data deletion."
            }

        try:
            result = global_task_manager.clear_all_data()
            return result # task_manager.clear_all_data()가 반환하는 success/error 메시지 그대로 사용
        except Exception as e:
            logger.error(f"MCP clear_all_data (API) 중 예상치 못한 오류: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": f"An unexpected error occurred while clearing data: {str(e)}"}
    
    def _create_progress_table(self, request_info: Dict[str, Any]) -> str:
        """
        진행 상황 테이블을 생성합니다. (이 함수는 이제 직접 사용되지 않음, 
        _create_progress_table_from_task_manager_details 로 대체됨)
        
        Args:
            request_info: 요청 정보
            
        Returns:
            str: 마크다운 형식의 진행 상황 테이블
        """
        # 헤더
        # ... (이전 로직, 현재는 사용 안 함)
        logger.warning("_create_progress_table is deprecated and should not be called directly.")
        # 대신 task_manager의 tasksProgress를 사용하는 새 함수를 사용해야 함
        # 예시로 비워두거나, tasksProgress를 받는 형태로 수정할 수 있으나, 이미 새 함수가 있음.
        tasks_details = []
        if "tasks" in request_info and isinstance(request_info["tasks"], list):
            for task_item in request_info["tasks"]:
                if isinstance(task_item, str): # task_id만 있는 경우
                    task_detail = global_task_manager.tasks.get(task_item) # 직접 접근은 지양해야하나, 예시용
                    if task_detail: tasks_details.append(task_detail)
                elif isinstance(task_item, dict): # task 객체가 있는 경우
                    tasks_details.append(task_item)
        return self._create_progress_table_from_task_manager_details(tasks_details)
    
    def start(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
        """
        API 서버를 시작합니다.
        
        Args:
            host: 호스트 (기본값: "0.0.0.0")
            port: 포트 (기본값: 8000)
            reload: 리로드 여부 (기본값: False)
        """
        uvicorn.run(self.api_app, host=host, port=port, reload=reload)

def create_mcp_api(config: Optional[Dict[str, Any]] = None) -> PMAgentMCPAPI:
    """
    MCP API 인스턴스를 생성합니다.
    
    Args:
        config: 설정 (기본값: None)
        
    Returns:
        PMAgentMCPAPI: MCP API 인스턴스
    """
    return PMAgentMCPAPI(config) 