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
from typing import Dict, List, Optional, Any, Union, Tuple

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
                 mcp_helper: Optional[Any] = None, **kwargs):
        """
        Ollama 기반 PM Agent 초기화
        
        Args:
            api_key: 사용되지 않음 (Ollama 호환성 유지용)
            api_base: Ollama API 기본 URL
            model: 사용할 Ollama 모델명
            use_mcp: MCP(Model Context Protocol) 사용 여부
            mcp_helper: MCPAgentHelper 인스턴스
        """
        # API 설정
        self.api_key = api_key  # Ollama는 API 키를 사용하지 않지만 호환성을 위해 유지
        self.api_base = api_base or os.environ.get("OLLAMA_API_BASE", "http://localhost:11434/api")
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.2:latest")
        
        # MCP 설정
        self.use_mcp = use_mcp
        self.mcp_helper = mcp_helper
        
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
                         temperature: float = 0.7, max_tokens: int = 800) -> str:
        """
        Ollama API 호출
        
        Args:
            prompt: 프롬프트 텍스트
            system_prompt: 시스템 프롬프트 (지시사항)
            temperature: 온도 (창의성 조절)
            max_tokens: 최대 토큰 수
            
        Returns:
            str: API 응답 텍스트
        """
        url = f"{self.api_base.rstrip('/')}/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "options": {}
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "응답을 받을 수 없습니다.")
        except Exception as e:
            return f"Ollama API 호출 중 오류 발생: {str(e)}"
    
    def _run(self, task: Dict[str, Any]) -> str:
        """
        PM Agent로 작업을 실행합니다.
        
        Args:
            task: 작업 정보 딕셔너리 또는 작업 설명 문자열
            
        Returns:
            str: 작업 결과
        """
        # task가 문자열인 경우 딕셔너리로 변환
        if isinstance(task, str):
            task = {"task": task}
        
        task_desc = task.get("task", "")
        
        # 작업 유형 분석
        action, agent_type, details = self._analyze_task(task_desc)
        
        # 작업 유형에 따라 다른 처리
        if action == "plan":
            result = self._handle_planning_task(details)
        elif action == "delegate":
            result = self._delegate_task(agent_type, details, task.get("approve", False))
        elif action == "status":
            result = self._handle_status_request(details)
        elif action == "approve":
            result = self._handle_approval_request(details)
        else:
            # 기본 작업 처리 (직접 응답)
            result = self._handle_direct_response(task_desc)
        
        # 작업 기록에 추가
        self.task_history.append({
            "timestamp": time.time(),
            "task": task_desc,
            "action": action,
            "agent_type": agent_type,
            "result_length": len(result)
        })
        
        return result
    
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
    
    def _handle_planning_task(self, task_desc: str) -> str:
        """
        프로젝트 계획 수립 작업을 처리합니다.
        
        Args:
            task_desc: 작업 설명
            
        Returns:
            str: 생성된 프로젝트 계획
        """
        system_prompt = """
        당신은 프로젝트 관리자(PM)로서 개발 프로젝트의 전체 계획을 수립하는 전문가입니다.
        다음 요소를 포함한 종합적인 프로젝트 계획을 작성하세요:
        
        1. 프로젝트 목표 및 범위
        2. 주요 작업 목록 (디자인, 프론트엔드, 백엔드, AI 관련 작업으로 구분)
        3. 작업 순서 및 종속성
        4. 예상 타임라인
        5. 리스크 및 완화 전략
        
        각 전문 영역(디자인, 프론트엔드, 백엔드, AI)별로 세부 작업을 구체적으로 나열하세요.
        """
        
        prompt = f"""
        프로젝트 요청: {task_desc}
        
        위 요청에 대한 상세한 프로젝트 계획을 작성해주세요.
        각 전문 에이전트(디자이너, 프론트엔드, 백엔드, AI 엔지니어)가 담당할 작업을 명확히 구분하여 작성해주세요.
        """
        
        plan = self._call_ollama_api(prompt, system_prompt, temperature=0.7, max_tokens=2000)
        
        # 생성된 계획에서 작업 추출 및 상태 업데이트
        try:
            tasks = self._extract_tasks_from_plan(plan)
            self.project_status["tasks"].extend(tasks)
        except Exception as e:
            logger.error(f"계획에서 작업 추출 중 오류 발생: {str(e)}")
        
        return plan
    
    def _extract_tasks_from_plan(self, plan: str) -> List[Dict[str, Any]]:
        """
        계획 텍스트에서 작업 추출
        
        Args:
            plan: 계획 텍스트
            
        Returns:
            List[Dict[str, Any]]: 추출된 작업 목록
        """
        tasks = []
        
        # 단순 휴리스틱을 사용한 작업 추출
        # 실제 구현에서는 더 강력한 파싱 로직이 필요할 수 있음
        for agent_type in ["디자인", "Design", "프론트엔드", "Frontend", "백엔드", "Backend", "AI", "AI 엔지니어"]:
            section_start = plan.find(agent_type)
            if section_start == -1:
                continue
            
            # 다음 섹션 또는 문서 끝까지 검색
            next_section = float('inf')
            for next_agent in ["디자인", "Design", "프론트엔드", "Frontend", "백엔드", "Backend", "AI", "AI 엔지니어"]:
                if next_agent == agent_type:
                    continue
                pos = plan.find(next_agent, section_start + len(agent_type))
                if pos != -1 and pos < next_section:
                    next_section = pos
            
            if next_section == float('inf'):
                section_text = plan[section_start:]
            else:
                section_text = plan[section_start:next_section]
            
            # 행 단위로 분할하고 작업 항목 찾기 (번호 또는 목록 기호로 시작하는 줄)
            lines = section_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line[0] in ['-', '*', '•']):
                    # 에이전트 유형 정규화
                    normalized_agent_type = self._normalize_agent_type(agent_type)
                    if normalized_agent_type:
                        task_desc = line[1:].strip() if not line[0].isdigit() else line[line.find('.')+1:].strip()
                        if task_desc:
                            tasks.append({
                                "id": f"task_{len(self.project_status['tasks']) + len(tasks) + 1}",
                                "description": task_desc,
                                "agent_type": normalized_agent_type,
                                "status": "pending",
                                "created_at": time.time()
                            })
        
        return tasks
    
    def _normalize_agent_type(self, agent_type: str) -> Optional[str]:
        """
        에이전트 유형을 정규화합니다.
        
        Args:
            agent_type: 원본 에이전트 유형 문자열
            
        Returns:
            Optional[str]: 정규화된 에이전트 유형 또는 None
        """
        agent_type_lower = agent_type.lower()
        
        if "디자인" in agent_type_lower or "design" in agent_type_lower:
            return "designer"
        elif "프론트" in agent_type_lower or "front" in agent_type_lower:
            return "frontend"
        elif "백" in agent_type_lower or "back" in agent_type_lower:
            return "backend"
        elif "ai" in agent_type_lower or "인공지능" in agent_type_lower or "엔지니어" in agent_type_lower:
            return "ai_engineer"
        
        return None
    
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

