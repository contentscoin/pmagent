"""
Ollama API를 활용한 PM(Project Manager) 에이전트 모듈

이 모듈은 프로젝트 관리 에이전트를 제공하여 다양한 전문 에이전트들(디자이너, 프론트엔드, 백엔드, AI 엔지니어)을
조율하고 작업을 관리하는 기능을 제공합니다.
"""

import os
import json
import time
import random
import requests
import logging
import uuid  # 에이전트 ID 기본값 생성용
from typing import Dict, List, Optional, Any, Union, Tuple
import re # 추가 (JSON 파싱용)
from datetime import datetime
import sys

# MCP Agent Helper 가져오기 (사용 가능한 경우)
try:
    from .mcp_agent_helper import MCPAgentHelper
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class PMAgentOllama(BaseTool):
    """
    Ollama API를 사용하는 PM(Project Manager) 에이전트
    
    다양한 전문 에이전트들을 조율하고 작업을 관리하는 중앙 코디네이터 역할을 수행합니다.
    - 작업 계획 수립 및 분배
    - 작업 진행 상황 추적
    - 작업 실행 승인
    - 에이전트 간 조율
    - 사용자와의 소통 창구
    """
    
    name = "pm_agent_ollama"
    description = "Ollama 기반 PM Agent - 프로젝트 관리 및 에이전트 조율"
    
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, 
                 model: str = "llama3.2:latest", use_mcp: bool = False, 
                 mcp_helper: Optional[Any] = None, agent_id: Optional[str] = None,
                 mcp_server_url: str = "http://localhost:8083/mcp/invoke", **kwargs):
        """
        Ollama 기반 PM Agent 초기화
        
        Args:
            api_key: 사용되지 않음 (Ollama 호환성 유지용)
            api_base: Ollama API 기본 URL
            model: 사용할 Ollama 모델명
            use_mcp: MCP(Model Context Protocol) 사용 여부
            mcp_helper: MCPAgentHelper 인스턴스
            agent_id: 에이전트의 고유 ID (없으면 생성)
            mcp_server_url: PMAgent MCP 서버의 invoke 엔드포인트 URL
        """
        # API 설정
        self.api_key = api_key  # Ollama는 API 키를 사용하지 않지만 호환성을 위해 유지
        self.api_base = api_base or os.environ.get("OLLAMA_API_BASE", "http://localhost:11434/api")
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.2:latest")
        
        self.agent_id = agent_id or f"pm-agent-{uuid.uuid4().hex[:7]}" # Agent ID 길이 약간 줄임
        self.mcp_server_url = mcp_server_url
        
        # MCP 설정
        self.use_mcp = use_mcp
        self.mcp_helper = mcp_helper
        
        # 현재 작업 중인 프로젝트 정보
        self.current_project_id: Optional[str] = None
        self.current_project_name: Optional[str] = None
        
        # 등록된 에이전트 (나중에 자동으로 채워질 것임)
        self.agents = {
            "designer": None,
            "frontend": None,
            "backend": None,
            "ai_engineer": None
        }
        
        # 프로젝트 상태 관리
        self.project_status = {
            "tasks": [],
            "completed_tasks": [],
            "pending_approvals": [],
            "agent_status": {
                "designer": "idle",
                "frontend": "idle",
                "backend": "idle",
                "ai_engineer": "idle"
            }
        }
        
        # 모델 가용성 확인
        self._check_model_availability()
        
        # 작업 기록
        self.task_history = []
    
    def register_agent(self, agent_type: str, agent_instance: Any) -> None:
        """
        에이전트 등록
        
        Args:
            agent_type: 에이전트 유형 (designer, frontend, backend, ai_engineer)
            agent_instance: 에이전트 인스턴스
        """
        if agent_type in self.agents:
            self.agents[agent_type] = agent_instance
            logger.info(f"{agent_type.capitalize()} 에이전트 등록 완료")
        else:
            logger.warning(f"알 수 없는 에이전트 유형: {agent_type}")
    
    def get_available_models(self) -> List[str]:
        """
        Ollama에서 사용 가능한 모델 목록을 가져옵니다.
        
        Returns:
            List[str]: 사용 가능한 모델 목록
        """
        try:
            url = f"{self.api_base.rstrip('/')}/tags"
            response = requests.get(url)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [model.get("name") for model in models]
        except Exception as e:
            logger.error(f"모델 목록을 가져오는 중 오류 발생: {str(e)}")
            return []
    
    def _check_model_availability(self):
        """
        선택한 Ollama 모델이 사용 가능한지 확인합니다.
        
        Returns:
            bool: 모델이 사용 가능하면 True, 아니면 False
        """
        models = self.get_available_models()
        
        if not models:
            print("⚠️ 사용 가능한 모델이 없습니다. Ollama가 실행 중인지 확인하세요.")
            return False
            
        if self.model in models:
            print(f"✅ 모델 '{self.model}'이(가) 사용 가능합니다.")
            return True
        else:
            print(f"⚠️ 모델 '{self.model}'을(를) 찾을 수 없습니다.")
            
            # llama3.2 또는 llama3 관련 모델이 있는지 확인
            llama3_models = [m for m in models if "llama3" in m.lower()]
            if llama3_models:
                recommended = llama3_models[0]
                print(f"💡 대체 모델로 '{recommended}'을(를) 사용해 보세요.")
                print(f"   명령어: ollama pull {recommended}")
            else:
                print("💡 다음 명령어로 필요한 모델을 다운로드하세요:")
                print("   ollama pull llama3.2:latest")
                
            return False
    
    def _call_ollama_api(self, prompt: str, system_prompt: Optional[str] = None, 
                         temperature: float = 0.7, max_tokens: int = 2048) -> Optional[str]:
        """
        Ollama API 호출 (스트림을 False로 명시적으로 설정하여 단일 응답을 받도록 시도)
        
        Args:
            prompt: 프롬프트 텍스트
            system_prompt: 시스템 프롬프트 (지시사항)
            temperature: 온도 (창의성 조절)
            max_tokens: 최대 토큰 수
            
        Returns:
            Optional[str]: API 응답 텍스트 (성공 시), None (실패 시)
        """
        url = f"{self.api_base.rstrip('/')}/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False,
            "options": {
                "num_predict": max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            logger.debug(f"Calling Ollama API. URL: {url}, Payload: {payload}")
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            # 응답이 성공적인지 확인
            try:
                response_data = response.json()
                if response_data.get("done") and "response" in response_data:
                    logger.info(f"Ollama API call successful. Done: {response_data.get('done')}")
                    return response_data.get("response")
                else:
                    logger.error(f"Ollama API response format unexpected or not done. Data: {response_data}")
                    return None
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON from Ollama API response: {e}. Response text: {response.text[:500]}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Ollama API call timed out after 60 seconds.")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API call failed: {e}")
            error_detail = str(e)
            if e.response is not None:
                try:
                    error_detail += f" - Response status: {e.response.status_code}, Response text: {e.response.text[:500]}"
                except Exception:
                    pass 
            logger.error(f"Detailed error: {error_detail}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during Ollama API call: {e}", exc_info=True)
            return None
    
    def _set_current_project(self, project_id: str, project_name: str):
        """현재 작업 프로젝트 정보를 설정합니다."""
        self.current_project_id = project_id
        self.current_project_name = project_name
        logger.info(f"PMAgent current project set to: ID='{project_id}', Name='{project_name}'")

    def _generate_project_name_from_desc(self, task_desc: str, max_length: int = 50) -> str:
        """작업 설명에서 프로젝트 이름을 생성합니다 (간단한 버전)."""
        # 첫 줄 또는 처음 몇 단어를 사용할 수 있습니다.
        name = task_desc.split('\n')[0].strip()
        if len(name) > max_length:
            name = name[:max_length-3] + "..."
        if not name: # 설명이 비어있거나 매우 짧은 경우
            name = f"Project_{datetime.now().strftime('%Y%m%d_%H%M')}"
        return name

    def _run(self, task: Dict[str, Any]) -> str:
        """
        PM 에이전트의 주 실행 로직.
        주어진 태스크를 분석하고 적절한 핸들러로 라우팅합니다.
        """
        task_desc = task.get("task", "")
        if not task_desc:
            return "오류: 작업 설명이 없습니다."

        logger.info(f"PM Agent {self.agent_id} received task: '{task_desc[:100]}...'")
        
        # 프로젝트 ID 및 이름 처리 (예시: task 딕셔너리에 projectId가 올 수 있음)
        # 또는 _run이 호출되는 시점에 프로젝트 컨텍스트가 이미 설정되어 있어야 함.
        # 여기서는 _handle_planning_task가 새 프로젝트를 시작한다고 가정하고, 
        # 해당 메소드 내에서 project_id와 name을 설정하도록 함.
        # 만약 _run이 기존 프로젝트의 컨텍스트에서 실행된다면, 
        # self.current_project_id 등이 이미 설정되어 있어야 함.

        analysis_type, agent_type, processed_task_desc = self._analyze_task(task_desc)
        
        self.task_history.append({
            "timestamp": time.time(),
            "original_request": task_desc,
            "analysis_type": analysis_type,
            "agent_type": agent_type,
            "processed_task": processed_task_desc
        })

        if analysis_type == "plan":
            return self._handle_planning_task(processed_task_desc)
        # ... (다른 핸들러 호출) ...
        else: # 기본적으로 direct 또는 알 수 없는 타입
            return self._handle_direct_response(processed_task_desc)
    
    def _analyze_task(self, task_desc: str) -> Tuple[str, Optional[str], str]:
        """
        작업 설명을 분석하여 작업 유형과 관련 에이전트 추출
        
        Args:
            task_desc: 작업 설명
            
        Returns:
            Tuple[str, Optional[str], str]: (작업 유형, 에이전트 유형, 세부 정보)
                작업 유형: 'plan', 'delegate', 'status', 'approve', 'direct'
                에이전트 유형: 'designer', 'frontend', 'backend', 'ai_engineer', None
                세부 정보: 추가 작업 정보
        """
        task_desc_lower = task_desc.lower()
        
        # 기획/계획 작업
        if any(keyword in task_desc_lower for keyword in ["계획", "계획 수립", "기획", "프로젝트 계획", "plan", "planning"]):
            return "plan", None, task_desc
        
        # 작업 위임/할당 관련 키워드
        delegate_keywords = {
            "designer": ["디자인", "디자이너", "ui", "ux", "와이어프레임", "디자인 시스템", "컴포넌트 디자인"],
            "frontend": ["프론트엔드", "front-end", "프론트", "UI 구현", "컴포넌트 개발", "react", "vue", "angular"],
            "backend": ["백엔드", "back-end", "백", "서버", "api", "데이터베이스", "db", "서버 로직"],
            "ai_engineer": ["ai", "인공지능", "머신러닝", "ml", "딥러닝", "ai 모델", "ai 통합"]
        }
        
        # 각 에이전트 유형별 키워드 확인
        for agent_type, keywords in delegate_keywords.items():
            if any(keyword in task_desc_lower for keyword in keywords):
                return "delegate", agent_type, task_desc
        
        # 상태 확인
        if any(keyword in task_desc_lower for keyword in ["상태", "진행 상황", "진척도", "status", "progress"]):
            return "status", None, task_desc
        
        # 승인 요청
        if any(keyword in task_desc_lower for keyword in ["승인", "승인해", "approve", "confirm", "확인"]):
            return "approve", None, task_desc
        
        # 기본값: 직접 응답
        return "direct", None, task_desc
    
    def _handle_planning_task(self, task_desc: str) -> Dict[str, Any]:
        """
        프로젝트 계획 수립 작업을 처리합니다.
        이 메소드가 호출되면 새로운 프로젝트가 시작되거나 기존 프로젝트에 계획이 추가된다고 가정합니다.
        """
        # 새로운 프로젝트 계획 요청으로 간주하고, project ID와 name을 생성 또는 설정
        # 만약 이전에 설정된 current_project_id가 있다면 그것을 사용할 수도 있지만,
        # 여기서는 "계획 수립" 자체를 새 프로젝트의 시작점으로 볼 수 있음.
        # 또는, task_desc 안에 project_id에 대한 힌트가 있는지 확인하는 로직 추가 가능.
        
        # 지금은 _handle_planning_task가 호출될 때마다 새 프로젝트 ID/이름을 만들거나,
        # 외부에서 이 메소드 호출 전에 _set_current_project를 통해 설정한다고 가정.
        # 여기서는 "새로운" 계획 요청으로 보고 ID와 이름을 생성/설정합니다.
        if not self.current_project_id: # 현재 프로젝트가 설정되지 않았다면 새로 생성
            new_project_id = f"proj_{uuid.uuid4().hex[:8]}"
            new_project_name = self._generate_project_name_from_desc(task_desc)
            self._set_current_project(new_project_id, new_project_name)
            logger.info(f"New project context initiated by planning task: ID='{self.current_project_id}', Name='{self.current_project_name}'")
        else:
            logger.info(f"Planning task for existing project: ID='{self.current_project_id}', Name='{self.current_project_name}'")

        system_prompt = f"""
You are a project manager AI. Your task is to break down the given user request into a sequence of specific, actionable sub-tasks.
The user request is: '{task_desc}'
Project Name: '{self.current_project_name}' 
Project ID: '{self.current_project_id}'

You MUST follow these rules:
1.  Analyze the request and identify all necessary steps to complete it.
2.  Break it down into a list of sequential sub-tasks. Each sub-task should be a logical unit of work.
3.  For each sub-task, provide:
    *   `title`: A concise and clear title for the task (e.g., "Define User Schema", "Implement POST /api/users endpoint").
    *   `description`: A detailed description of what needs to be done for this task. Be specific.
    *   `status`: Set this to "PENDING".
    *   `assigned_to`: Based on the task nature. Examples: "BackendAgent", "FrontendAgent", "DesignerAgent", "QAAgent".
    *   `dependencies`: An optional list of task titles (strings) that this task depends on.
    *   `task_id`: (Optional but recommended) A unique identifier for this task, e.g., "task_001", "user_schema_def". If you generate it, ensure it's unique within this plan. If not provided, the server will generate one.
4.  The output MUST be a valid JSON array of task objects. Do NOT include any other text, explanations, or markdown formatting outside the JSON array.
5.  The order of tasks in the array should represent the logical sequence of execution.

Example of a valid JSON output format (note: `task_id` is optional here, if you omit it, the MCP server will generate one):
```json
[
  {{
    "task_id": "user_schema", 
    "title": "Sub-task 1 Title",
    "description": "Detailed description for sub-task 1...",
    "status": "PENDING",
    "assigned_to": "BackendAgent",
    "dependencies": []
  }},
  {{
    "title": "Sub-task 2 Title", // task_id omitted, server will generate
    "description": "Detailed description for sub-task 2, which might depend on Sub-task 1.",
    "status": "PENDING",
    "assigned_to": "BackendAgent",
    "dependencies": ["Sub-task 1 Title"]
  }}
]
```

Now, generate the JSON array of sub-tasks for the user request: '{task_desc}'
Ensure the output is ONLY the JSON array, starting with `[` and ending with `]`."""
        
        logger.info(f"Generating tasks from Ollama for request: {task_desc} (Project: {self.current_project_id})")
        
        ollama_response_text = self._call_ollama_api(prompt=system_prompt)

        if not ollama_response_text:
            # Ollama 응답 실패 시 에러 반환
            error_detail = "Ollama did not return a response for task generation."
            logger.error(error_detail)
            return {"success": False, "error": error_detail, "details": None}

        logger.info(f"Ollama raw response for task generation: {ollama_response_text[:1000]}...")

        parsed_tasks = []
        json_str_for_parsing = ""
        try:
            # 코드블록 추출
            match_code_block = re.search(r"```json\s*([\s\S]*?)\s*```", ollama_response_text)
            if match_code_block:
                json_str_for_parsing = match_code_block.group(1).strip()
            else:
                # 대괄호로 시작하는 전체 배열 추출 (캡처 그룹 1개)
                match_array = re.search(r"^\s*(\[[\s\S]*\])\s*$", ollama_response_text.strip())
                if match_array:
                    json_str_for_parsing = match_array.group(1)
                else:
                    json_str_for_parsing = ollama_response_text.strip()
            
            parsed_tasks_list = json.loads(json_str_for_parsing)
            
            if not isinstance(parsed_tasks_list, list):
                raise ValueError("Parsed JSON is not a list.")
            for i, task_item_data in enumerate(parsed_tasks_list):
                if not isinstance(task_item_data, dict):
                    raise ValueError(f"Task item at index {i} is not a dictionary: {task_item_data}")
                if not all(k in task_item_data for k in ["title", "description"]):
                     logger.warning(f"Task item at index {i} is missing 'title' or 'description': {task_item_data}")
                parsed_tasks.append(task_item_data)
            logger.info(f"Successfully parsed {len(parsed_tasks)} tasks from Ollama response.")

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse or validate JSON tasks from Ollama response: {e}")
            logger.error(f"Problematic JSON string for parsing was: '{json_str_for_parsing}'")
            return {"success": False, "error": f"JSON parsing/validation failed: {e}", "details": {"raw_ollama_response": ollama_response_text}}

        if not parsed_tasks:
            error_detail = "Task generation resulted in an empty list after parsing."
            logger.error(error_detail)
            return {"success": False, "error": error_detail, "details": {"raw_ollama_response": ollama_response_text}}

        mcp_response = self.plan_request(
            original_request_text=task_desc, 
            tasks_list=parsed_tasks,
            current_project_id=self.current_project_id,
            current_project_name=self.current_project_name
        )
        
        if mcp_response and mcp_response.get("project_id"):
            if self.current_project_id != mcp_response.get("project_id"):
                 logger.warning(f"MCP server returned a different project_id ('{mcp_response.get('project_id')}') than expected ('{self.current_project_id}'). Updating PMAgent's current project.")
                 self._set_current_project(mcp_response.get("project_id"), self.current_project_name) 

            final_project_id = mcp_response.get("project_id")
            num_tasks_processed = len(mcp_response.get("task_ids", []))

            logger.info(f"MCP Server confirmed planning. Project ID: {final_project_id}, Tasks processed: {num_tasks_processed}.")
            # 성공 응답에 success: True 추가 및 MCP 응답 전체 포함
            return {"success": True, **mcp_response} 
        else:
            error_msg = f"Failed to create/update a plan via MCP."
            logger.error(f"{error_msg} Response: {mcp_response}. Check logs.")
            # 실패 응답에 success: False 추가
            return {"success": False, "error": error_msg, "details": mcp_response}
    
    def _delegate_task(self, agent_type: str, task_desc: str, auto_approve: bool = False) -> str:
        """
        작업을 해당 전문 에이전트에게 위임합니다.
        
        Args:
            agent_type: 에이전트 유형
            task_desc: 작업 설명
            auto_approve: 자동 승인 여부
            
        Returns:
            str: 위임 결과
        """
        if not agent_type or agent_type not in self.agents or not self.agents[agent_type]:
            return f"에이전트가 등록되지 않았습니다: {agent_type}"
        
        # 에이전트 상태 업데이트
        self.project_status["agent_status"][agent_type] = "working"
        
        # 작업 ID 생성
        task_id = f"task_{len(self.project_status['tasks']) + 1}"
        
        # 작업 실행
        try:
            agent = self.agents[agent_type]
            result = agent.run_task(task_desc)
            
            # 작업 기록 및 상태 업데이트
            task_entry = {
                "id": task_id,
                "description": task_desc,
                "agent_type": agent_type,
                "status": "completed" if auto_approve else "pending_approval",
                "created_at": time.time(),
                "completed_at": time.time(),
                "result": result
            }
            
            self.project_status["tasks"].append(task_entry)
            
            if auto_approve:
                self.project_status["completed_tasks"].append(task_entry)
            else:
                self.project_status["pending_approvals"].append(task_entry)
            
            # 에이전트 상태 업데이트
            self.project_status["agent_status"][agent_type] = "idle"
            
            # 응답 생성
            if auto_approve:
                return f"{agent_type.capitalize()} 에이전트가 작업을 완료했습니다:\n\n{result[:500]}...\n\n(작업이 자동 승인되었습니다)"
            else:
                return f"{agent_type.capitalize()} 에이전트가 작업을 완료했습니다. 승인이 필요합니다:\n\n{result[:500]}...\n\n승인하려면 '작업 {task_id} 승인'이라고 말씀해주세요."
            
        except Exception as e:
            # 에러 발생 시 상태 복원
            self.project_status["agent_status"][agent_type] = "idle"
            return f"{agent_type.capitalize()} 에이전트에 작업 위임 중 오류 발생: {str(e)}"
    
    def _handle_status_request(self, task_desc: str) -> str:
        """
        프로젝트 상태 요청 처리
        
        Args:
            task_desc: 작업 설명
            
        Returns:
            str: 프로젝트 상태 보고서
        """
        total_tasks = len(self.project_status["tasks"])
        completed_tasks = len(self.project_status["completed_tasks"])
        pending_approvals = len(self.project_status["pending_approvals"])
        
        # 각 에이전트별 통계 계산
        agent_stats = {}
        for agent_type in self.agents.keys():
            agent_tasks = [t for t in self.project_status["tasks"] if t.get("agent_type") == agent_type]
            agent_completed = [t for t in self.project_status["completed_tasks"] if t.get("agent_type") == agent_type]
            
            agent_stats[agent_type] = {
                "total": len(agent_tasks),
                "completed": len(agent_completed),
                "status": self.project_status["agent_status"][agent_type]
            }
        
        # 응답 생성
        response = f"## 프로젝트 상태 보고서\n\n"
        response += f"**총 작업:** {total_tasks}개\n"
        response += f"**완료된 작업:** {completed_tasks}개\n"
        response += f"**승인 대기 중:** {pending_approvals}개\n\n"
        
        # 에이전트별 상태
        response += "### 에이전트별 상태\n\n"
        for agent_type, stats in agent_stats.items():
            agent_name = agent_type.capitalize()
            response += f"**{agent_name} 에이전트**\n"
            response += f"- 총 작업: {stats['total']}개\n"
            response += f"- 완료된 작업: {stats['completed']}개\n"
            response += f"- 현재 상태: {stats['status']}\n\n"
        
        # 승인 대기 중인 작업
        if pending_approvals > 0:
            response += "### 승인 대기 중인 작업\n\n"
            for i, task in enumerate(self.project_status["pending_approvals"][:5]):  # 최대 5개만 표시
                response += f"{i+1}. **작업 {task['id']}**: {task['description'][:50]}... ({task['agent_type']})\n"
            
            if pending_approvals > 5:
                response += f"\n외 {pending_approvals - 5}개의 작업이 승인 대기 중입니다.\n"
            
            response += "\n승인하려면 '작업 [작업ID] 승인'이라고 말씀해주세요.\n"
        
        return response
    
    def _handle_approval_request(self, task_desc: str) -> str:
        """
        작업 승인 요청 처리
        
        Args:
            task_desc: 작업 설명 (예: "작업 task_3 승인")
            
        Returns:
            str: 승인 결과
        """
        # 작업 ID 추출 시도
        task_id = None
        task_desc_lower = task_desc.lower()
        
        if "작업" in task_desc_lower and "승인" in task_desc_lower:
            parts = task_desc_lower.split()
            for i, part in enumerate(parts):
                if part == "작업" and i + 1 < len(parts):
                    task_id = parts[i + 1]
                    break
        
        # 작업 ID 형식 정리 (task_3 또는 3과 같은 형식 처리)
        if task_id:
            if not task_id.startswith("task_") and task_id.isdigit():
                task_id = f"task_{task_id}"
        
        # 작업 ID를 찾지 못한 경우
        if not task_id:
            return "승인할 작업 ID를 찾을 수 없습니다. '작업 [작업ID] 승인' 형식으로 요청해주세요."
        
        # 해당 작업 찾기
        pending_task = None
        for task in self.project_status["pending_approvals"]:
            if task["id"] == task_id:
                pending_task = task
                break
        
        if not pending_task:
            return f"작업 ID '{task_id}'를 찾을 수 없거나 승인 대기 중이 아닙니다."
        
        # 작업 승인 처리
        self.project_status["pending_approvals"] = [t for t in self.project_status["pending_approvals"] if t["id"] != task_id]
        pending_task["status"] = "completed"
        self.project_status["completed_tasks"].append(pending_task)
        
        return f"작업 '{task_id}'가 성공적으로 승인되었습니다."
    
    def _handle_direct_response(self, task_desc: str) -> str:
        """
        PM Agent가 직접 응답할 수 있는 작업 처리
        
        Args:
            task_desc: 작업 설명
            
        Returns:
            str: 직접 생성한 응답
        """
        system_prompt = """
        당신은 소프트웨어 개발 프로젝트의 프로젝트 관리자(PM)입니다.
        개발 프로젝트의 계획, 일정, 리소스 관리, 이슈 대응, 이해관계자 소통 등에 관한 전문 지식을 보유하고 있습니다.
        
        질문이나 요청에 전문적이고 간결하게 응답하되, 필요시 설명과 근거를 제시하세요.
        UI/UX, 프론트엔드, 백엔드 또는 AI 엔지니어링에 대한 전문적 질문일 경우, 
        해당 전문가에게 문의하는 것이 더 적절한지 언급할 수 있습니다.
        """
        
        prompt = f"""
        현재 프로젝트 상태:
        - 총 작업: {len(self.project_status["tasks"])}개
        - 완료된 작업: {len(self.project_status["completed_tasks"])}개
        - 승인 대기 중: {len(self.project_status["pending_approvals"])}개
        
        질문/요청: {task_desc}
        
        위 요청에 대해 프로젝트 관리자로서 응답해주세요.
        """
        
        return self._call_ollama_api(prompt, system_prompt, temperature=0.7, max_tokens=1500)
    
    def generate_project_plan(self, project_desc: str) -> Dict[str, Any]:
        """
        프로젝트 계획 생성
        
        Args:
            project_desc: 프로젝트 설명
            
        Returns:
            Dict[str, Any]: 생성된 프로젝트 계획
        """
        result = self._handle_planning_task(project_desc)
        
        # 계획을 구조화된 포맷으로 변환
        return {
            "description": project_desc,
            "plan_text": result,
            "tasks": self.project_status["tasks"],
            "created_at": time.time()
        }
    
    def execute_task(self, task_desc: str, agent_type: Optional[str] = None) -> Dict[str, Any]:
        """
        작업 실행 (자동 에이전트 할당 또는 지정된 에이전트 사용)
        
        Args:
            task_desc: 작업 설명
            agent_type: 에이전트 유형 (지정하지 않으면 자동 분석)
            
        Returns:
            Dict[str, Any]: 작업 실행 결과
        """
        if not agent_type:
            _, detected_agent, _ = self._analyze_task(task_desc)
            agent_type = detected_agent
        
        if not agent_type:
            # 에이전트를 감지할 수 없는 경우, PM이 직접 처리
            result = self._handle_direct_response(task_desc)
            return {
                "task": task_desc,
                "agent_type": "pm",
                "result": result,
                "status": "completed",
                "timestamp": time.time()
            }
        
        # 에이전트에 작업 위임
        result = self._delegate_task(agent_type, task_desc)
        
        # 가장 최근 작업 찾기
        latest_task = None
        for task in self.project_status["tasks"]:
            if task["description"] == task_desc:
                if not latest_task or task["created_at"] > latest_task["created_at"]:
                    latest_task = task
        
        if not latest_task:
            return {
                "task": task_desc,
                "agent_type": agent_type,
                "result": result,
                "status": "error",
                "timestamp": time.time()
            }
        
        return {
            "task": task_desc,
            "task_id": latest_task["id"],
            "agent_type": agent_type,
            "result": result,
            "status": latest_task["status"],
            "timestamp": time.time()
        }
    
    def approve_task(self, task_id: str) -> Dict[str, Any]:
        """
        작업 승인
        
        Args:
            task_id: 작업 ID
            
        Returns:
            Dict[str, Any]: 승인 결과
        """
        # task_id 형식 정규화
        if not task_id.startswith("task_") and task_id.isdigit():
            task_id = f"task_{task_id}"
        
        result = self._handle_approval_request(f"작업 {task_id} 승인")
        
        success = "성공적으로 승인" in result
        
        return {
            "task_id": task_id,
            "approved": success,
            "message": result,
            "timestamp": time.time()
        }
    
    def get_project_status(self) -> Dict[str, Any]:
        """
        프로젝트 상태 가져오기
        
        Returns:
            Dict[str, Any]: 프로젝트 상태 정보
        """
        return {
            "total_tasks": len(self.project_status["tasks"]),
            "completed_tasks": len(self.project_status["completed_tasks"]),
            "pending_approvals": len(self.project_status["pending_approvals"]),
            "agent_status": self.project_status["agent_status"],
            "tasks": self.project_status["tasks"],
            "pending_approval_tasks": self.project_status["pending_approvals"],
            "timestamp": time.time()
        }
    
    def run_task(self, task_description: str) -> str:
        """
        작업 실행 (호환성을 위한 메서드)
        
        Args:
            task_description: 작업 설명
            
        Returns:
            str: 작업 결과
        """
        return self._run({"task": task_description})

    def _call_pmagent_mcp(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """PMAgent MCP 서버의 도구를 호출합니다."""
        payload = {
            "name": tool_name,
            "parameters": parameters
        }
        headers = {"Content-Type": "application/json"}

        logger.debug(f"PM Agent {self.agent_id} calling MCP tool: {tool_name} with params: {parameters}")

        try:
            response = requests.post(self.mcp_server_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status() # HTTP 오류 발생 시 예외 처리
            result = response.json()
            logger.debug(f"MCP tool {tool_name} response: {result}")
            return result
        except requests.exceptions.Timeout:
            logger.error(f"MCP tool {tool_name} call timed out.")
            return {"success": False, "error": "Request timed out"}
        except requests.exceptions.RequestException as e:
            logger.error(f"MCP tool {tool_name} call failed: {e}")
            # 응답 내용이 있다면 포함
            error_detail = str(e)
            if e.response is not None:
                try:
                    error_detail += f" - Response: {e.response.text}"
                except Exception:
                    pass # 응답 내용 읽기 실패 시 무시
            return {"success": False, "error": error_detail}
        except json.JSONDecodeError:
            logger.error(f"MCP tool {tool_name} response is not valid JSON: {response.text}")
            return {"success": False, "error": "Invalid JSON response from server"}

    def _check_and_process_tasks(self, request_id: Optional[str] = None):
        """MCP 서버에서 다음 작업을 확인하고 처리(시뮬레이션)합니다."""
        if not self.use_mcp:
            logger.info("MCP is not enabled for this agent.")
            return

        if not request_id:
            # 현재 프로젝트 ID를 사용하여 작업 확인
            if self.current_project_id:
                request_id = self.current_project_id
                logger.info(f"Using current project ID as request_id: {request_id}")
            else:
                logger.warning("No specific requestId provided and no current project. Cannot check tasks.")
                return

        logger.info(f"PM Agent {self.agent_id} checking for next task for request {request_id}...")
        get_task_params = {
            "requestId": request_id,
            "agentId": self.agent_id
        }
        result = self._call_pmagent_mcp("get_next_task", get_task_params)

        if result.get("success") and result.get("hasNextTask"):
            task_data = result.get("task")
            if task_data:
                task_id = task_data.get("id")
                task_title = task_data.get("title")
                logger.info(f"PM Agent {self.agent_id} assigned task: ID={task_id}, Title='{task_title}'")

                # --- 작업 처리 시뮬레이션 시작 ---
                logger.info(f"Processing task {task_id}...")
                # 실제 작업 로직 대신 간단한 메시지 생성
                completed_details = f"PM Agent {self.agent_id} processed task '{task_title}'. All looks good."
                time.sleep(random.uniform(1, 3)) # 처리 시간 모방
                logger.info(f"Task {task_id} processing complete.")
                # --- 작업 처리 시뮬레이션 끝 ---

                # 작업 완료 보고
                mark_done_params = {
                    "requestId": request_id,
                    "taskId": task_id,
                    "agentId": self.agent_id,
                    "completedDetails": completed_details
                }
                done_result = self._call_pmagent_mcp("mark_task_done", mark_done_params)

                if done_result.get("success"):
                    logger.info(f"Successfully marked task {task_id} as done.")
                else:
                    logger.error(f"Failed to mark task {task_id} as done: {done_result.get('error')}")
            else:
                logger.warning("get_next_task succeeded but no task data received.")
        elif result.get("success") and not result.get("hasNextTask"):
            logger.info(f"No new assignable tasks found for request {request_id} for agent {self.agent_id}.")
        else:
            logger.error(f"Failed to get next task for request {request_id}: {result.get('error')}")

    def start_working(self, request_id: str, interval: int = 10):
        """
        지정된 요청 ID에 대해 주기적으로 작업을 확인하고 처리합니다.

        Args:
            request_id: 처리할 요청 ID
            interval: 작업 확인 간격 (초)
        """
        if not self.use_mcp:
            logger.error("MCP is not enabled. Cannot start working loop.")
            return

        logger.info(f"PM Agent {self.agent_id} starting to work on request {request_id} (checking every {interval} seconds)...")
        try:
            while True: # 실제 운영시 종료 조건 필요
                self._check_and_process_tasks(request_id)
                logger.debug(f"Waiting for {interval} seconds before next check...")
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info(f"PM Agent {self.agent_id} stopping work loop.")
        except Exception as e:
            logger.error(f"An error occurred during the working loop for request {request_id}: {e}", exc_info=True)

    def plan_request(self, original_request_text: str, tasks_list: List[Dict[str, Any]], 
                     current_project_id: Optional[str] = None, 
                     current_project_name: Optional[str] = None) -> Optional[Dict[str, Any]]: # 반환 타입을 Dict로 변경
        """
        주어진 요청으로 request_planning을 호출하여 요청과 태스크를 생성하고 MCP 서버 응답을 반환합니다.
        """
        if not self.use_mcp:
            logger.error("MCP is not enabled. Cannot plan and start work.")
            return None

        logger.info(f"PM Agent {self.agent_id} preparing to call 'request_planning' for: {original_request_text[:50]}...")
        planning_params = {
            "originalRequest": original_request_text,
            "tasks": tasks_list
        }
        if current_project_id:
            planning_params["projectId"] = current_project_id
            logger.info(f"Using provided projectId: {current_project_id}")
        if current_project_name:
            planning_params["projectName"] = current_project_name
            logger.info(f"Using provided projectName: {current_project_name}")
        
        # MCP 서버의 request_planning 도구 호출
        planning_result_from_mcp = self._call_pmagent_mcp("request_planning", planning_params)

        # _call_pmagent_mcp는 이미 dict를 반환하므로, success 키 등으로 성공 여부 판단 가능
        if planning_result_from_mcp and planning_result_from_mcp.get("project_id"): # mcp_server.py가 반환하는 키에 맞춤
            logger.info(f"MCP 'request_planning' successful. Server response: {planning_result_from_mcp}")
            return planning_result_from_mcp # MCP 서버의 전체 응답 반환
        else:
            error_msg = planning_result_from_mcp.get("error") or planning_result_from_mcp.get("detail") or "Unknown error from MCP server."
            logger.error(f"Failed to plan request via MCP: {error_msg}")
            logger.debug(f"Full MCP response on failure: {planning_result_from_mcp}")
            return {"error": error_msg, "details": planning_result_from_mcp} # 실패 시에도 dict 반환

# 테스트 코드 (예시)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # PMAgentOllama 인스턴스 생성
    pm_agent = PMAgentOllama(
        # api_base, model 등 필요한 파라미터는 환경변수나 기본값을 따르도록 설정되어 있음
        use_mcp=True, 
        mcp_server_url="http://localhost:8083/mcp/invoke" 
    )

    if len(sys.argv) > 1:
        user_request = " ".join(sys.argv[1:])
        print(f"\n=== PMAgentOllama 작업 계획 테스트 시작 ===")
        print(f"사용자 요청: {user_request}")
        
        try:
            plan_result = pm_agent._handle_planning_task(
                task_desc=user_request
            )
            
            # plan_result가 딕셔너리이고 'success' 키를 가지고 있는지 확인
            if isinstance(plan_result, dict) and plan_result.get("success"):
                project_id = plan_result.get("project_id") # MCP 응답에서 직접 가져옴
                task_ids = plan_result.get("task_ids", []) 
                print(f"프로젝트 계획이 MCP 서버에 성공적으로 등록되었습니다.")
                print(f"Project ID: {project_id}")
                if task_ids:
                    print(f"생성된 Task IDs: {', '.join(task_ids)}")
                else:
                    print("생성된 Task ID가 없습니다 (MCP 서버 응답 확인 필요).")
                
                if project_id:
                    print(f"\n이제 다음 명령으로 BackendAgent를 실행하세요 (YOUR_PROJECT_ID를 위 Project ID로 교체):")
                    print(f"python -m agents.backend_agent_ollama {project_id}")
                else:
                    print("\nProject ID가 반환되지 않아 BackendAgent 실행 명령을 생성할 수 없습니다.")
            else: # 실패 또는 예기치 않은 형식의 결과
                error_msg = "알 수 없는 오류 또는 실패"
                details_msg = ""
                if isinstance(plan_result, dict):
                    error_msg = plan_result.get('error', error_msg)
                    details = plan_result.get('details')
                    if details:
                        details_msg = f" 세부 정보: {details}"

                print(f"프로젝트 계획 등록에 실패했습니다. 오류: {error_msg}{details_msg}")
                if plan_result: # 전체 응답 로깅
                    print(f"전체 응답: {plan_result}")

        except Exception as e:
            logger.error(f"PMAgentOllama 실행 중 오류 발생: {e}", exc_info=True)
            print(f"오류 발생: {e}")
            
    else:
        print("오류: 사용자 요청을 명령행 인자로 제공해주세요.")
        print("예시: python -m agents.pm_agent_ollama \"간단한 블로그 API 서버 만들기\"") 