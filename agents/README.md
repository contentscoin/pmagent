# PPLShop 에이전트 시스템

이 폴더는 PPLShop 프로젝트에서 사용되는 AI 에이전트 모듈을 포함합니다. 각 에이전트는 특정 역할을 담당하며, 함께 협업하여 프로젝트 개발을 지원합니다.

## 에이전트 구조

- **PM Agent (Orchestrator)**: 프로젝트 관리 및 다른 에이전트 간의 조율을 담당합니다.
- **Designer Agent**: UI/UX 디자인 관련 작업을 수행합니다.
- **Frontend Agent**: React Native/React 기반 프론트엔드 개발을 담당합니다.
- **Backend Agent**: API 및 서버 측 기능 개발을 담당합니다.
- **AI Engineer Agent**: AI/ML 기능 통합 및 개발을 담당합니다.

## 사용 방법

```python
# 기본 사용 예시
from agents import PMAgent, DesignerAgent, FrontendAgent, BackendAgent, AIEngineerAgent

# PM Agent 초기화 및 사용
pm_agent = PMAgent()
project_status = pm_agent.get_project_status()

# Designer Agent 초기화 및 사용
designer_agent = DesignerAgent()
button_design = designer_agent.generate_design("button", {"label": "로그인", "primary": True})

# Frontend Agent 초기화 및 사용
frontend_agent = FrontendAgent()
button_component = frontend_agent.generate_component("ButtonComponent", button_design)

# Backend Agent 초기화 및 사용
backend_agent = BackendAgent()
api_endpoint = backend_agent.create_api_endpoint({"name": "products"})

# AI Engineer Agent 초기화 및 사용
ai_engineer_agent = AIEngineerAgent()
recommendation_service = ai_engineer_agent.create_recommendation_system("products")
```

## 환경 설정

모든 에이전트는 OpenAI API 키가 필요합니다. 다음과 같이 환경 변수로 설정하거나 직접 전달할 수 있습니다:

```python
# 환경 변수 설정
import os
os.environ["OPENAI_API_KEY"] = "your-api-key"

# 또는 에이전트 초기화 시 직접 전달
pm_agent = PMAgent(api_key="your-api-key")
```

## 에이전트 간 협업

PM Agent(Orchestrator)를 통해 다른 에이전트들 간의 협업을 조율할 수 있습니다:

```python
# PM Agent가 다른 에이전트에게 작업 할당
pm_agent.assign_task("designer", {"task": "로그인 화면 디자인", "priority": "high"})
pm_agent.assign_task("frontend", {"task": "로그인 컴포넌트 구현", "priority": "medium"})
```

## 커스터마이징

각 에이전트는 내부 메서드를 오버라이드하여 커스터마이징할 수 있습니다:

```python
class CustomPMAgent(PMAgent):
    def _setup_tools(self):
        # 맞춤형 도구 설정
        custom_tools = super()._setup_tools()
        # 추가 도구 구성...
        return custom_tools
``` 