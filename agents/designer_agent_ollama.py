"""
Ollama API를 활용한 디자이너 에이전트 모듈

이 모듈은 Ollama를 통해 로컬에서 실행되는 LLM을 사용하여 디자인 관련 기능을 제공합니다.
PM 에이전트의 지시에 따라 작업을 수행하고 결과를 반환합니다.
"""

import os
import json
import time
import requests
import logging
from typing import Dict, List, Optional, Any, Union

# MCP Agent Helper 가져오기 (사용 가능한 경우)
try:
    from .mcp_agent_helper import MCPAgentHelper
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class DesignerAgentOllama(BaseTool):
    """
    Ollama API를 사용하는 Designer Agent
    
    디자인 관련 작업을 처리하는 Ollama 기반 에이전트
    - UI/UX 디자인
    - 와이어프레임 작성
    - 디자인 시스템 관리
    - 컴포넌트 디자인
    - 디자인 가이드라인 제공
    """
    
    name = "designer_agent_ollama"
    description = "Ollama 기반 Designer Agent - UI/UX 디자인 관련 작업 처리"
    
    def __init__(self, api_key=None, model="llama3.2:latest", api_base="http://localhost:11434", **kwargs):
        """
        디자이너 에이전트 초기화
        
        Args:
            api_key (str, optional): API 키
            model (str, optional): Ollama 모델명. 기본값은 "llama3.2:latest"
            api_base (str, optional): Ollama API 기본 URL. 기본값은 "http://localhost:11434"
        """
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        
        # API URL이 /api로 끝나지 않으면 추가
        if not self.api_base.endswith('/api'):
            self.api_base = f"{self.api_base}/api"
        
        # 디자인 시스템 초기화
        self.design_system = {
            "색상": {
                "primary": {
                    "main": "#3A86FF",
                    "light": "#7CB0FF",
                    "dark": "#0063CC"
                },
                "secondary": {
                    "main": "#8338EC",
                    "light": "#B26EFF",
                    "dark": "#5900B9"
                },
                "accent": {
                    "main": "#FF006E",
                    "light": "#FF5998",
                    "dark": "#C50046"
                },
                "배경": {
                    "light": "#FFFFFF",
                    "dark": "#121212",
                    "muted": "#F5F5F5"
                },
                "텍스트": {
                    "primary": "#212121",
                    "secondary": "#757575",
                    "disabled": "#BDBDBD"
                }
            },
            "타이포그래피": {
                "폰트패밀리": {
                    "기본": "Pretendard, sans-serif",
                    "제목": "Pretendard, sans-serif",
                    "코드": "JetBrains Mono, monospace"
                },
                "크기": {
                    "h1": "2.5rem",
                    "h2": "2rem",
                    "h3": "1.75rem",
                    "h4": "1.5rem",
                    "h5": "1.25rem",
                    "h6": "1rem",
                    "본문": "1rem",
                    "작게": "0.875rem",
                    "매우작게": "0.75rem"
                },
                "두께": {
                    "가늘게": 300,
                    "일반": 400,
                    "중간": 500,
                    "굵게": 700,
                    "매우굵게": 900
                }
            },
            "간격": {
                "xs": "0.25rem",
                "sm": "0.5rem",
                "md": "1rem",
                "lg": "1.5rem",
                "xl": "2rem",
                "xxl": "3rem"
            },
            "그림자": {
                "작게": "0 2px 4px rgba(0,0,0,0.1)",
                "중간": "0 4px 8px rgba(0,0,0,0.1)",
                "크게": "0 8px 16px rgba(0,0,0,0.1)"
            },
            "반경": {
                "작게": "4px",
                "중간": "8px",
                "크게": "16px",
                "원형": "50%"
            }
        }
        
        # Ollama 모델 사용 가능 확인
        self._check_model_availability()
        
        logger.info(f"디자이너 에이전트가 초기화되었습니다. 모델: {self.model}")
        
        # 작업 기록
        self.task_history = []
    
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
    
    def get_available_models(self):
        """
        Ollama API에서 사용 가능한 모델 목록을 가져옵니다.
        
        Returns:
            list: 사용 가능한 모델 이름 목록
        """
        try:
            url = f"{self.api_base}/tags"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                # 모델 이름 추출
                models = [model['name'] for model in data.get('models', [])]
                return models
            else:
                print(f"⚠️ 모델 목록 가져오기 실패: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"⚠️ 모델 목록 가져오기 중 오류 발생: {str(e)}")
            return []
    
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
        url = f"{self.api_base}/generate"
        
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
        Designer Agent로 작업을 실행합니다.
        
        Args:
            task: 작업 정보 딕셔너리 또는 작업 설명 문자열
            
        Returns:
            str: 작업 결과
        """
        # task가 문자열인 경우 딕셔너리로 변환
        if isinstance(task, str):
            task = {"task": task}
        
        task_desc = task.get("task", "")
        task_type = self._determine_task_type(task_desc)
        
        # MCP 데이터 추가 (사용 가능한 경우)
        if self.use_mcp and self.mcp_helper:
            if task_type == "ui_component" and hasattr(self.mcp_helper, "get_design_data"):
                try:
                    # Figma에서 디자인 데이터 가져오기
                    figma_data = self.mcp_helper.get_design_data("component", task_desc)
                    if figma_data:
                        task["figma_data"] = figma_data
                except Exception as e:
                    logger.error(f"Figma 데이터 가져오기 실패: {str(e)}")
        
        # 작업 유형에 따라 다른 처리
        if task_type == "design_system":
            result = self._handle_design_system_task(task_desc)
        elif task_type == "wireframe":
            result = self._handle_wireframe_task(task_desc, task.get("figma_data"))
        elif task_type == "ui_component":
            result = self._handle_ui_component_task(task_desc, task.get("figma_data"))
        elif task_type == "design_review":
            result = self._handle_design_review_task(task_desc)
        else:
            # 기본 작업 처리
            result = self._handle_general_design_task(task_desc)
        
        # 작업 기록에 추가
        self.task_history.append({
            "timestamp": time.time(),
            "task": task_desc,
            "type": task_type,
            "result_length": len(result)
        })
        
        return result
    
    def _determine_task_type(self, task_desc: str) -> str:
        """
        작업 설명에서 작업 유형을 판단합니다.
        
        Args:
            task_desc: 작업 설명
            
        Returns:
            str: 작업 유형 (design_system, wireframe, ui_component, design_review, general)
        """
        task_desc_lower = task_desc.lower()
        
        if "디자인 시스템" in task_desc_lower or "design system" in task_desc_lower or "색상" in task_desc_lower or "타이포그래피" in task_desc_lower:
            return "design_system"
        elif "와이어프레임" in task_desc_lower or "wireframe" in task_desc_lower or "레이아웃" in task_desc_lower:
            return "wireframe"
        elif "컴포넌트" in task_desc_lower or "component" in task_desc_lower or "ui 요소" in task_desc_lower or "버튼" in task_desc_lower or "폼" in task_desc_lower:
            return "ui_component"
        elif "리뷰" in task_desc_lower or "review" in task_desc_lower or "개선" in task_desc_lower or "피드백" in task_desc_lower:
            return "design_review"
        else:
            return "general"
    
    def _handle_design_system_task(self, task_desc: str) -> str:
        """
        디자인 시스템 관련 작업 처리
        
        Args:
            task_desc: 작업 설명
            
        Returns:
            str: 작업 결과
        """
        system_prompt = """
        당신은 UI/UX 디자이너로 디자인 시스템을 만들고 관리하는 전문가입니다. 
        디자인 시스템에는 다음 요소가 포함됩니다:
        - 색상 팔레트 (브랜드, 기능별, 의미별)
        - 타이포그래피 (서체, 크기, 스타일)
        - 간격 시스템 (마진, 패딩)
        - 컴포넌트 스타일 가이드
        
        사용자의 요구에 맞게 명확하고 일관된 디자인 시스템을 제안하세요.
        """
        
        # 현재 디자인 시스템 정보를 포함한 프롬프트 구성
        prompt = f"""
        현재 디자인 시스템:
        {json.dumps(self.design_system, indent=2, ensure_ascii=False)}
        
        작업 요청: {task_desc}
        
        위 정보를 바탕으로 적절한 디자인 시스템 요소를 생성하거나 수정해주세요.
        결과는 Markdown 형식으로 제공해주세요.
        """
        
        result = self._call_ollama_api(prompt, system_prompt, temperature=0.7, max_tokens=1500)
        
        # 디자인 시스템 업데이트 여부 확인 및 처리
        if "```json" in result:
            try:
                json_start = result.find("```json") + 7
                json_end = result.find("```", json_start)
                json_content = result[json_start:json_end].strip()
                
                updated_design_system = json.loads(json_content)
                # 부분 업데이트 처리
                if isinstance(updated_design_system, dict):
                    for key, value in updated_design_system.items():
                        if key in self.design_system and isinstance(value, dict):
                            self.design_system[key].update(value)
                        else:
                            self.design_system[key] = value
            except Exception as e:
                logger.error(f"디자인 시스템 업데이트 중 오류: {str(e)}")
        
        return result
    
    def _handle_wireframe_task(self, task_desc: str, figma_data: Optional[Dict[str, Any]] = None) -> str:
        """
        와이어프레임 관련 작업 처리
        
        Args:
            task_desc: 작업 설명
            figma_data: Figma에서 가져온 디자인 데이터 (옵션)
            
        Returns:
            str: 작업 결과
        """
        system_prompt = """
        당신은 UI/UX 디자이너로 와이어프레임을 만드는 전문가입니다.
        다음 형식으로 와이어프레임을 설명해주세요:
        
        1. 레이아웃 구조 설명
        2. 주요 영역 및 요소 나열
        3. 인터랙션 및 흐름 설명
        4. 반응형 디자인 고려사항
        
        상세하고 구체적인 와이어프레임 설계를 제공하세요.
        """
        
        # Figma 데이터가 있는 경우 프롬프트에 포함
        figma_prompt = ""
        if figma_data:
            figma_prompt = f"""
            참고할 Figma 디자인 데이터:
            {json.dumps(figma_data, indent=2, ensure_ascii=False)}
            """
        
        prompt = f"""
        현재 디자인 시스템:
        {json.dumps(self.design_system, indent=2, ensure_ascii=False)}
        
        {figma_prompt}
        
        작업 요청: {task_desc}
        
        위 정보를 바탕으로 상세한 와이어프레임 설명을 제공해주세요.
        결과는 Markdown 형식으로 작성해주시고, 가능하면 ASCII 아트를 사용하여 레이아웃을 시각적으로 표현해주세요.
        """
        
        return self._call_ollama_api(prompt, system_prompt, temperature=0.7, max_tokens=2000)
    
    def _handle_ui_component_task(self, task_desc: str, figma_data: Optional[Dict[str, Any]] = None) -> str:
        """
        UI 컴포넌트 관련 작업 처리
        
        Args:
            task_desc: 작업 설명
            figma_data: Figma에서 가져온 디자인 데이터 (옵션)
            
        Returns:
            str: 작업 결과
        """
        system_prompt = """
        당신은 UI/UX 디자이너로 UI 컴포넌트를 디자인하는 전문가입니다.
        다음 정보를 포함하여 UI 컴포넌트 디자인을 설명해주세요:
        
        1. 컴포넌트 기본 설명 및 사용 목적
        2. 시각적 디자인 요소 (색상, 형태, 타이포그래피)
        3. 상태 변화 (기본, 호버, 활성, 비활성)
        4. 접근성 고려사항
        5. 변형 및 사이즈 옵션
        
        가능하면 HTML/CSS 코드 예시를 포함해주세요.
        """
        
        # Figma 데이터가 있는 경우 프롬프트에 포함
        figma_prompt = ""
        if figma_data:
            figma_prompt = f"""
            참고할 Figma 디자인 데이터:
            {json.dumps(figma_data, indent=2, ensure_ascii=False)}
            """
        
        prompt = f"""
        현재 디자인 시스템:
        {json.dumps(self.design_system, indent=2, ensure_ascii=False)}
        
        {figma_prompt}
        
        작업 요청: {task_desc}
        
        위 정보를 바탕으로 상세한 UI 컴포넌트 디자인을 제공해주세요.
        결과는 Markdown 형식으로 작성해주시고, HTML/CSS 코드 예시를 함께 제공해주세요.
        """
        
        return self._call_ollama_api(prompt, system_prompt, temperature=0.7, max_tokens=2000)
    
    def _handle_design_review_task(self, task_desc: str) -> str:
        """
        디자인 리뷰 관련 작업 처리
        
        Args:
            task_desc: 작업 설명
            
        Returns:
            str: 작업 결과
        """
        system_prompt = """
        당신은 UI/UX 디자인 리뷰어입니다. 다음 항목을 포함한 종합적인 디자인 리뷰를 제공하세요:
        
        1. 시각적 일관성 및 디자인 시스템 준수 여부
        2. 사용자 경험 및 상호작용 흐름
        3. 접근성 및 포용성
        4. 개선 제안
        
        객관적이고 건설적인 피드백을 제공하세요.
        """
        
        prompt = f"""
        현재 디자인 시스템:
        {json.dumps(self.design_system, indent=2, ensure_ascii=False)}
        
        작업 요청: {task_desc}
        
        위 정보를 바탕으로 상세한 디자인 리뷰를 제공해주세요.
        """
        
        return self._call_ollama_api(prompt, system_prompt, temperature=0.6, max_tokens=1500)
    
    def _handle_general_design_task(self, task_desc: str) -> str:
        """
        일반 디자인 관련 작업 처리
        
        Args:
            task_desc: 작업 설명
            
        Returns:
            str: 작업 결과
        """
        system_prompt = """
        당신은 UI/UX 디자이너입니다. 디자인 관련 질문이나 요청에 명확하고 전문적으로 답변하세요.
        가능한 경우 다양한 디자인 옵션과 각 옵션의 장단점을 제시하세요.
        필요에 따라 트렌드, 모범 사례, 디자인 원칙 등을 언급하세요.
        """
        
        prompt = f"""
        현재 디자인 시스템:
        {json.dumps(self.design_system, indent=2, ensure_ascii=False)}
        
        작업 요청: {task_desc}
        
        위 정보를 바탕으로 응답해주세요.
        """
        
        return self._call_ollama_api(prompt, system_prompt, temperature=0.7, max_tokens=1500)
    
    def update_design_system(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        디자인 시스템 업데이트
        
        Args:
            updates: 업데이트할 디자인 시스템 요소
            
        Returns:
            Dict[str, Any]: 업데이트된 디자인 시스템
        """
        # 부분 업데이트 처리
        for key, value in updates.items():
            if key in self.design_system and isinstance(value, dict):
                self.design_system[key].update(value)
            else:
                self.design_system[key] = value
        
        return self.design_system
    
    def get_design_system(self) -> Dict[str, Any]:
        """
        현재 디자인 시스템 반환
        
        Returns:
            Dict[str, Any]: 현재 디자인 시스템
        """
        return self.design_system
    
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
    # Ollama Designer 에이전트 생성
    agent = DesignerAgentOllama(
        api_base="http://localhost:11434/api",
        model="llama3.2:latest"
    )
    
    # 테스트 작업
    test_tasks = [
        "로그인 페이지 와이어프레임을 작성해주세요",
        "메인 색상 팔레트에 중간 강조색을 추가해주세요",
        "입력 필드 컴포넌트를 디자인해주세요"
    ]
    
    for task in test_tasks:
        print(f"=== 작업: {task} ===")
        result = agent.run_task(task)
        print(f"결과 (일부): {result[:150]}...\n")
    
    # 디자인 시스템 출력
    print("=== 디자인 시스템 ===")
    print(json.dumps(agent.get_design_system(), indent=2, ensure_ascii=False)) 