#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
프론트엔드 에이전트 - Ollama 기반

디자이너 에이전트의 디자인 결과물을 기반으로 React 컴포넌트를 생성하는 에이전트입니다.
"""

import logging
import json
import os
import sys
from typing import Dict, List, Optional, Any, Tuple

# 상위 디렉토리 추가 (상대 임포트를 위함)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_tool import BaseTool

# OllamaClient 임포트 시도
try:
    from pmagent.ollama_client import OllamaClient
    OLLAMA_CLIENT_AVAILABLE = True
except ImportError:
    OLLAMA_CLIENT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("pmagent.ollama_client 모듈을 불러올 수 없습니다. 일부 기능이 제한될 수 있습니다.")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FrontendAgentOllama(BaseTool):
    """
    디자이너 에이전트의 디자인 결과물을 기반으로 React 컴포넌트를 생성하는 프론트엔드 에이전트입니다.
    """

    def __init__(self, name: str = "프론트엔드 에이전트", model: str = "llama3", config: Optional[Dict[str, Any]] = None):
        """
        FrontendAgentOllama 초기화
        
        Args:
            name: 에이전트 이름
            model: 사용할 Ollama 모델
            config: 추가 설정 (선택적)
        """
        super().__init__()
        self.name = name
        self.agent_type = "frontend"
        
        # Ollama 클라이언트 초기화
        self.client = None
        if OLLAMA_CLIENT_AVAILABLE:
            self.client = OllamaClient(model=model)
        
        # 기본 설정
        self.config = {
            "framework": "react",  # 기본 프레임워크
            "styling": "css-in-js",  # 기본 스타일링 방식
            "typescript": True,  # TypeScript 사용 여부
            "component_library": "none",  # 기본 컴포넌트 라이브러리
            "state_management": "react-hooks"  # 기본 상태 관리 방식
        }
        
        # 사용자 설정 적용
        if config:
            self.config.update(config)
        
        # 태스크 타입 정의
        self.task_types = {
            "GENERATE_COMPONENT": "generate_component",
            "GENERATE_PAGE": "generate_page",
            "REFACTOR_CODE": "refactor_code",
            "OPTIMIZE_PERFORMANCE": "optimize_performance"
        }
        
        logger.info(f"프론트엔드 에이전트 초기화 완료: {name}, 모델: {model}")

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        태스크를 처리합니다.
        
        Args:
            task: 처리할 태스크 정보
            
        Returns:
            처리 결과
        """
        task_type = task.get("type", "")
        logger.info(f"태스크 처리 시작: {task_type}")
        
        if task_type == self.task_types["GENERATE_COMPONENT"]:
            return self.generate_component(task)
        
        elif task_type == self.task_types["GENERATE_PAGE"]:
            return self.generate_page(task)
        
        elif task_type == self.task_types["REFACTOR_CODE"]:
            return self.refactor_code(task)
        
        elif task_type == self.task_types["OPTIMIZE_PERFORMANCE"]:
            return self.optimize_performance(task)
        
        else:
            return {
                "status": "error",
                "message": f"지원하지 않는 태스크 타입: {task_type}",
                "supported_types": list(self.task_types.values())
            }

    def generate_component(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        디자인 정보를 기반으로 React 컴포넌트를 생성합니다.
        
        Args:
            task: 컴포넌트 생성 태스크 정보
            
        Returns:
            생성된 컴포넌트 코드
        """
        # 태스크에서 필요한 정보 추출
        component_name = task.get("component_name", "Component")
        component_type = task.get("component_type", "button")
        design_data = task.get("design_data", {})
        framework = task.get("framework", self.config["framework"])
        use_typescript = task.get("typescript", self.config["typescript"])
        component_library = task.get("component_library", self.config["component_library"])
        
        # 디자인 데이터 확인
        if not design_data:
            return {
                "status": "error",
                "message": "디자인 데이터가 제공되지 않았습니다."
            }
        
        # 프롬프트 생성
        prompt = self._create_component_generation_prompt(
            component_name, component_type, design_data, 
            framework, use_typescript, component_library
        )
        
        # 테스트 중에는 실제 API 호출 대신 더미 응답 사용
        if not self.client:
            response = f"```jsx\nimport React from 'react';\n\nconst {component_name} = () => {{\n  return (\n    <div className=\"{component_type.lower()}\">\n      {component_name} 컴포넌트\n    </div>\n  );\n}};\n\nexport default {component_name};\n```"
        else:
            # AI 모델에 요청
            response = self.client.generate(prompt)
        
        # 코드 추출
        code = self._extract_code_from_response(response)
        
        # 결과 반환
        return {
            "status": "generated",
            "component_name": component_name,
            "framework": framework,
            "typescript": use_typescript,
            "component_library": component_library,
            "code": code,
            "imports": self._extract_imports(code),
            "component_type": component_type
        }

    def generate_page(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        디자인 정보를 기반으로 전체 페이지를 생성합니다.
        
        Args:
            task: 페이지 생성 태스크 정보
            
        Returns:
            생성된 페이지 코드
        """
        # 태스크에서 필요한 정보 추출
        page_name = task.get("page_name", "Page")
        screen_design = task.get("screen_design", {})
        components = task.get("components", [])
        routing = task.get("routing", {})
        framework = task.get("framework", self.config["framework"])
        use_typescript = task.get("typescript", self.config["typescript"])
        
        # 프롬프트 생성
        prompt = self._create_page_generation_prompt(
            page_name, screen_design, components, routing, 
            framework, use_typescript
        )
        
        # 테스트 중에는 실제 API 호출 대신 더미 응답 사용
        if not self.client:
            response = f"```jsx\nimport React from 'react';\n\nconst {page_name} = () => {{\n  return (\n    <div className=\"page-container\">\n      <h1>{page_name}</h1>\n      <div className=\"content\">\n        {page_name} 내용\n      </div>\n    </div>\n  );\n}};\n\nexport default {page_name};\n```"
        else:
            # AI 모델에 요청
            response = self.client.generate(prompt)
        
        # 코드 추출
        code = self._extract_code_from_response(response)
        
        # 결과 반환
        return {
            "status": "generated",
            "page_name": page_name,
            "framework": framework,
            "typescript": use_typescript,
            "code": code,
            "imports": self._extract_imports(code)
        }

    def refactor_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        기존 코드를 리팩토링합니다.
        
        Args:
            task: 리팩토링 태스크 정보
            
        Returns:
            리팩토링된 코드
        """
        # 태스크에서 필요한 정보 추출
        code = task.get("code", "")
        goals = task.get("goals", ["가독성", "재사용성", "유지보수성"])
        
        if not code:
            return {
                "status": "error",
                "message": "리팩토링할 코드가 제공되지 않았습니다."
            }
        
        # 프롬프트 생성
        prompt = self._create_refactoring_prompt(code, goals)
        
        # 테스트 중에는 실제 API 호출 대신 더미 응답 사용
        if not self.client:
            response = f"```jsx\n// 리팩토링된 코드\nimport React from 'react';\n\n// 컴포넌트 분리\nconst Header = ({{ title }}) => (\n  <header>\n    <h1>{{title}}</h1>\n  </header>\n);\n\nconst Content = ({{ children }}) => (\n  <main className=\"content\">\n    {{children}}\n  </main>\n);\n\nconst Footer = () => (\n  <footer>\n    <p>&copy; 2023 Company Name</p>\n  </footer>\n);\n\n// 메인 컴포넌트\nconst App = ({{ data }}) => (\n  <div className=\"app\">\n    <Header title=\"Welcome\" />\n    <Content>\n      {{data.map(item => (\n        <p key={{item.id}}>{{item.name}}</p>\n      ))}}\n    </Content>\n    <Footer />\n  </div>\n);\n\nexport default App;\n```"
        else:
            # AI 모델에 요청
            response = self.client.generate(prompt)
        
        # 코드 추출
        refactored_code = self._extract_code_from_response(response)
        
        # 결과 반환
        return {
            "status": "refactored",
            "original_code": code,
            "refactored_code": refactored_code,
            "goals": goals,
            "imports": self._extract_imports(refactored_code)
        }

    def optimize_performance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        컴포넌트 성능을 최적화합니다.
        
        Args:
            task: 성능 최적화 태스크 정보
            
        Returns:
            최적화된 코드
        """
        # 태스크에서 필요한 정보 추출
        code = task.get("code", "")
        targets = task.get("targets", ["렌더링", "메모이제이션", "불필요한 리렌더링"])
        
        if not code:
            return {
                "status": "error",
                "message": "최적화할 코드가 제공되지 않았습니다."
            }
        
        # 프롬프트 생성
        prompt = self._create_optimization_prompt(code, targets)
        
        # 테스트 중에는 실제 API 호출 대신 더미 응답 사용
        if not self.client:
            response = f"```jsx\n// 최적화된 코드\nimport React, {{ useMemo, useCallback }} from 'react';\n\nconst OptimizedComponent = ({{ data }}) => {{\n  // 메모이제이션을 통한 최적화\n  const processedData = useMemo(() => {{\n    return data.map(item => item * 2);\n  }}, [data]);\n  \n  // 콜백 최적화\n  const handleClick = useCallback(() => {{\n    console.log('Clicked!');\n  }}, []);\n  \n  return (\n    <div onClick={handleClick}>\n      {{processedData.map(item => (\n        <span key={{item}}>{{item}}</span>\n      ))}}\n    </div>\n  );\n}};\n\nexport default React.memo(OptimizedComponent);\n```"
        else:
            # AI 모델에 요청
            response = self.client.generate(prompt)
        
        # 코드 추출
        code = self._extract_code_from_response(response)
        
        # 결과 반환
        return {
            "status": "optimized",
            "targets": targets,
            "code": code,
            "imports": self._extract_imports(code),
            "optimizations": self._extract_optimizations(code, targets)
        }

    # 프롬프트 생성 메서드
    def _create_component_generation_prompt(
        self, component_name: str, component_type: str, 
        design_data: Dict[str, Any], framework: str, 
        use_typescript: bool, component_library: str
    ) -> str:
        """
        컴포넌트 생성을 위한 프롬프트를 생성합니다.
        """
        language = "TypeScript" if use_typescript else "JavaScript"
        extension = "tsx" if use_typescript else "jsx"
        
        prompt = f"""당신은 숙련된 프론트엔드 개발자입니다. 디자인 정보를 기반으로 {framework} {component_type} 컴포넌트를 {language}로 생성해야 합니다.

컴포넌트 이름: {component_name}
프레임워크: {framework}
언어: {language}
컴포넌트 라이브러리: {component_library if component_library != 'none' else '사용하지 않음'}

디자인 정보:
```json
{json.dumps(design_data, ensure_ascii=False, indent=2)}
```

요구사항:
1. 코드는 깔끔하고 가독성이 좋아야 합니다.
2. 필요한 모든 import문을 포함해야 합니다.
3. 적절한 PropTypes(또는 TypeScript 타입)를 정의해야 합니다.
4. 디자인 정보와 일치하는 스타일을 구현해야 합니다.

파일 이름: {component_name}.{extension}

컴포넌트 코드만 제공해주세요:"""
        
        return prompt

    def _create_page_generation_prompt(
        self, page_name: str, screen_design: Dict[str, Any], 
        components: List[Dict[str, Any]], routing: Dict[str, Any], 
        framework: str, use_typescript: bool
    ) -> str:
        """
        페이지 생성을 위한 프롬프트를 생성합니다.
        """
        language = "TypeScript" if use_typescript else "JavaScript"
        extension = "tsx" if use_typescript else "jsx"
        
        components_str = json.dumps(components, ensure_ascii=False, indent=2)
        screen_design_str = json.dumps(screen_design, ensure_ascii=False, indent=2)
        
        prompt = f"""당신은 숙련된 프론트엔드 개발자입니다. 디자인 정보와 컴포넌트 목록을 기반으로 {framework} 페이지를 {language}로 생성해야 합니다.

페이지 이름: {page_name}
프레임워크: {framework}
언어: {language}

화면 디자인:
```json
{screen_design_str}
```

사용할 컴포넌트:
```json
{components_str}
```

라우팅 정보:
- 경로: {routing.get('path', f'/{page_name.lower()}')}

페이지 코드만 제공해주세요:"""
        
        return prompt

    def _create_refactoring_prompt(self, code: str, goals: List[str]) -> str:
        """
        코드 리팩토링을 위한 프롬프트를 생성합니다.
        """
        goals_str = "\n".join([f"- {goal}" for goal in goals])
        
        prompt = f"""당신은 숙련된 프론트엔드 개발자입니다. 다음 코드를 리팩토링해야 합니다.

원본 코드:
```
{code}
```

리팩토링 목표:
{goals_str}

리팩토링된 코드만 제공해주세요:"""
        
        return prompt

    def _create_optimization_prompt(self, code: str, targets: List[str]) -> str:
        """
        성능 최적화를 위한 프롬프트를 생성합니다.
        """
        targets_str = "\n".join([f"- {target}" for target in targets])
        
        prompt = f"""당신은 React 성능 최적화 전문가입니다. 다음 코드의 성능을 최적화해야 합니다.

원본 코드:
```
{code}
```

최적화 대상:
{targets_str}

최적화된 코드만 제공해주세요:"""
        
        return prompt

    # 유틸리티 메서드
    def _extract_code_from_response(self, response: str) -> str:
        """
        AI 응답에서 코드 블록을 추출합니다.
        """
        if "```" in response:
            # 코드 블록 추출
            code_blocks = response.split("```")
            if len(code_blocks) >= 3:
                # 첫 번째 코드 블록 사용
                code = code_blocks[1]
                # 언어 표시 제거 (있는 경우)
                if code.startswith("jsx") or code.startswith("tsx") or code.startswith("javascript") or code.startswith("typescript"):
                    code = code.split("\n", 1)[1]
                return code.strip()
        
        # 코드 블록이 없는 경우 전체 응답 반환
        return response.strip()

    def _extract_imports(self, code: str) -> List[str]:
        """
        코드에서 import 문을 추출합니다.
        """
        imports = []
        for line in code.split("\n"):
            if line.strip().startswith("import "):
                imports.append(line.strip())
        return imports

    def _extract_optimizations(self, code: str, targets: List[str]) -> List[str]:
        """
        코드에서 적용된 최적화 방법을 추출합니다.
        """
        optimizations = []
        for target in targets:
            if target.lower() in code.lower():
                optimizations.append(target)
        return optimizations


# 테스트 코드
if __name__ == "__main__":
    # 환경변수 설정 또는 직접 API 키 전달
    agent = FrontendAgentOllama(model="llama3:latest")
    
    # 테스트 실행
    result = agent.run_task("React Native 버튼 컴포넌트를 만들어주세요.")
    print(result) 