# 테스트 코드
if __name__ == "__main__":
    # PM 에이전트 생성
    pm_agent = PMAgentOllama(
        api_base="http://localhost:11434/api",
        model="llama3.2:latest"
    )
    
    # 작업 위임 시뮬레이션을 위한 간단한 에이전트 클래스
    class MockAgent:
        def __init__(self, agent_type):
            self.agent_type = agent_type
        
        def run_task(self, task):
            return f"{self.agent_type.capitalize()} 에이전트의 작업 결과: {task}"
    
    # 각 에이전트 등록
    for agent_type in ["designer", "frontend", "backend", "ai_engineer"]:
        pm_agent.register_agent(agent_type, MockAgent(agent_type))
    
    # 프로젝트 계획 생성
    print("=== 프로젝트 계획 생성 ===")
    plan_result = pm_agent.run_task("쇼핑몰 웹사이트 개발 프로젝트 계획을 수립해주세요.")
    print(f"계획 (일부): {plan_result[:200]}...\n")
    
    # 작업 위임
    print("=== 작업 위임 ===")
    delegate_result = pm_agent.run_task("로그인 페이지 디자인 작업을 진행해주세요.")
    print(f"위임 결과: {delegate_result}\n")
    
    # 상태 확인
    print("=== 프로젝트 상태 확인 ===")
    status_result = pm_agent.run_task("현재 프로젝트 진행 상황을 알려주세요.")
    print(f"상태 보고서: {status_result}\n")
    
    # 작업 승인
    print("=== 작업 승인 ===")
    approval_result = pm_agent.run_task("작업 task_1 승인")
    print(f"승인 결과: {approval_result}") 