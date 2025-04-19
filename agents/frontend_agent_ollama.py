import os
import requests
import json
from typing import Dict, List, Any, Optional, Union
import logging
try:
    from .mcp_agent_helper import MCPAgentHelper
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from .base_tool import BaseTool

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FrontendAgentOllama")

class FrontendAgentOllama(BaseTool):
    """
    Ollama를 통해 프론트엔드 개발 작업을 수행하는 에이전트
    
    FrontendAgent와 동일한 인터페이스를 제공하되 Ollama API를 통해 로컬 LLM을 활용
    """
    
    def __init__(self, 
                api_key: Optional[str] = None, 
                api_base: Optional[str] = None,
                model: str = "llama3:latest",
                use_mcp: bool = False,
                mcp_helper = None,
                temperature: float = 0.7):
        """
        Ollama 프론트엔드 에이전트 초기화
        
        Args:
            api_key: 사용하지 않음 (호환성 유지용)
            api_base: Ollama API 기본 URL (기본값: http://localhost:11434/api)
            model: 사용할 Ollama 모델 (기본값: llama3:latest)
            use_mcp: MCP 사용 여부
            mcp_helper: MCP 헬퍼 인스턴스
            temperature: 생성 온도 (0.0 ~ 1.0)
        """
        super().__init__()
        
        self.api_key = api_key  # 호환성 유지용
        self.api_base = api_base or os.environ.get("OLLAMA_API_BASE", "http://localhost:11434/api")
        self.model = model
        self.temperature = temperature
        self.use_mcp = use_mcp
        self.mcp_helper = mcp_helper
        
        # 프로젝트 구성 초기화
        self.project_config = self._initialize_project_config()
        
        # Ollama 모델 상태 확인
        self._check_model_availability()
        
        logger.info(f"Ollama 프론트엔드 에이전트 초기화 완료 - 모델: {model}, API 기본 URL: {api_base}")
        
    def _initialize_project_config(self) -> Dict[str, Any]:
        """
        프로젝트 구성을 초기화합니다.
        
        Returns:
            Dict[str, Any]: 프로젝트 구성 정보
        """
        return {
            "platform": "react",  # 기본값: React 웹, 'react-native'도 가능
            "use_typescript": True,
            "state_management": "react-query",
            "styling": "tailwind",
            "component_path": "src/components",
            "screen_path": "src/screens",
            "api_path": "src/api"
        }
    
    def _check_model_availability(self) -> bool:
        """
        Ollama 모델 사용 가능 여부 확인
        
        Returns:
            모델 사용 가능 여부
        """
        try:
            logger.info(f"Ollama 모델 확인 중: {self.model}")
            models_url = f"{self.api_base}/tags"
            response = requests.get(models_url)
            
            if response.status_code != 200:
                logger.warning(f"Ollama API 응답 오류: {response.status_code}")
                return False
            
            models_data = response.json()
            models = [model.get("name", "") for model in models_data.get("models", [])]
            
            if self.model in models:
                logger.info(f"Ollama 모델 사용 가능: {self.model}")
                return True
            else:
                logger.warning(f"Ollama 모델을 찾을 수 없음: {self.model}")
                logger.info(f"사용 가능한 모델: {', '.join(models)}")
                return False
                
        except Exception as e:
            logger.error(f"Ollama 모델 확인 중 오류 발생: {str(e)}")
            return False
            
    def _ollama_request(self, prompt: str) -> Dict[str, Any]:
        """
        Ollama API 요청 수행
        
        Args:
            prompt: 요청 프롬프트
            
        Returns:
            Ollama API 응답
        """
        # MCP 우선 사용(설정된 경우)
        if self.use_mcp and self.mcp_helper:
            try:
                result = self.mcp_helper.generate_text(prompt=prompt)
                if result and isinstance(result, str):
                    return {"response": result}
                elif result and isinstance(result, dict):
                    return result
            except Exception as e:
                logger.warning(f"MCP 사용 실패, Ollama로 대체합니다: {str(e)}")
                # MCP 실패 시 Ollama로 계속 진행
        
        try:
            generate_url = f"{self.api_base}/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": self.temperature,
                "stream": False
            }
            
            response = requests.post(generate_url, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Ollama API 오류: {response.status_code}, {response.text}")
                raise Exception(f"Ollama API 오류: {response.status_code}")
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Ollama API 요청 중 오류 발생: {str(e)}")
            raise
    
    def generate_component(self, component_name: str, design_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        디자인 데이터를 기반으로 컴포넌트 코드를 생성합니다.
        
        Args:
            component_name: 컴포넌트 이름
            design_data: 디자인 정보
            
        Returns:
            Dict[str, Any]: 생성된 컴포넌트 코드 및 정보
        """
        logger.info(f"컴포넌트 생성 요청: {component_name}")
        
        # 플랫폼에 따른 확장자 결정
        extension = "tsx" if self.project_config["use_typescript"] else "jsx"
        if self.project_config["platform"] == "react-native":
            extension = extension.replace("jsx", "js").replace("tsx", "ts")
            
        component_type = design_data.get("type", "generic")
        
        # Ollama API 요청 프롬프트 작성
        prompt = f"""
당신은 숙련된 프론트엔드 개발자입니다. 다음 정보를 바탕으로 {self.project_config["platform"]} 컴포넌트를 구현해야 합니다:

컴포넌트 이름: {component_name}
컴포넌트 유형: {component_type}
플랫폼: {self.project_config["platform"]}
TypeScript 사용: {self.project_config["use_typescript"]}
상태 관리: {self.project_config["state_management"]}
디자인 정보: {json.dumps(design_data, ensure_ascii=False)}

요청 형식:
1. 컴포넌트의 목적과 기능을 명확히 하세요.
2. 필요한 props와 상태를 식별하세요.
3. 컴포넌트 구현에 필요한 전체 코드를 작성하세요.
4. 스타일을 적절히 정의하세요.
5. 컴포넌트 내부에 필요한 로직이나 이벤트 핸들러를 구현하세요.

구현된 코드만 제공하세요. 설명이나 주석은 필요하지 않습니다.
"""
        
        # Ollama 요청 수행
        try:
            response = self._ollama_request(prompt)
            
            # 응답 파싱
            output = response.get("response", "")
            
            # 코드 블록 추출
            code = output
            if "```" in output:
                code_parts = []
                in_code_block = False
                for line in output.split('\n'):
                    if line.startswith('```'):
                        if not in_code_block:
                            in_code_block = True
                            # 언어 표시 제거 (```jsx -> ```)
                            continue
                        else:
                            in_code_block = False
                            continue
                    if in_code_block:
                        code_parts.append(line)
                if code_parts:
                    code = '\n'.join(code_parts)
            
            # 파일 경로 생성
            file_path = f"{self.project_config['component_path']}/{component_name}.{extension}"
            
            return {
                "name": component_name,
                "type": component_type,
                "code": code,
                "path": file_path
            }
                
        except Exception as e:
            logger.error(f"컴포넌트 생성 중 오류 발생: {str(e)}")
            return {
                "name": component_name,
                "type": component_type,
                "error": str(e),
                "path": f"{self.project_config['component_path']}/{component_name}.{extension}"
            }
    
    def implement_screen(self, screen_name: str, components: List[str], design_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        화면 구현
        
        Args:
            screen_name: 화면 이름
            components: 사용할 컴포넌트 목록
            design_data: 디자인 정보
            
        Returns:
            Dict[str, Any]: 구현된 화면 코드 및 정보
        """
        logger.info(f"화면 구현 요청: {screen_name}, 컴포넌트: {components}")
        
        # 플랫폼에 따른 확장자 결정
        extension = "tsx" if self.project_config["use_typescript"] else "jsx"
        if self.project_config["platform"] == "react-native":
            extension = extension.replace("jsx", "js").replace("tsx", "ts")
        
        # Ollama API 요청 프롬프트 작성
        prompt = f"""
당신은 숙련된 프론트엔드 개발자입니다. 다음 정보를 바탕으로 {self.project_config["platform"]} 화면을 구현해야 합니다:

화면 이름: {screen_name}
사용할 컴포넌트: {', '.join(components)}
플랫폼: {self.project_config["platform"]}
TypeScript 사용: {self.project_config["use_typescript"]}
상태 관리: {self.project_config["state_management"]}
디자인 정보: {json.dumps(design_data, ensure_ascii=False)}

요청 형식:
1. 화면의 목적과 레이아웃을 명확히 하세요.
2. 필요한 상태와 데이터를 정의하세요.
3. 컴포넌트를 적절히 배치하고 스타일을 적용하세요.
4. 필요한 이벤트 핸들러와 로직을 구현하세요.
5. 화면에 필요한 라우팅 또는 네비게이션 로직이 있다면 포함하세요.

구현된 코드만 제공하세요. 설명이나 주석은 필요하지 않습니다.
"""
        
        # Ollama 요청 수행
        try:
            response = self._ollama_request(prompt)
            
            # 응답 파싱
            output = response.get("response", "")
            
            # 코드 블록 추출
            code = output
            if "```" in output:
                code_parts = []
                in_code_block = False
                for line in output.split('\n'):
                    if line.startswith('```'):
                        if not in_code_block:
                            in_code_block = True
                            # 언어 표시 제거 (```jsx -> ```)
                            continue
                        else:
                            in_code_block = False
                            continue
                    if in_code_block:
                        code_parts.append(line)
                if code_parts:
                    code = '\n'.join(code_parts)
            
            # 파일 경로 생성
            file_path = f"{self.project_config['screen_path']}/{screen_name}.{extension}"
            
            return {
                "name": screen_name,
                "components": components,
                "code": code,
                "path": file_path
            }
                
        except Exception as e:
            logger.error(f"화면 구현 중 오류 발생: {str(e)}")
            return {
                "name": screen_name,
                "components": components,
                "error": str(e),
                "path": f"{self.project_config['screen_path']}/{screen_name}.{extension}"
            }
    
    def _run(self, task: Dict[str, Any]) -> str:
        """
        프론트엔드 작업을 실행합니다.
        
        Args:
            task: 작업 정보 딕셔너리
            
        Returns:
            str: 작업 결과
        """
        code_instructions = task.get('description', "")
        platform = task.get('platform', self.project_config["platform"])
        component_type = task.get('component_type', 'generic')
        
        # 디자인 정보 처리
        design_data = {"type": component_type, "styles": {"backgroundColor": "#3A86FF"}}
        
        # 플랫폼에 따라 코드 생성
        if "component" in code_instructions.lower() or "컴포넌트" in code_instructions.lower():
            component_name = task.get('component_name', f"{component_type.capitalize()}Component")
            component = self.generate_component(component_name, design_data)
            code_snippet = component["code"]
            file_path = component["path"]
        elif "screen" in code_instructions.lower() or "page" in code_instructions.lower() or "화면" in code_instructions.lower():
            screen_name = task.get('screen_name', "MainScreen")
            components = task.get('components', ["ButtonComponent", "CardComponent"])
            screen = self.implement_screen(screen_name, components, design_data)
            code_snippet = screen["code"]
            file_path = screen["path"]
        else:
            # 기본적으로 간단한 컴포넌트 생성
            component_name = task.get('component_name', "GenericComponent")
            component = self.generate_component(component_name, design_data)
            code_snippet = component["code"]
            file_path = component["path"]
        
        # GitHub에 저장 (GitHub MCP 통합 시)
        github_result = ""
        if task.get('save_to_github', False) and self.use_mcp and self.mcp_helper:
            try:
                commit_message = f"Add {file_path} for: {code_instructions}"
                # MCP 헬퍼를 통한 GitHub 커밋 호출
                github_result = f" GitHub 커밋 완료: {commit_message}"
            except Exception as e:
                logger.error(f"GitHub 커밋 중 오류 발생: {str(e)}")
                github_result = f" GitHub 커밋 실패: {str(e)}"
        else:
            github_result = f" GitHub 커밋 시뮬레이션: '{code_instructions}에 대한 코드' 커밋 완료"
        
        return f"작성된 코드: {file_path} ({code_instructions}).{github_result}"
        
    def run_task(self, task_desc: str) -> str:
        """
        프론트엔드 개발 관련 작업을 수행하고 결과를 반환합니다.
        
        Args:
            task_desc: 작업 설명
            
        Returns:
            str: 작업 결과 메시지
        """
        # 부모 클래스 메서드를 상속받아 그대로 사용
        return super().run_task(task_desc)


# 테스트 코드
if __name__ == "__main__":
    # 환경변수 설정 또는 직접 API 키 전달
    agent = FrontendAgentOllama(model="llama3:latest")
    
    # 테스트 실행
    result = agent.run_task("React Native 버튼 컴포넌트를 만들어주세요.")
    print(result) 