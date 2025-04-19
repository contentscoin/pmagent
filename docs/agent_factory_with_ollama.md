# Ollama 기반 에이전트 통합 가이드

## 개요

PPLShop 프로젝트는 이제 OpenAI API뿐만 아니라 Ollama를 통한 로컬 LLM도 지원합니다. 이 문서는 AgentFactory를 사용하여 Ollama 기반 에이전트를 생성하고 사용하는 방법을 설명합니다.

## 사전 요구 사항

1. [Ollama](https://ollama.ai) 설치
2. 필요한 모델 다운로드 (예: `llama3:latest`, `codellama:7b-instruct`)
   ```bash
   ollama pull llama3:latest
   ollama pull codellama:7b-instruct
   ```
3. Ollama 서버 실행
   ```bash
   ollama serve
   ```

## AgentFactory 사용법

### 1. Ollama 에이전트 생성하기

```python
from agents.agent_factory import AgentFactory

factory = AgentFactory()

# Ollama 프론트엔드 에이전트 생성
frontend_agent = factory.create_agent(
    "frontend_ollama",  # frontend_ollama로 직접 지정
    ollama_model="llama3:latest",  # 사용할 모델
    ollama_api_base="http://localhost:11434/api",  # API 엔드포인트
    temperature=0.7  # 생성 온도
)

# Ollama 백엔드 에이전트 생성
backend_agent = factory.create_agent(
    "backend_ollama",  # backend_ollama로 직접 지정
    ollama_model="codellama:7b-instruct",  # 백엔드 개발에 적합한 코드 모델
    ollama_api_base="http://localhost:11434/api"
)
```

### 2. 기존 에이전트 타입으로 Ollama 사용하기

```python
from agents.agent_factory import AgentFactory

factory = AgentFactory()

# use_ollama 플래그로 프론트엔드 에이전트를 Ollama 버전으로 생성
frontend_agent = factory.create_agent(
    "frontend",  # 일반 프론트엔드 에이전트 타입
    use_ollama=True,  # Ollama 사용 설정
    ollama_model="llama3:latest"
)

# use_ollama 플래그로 백엔드 에이전트를 Ollama 버전으로 생성
backend_agent = factory.create_agent(
    "backend",  # 일반 백엔드 에이전트 타입
    use_ollama=True,  # Ollama 사용 설정
    ollama_model="codellama:7b-instruct"
)
```

### 3. 모든 에이전트를 Ollama 버전으로 생성하기

```python
from agents.agent_factory import AgentFactory

factory = AgentFactory()

# 모든 에이전트를 Ollama 버전으로 생성 (프론트엔드와 백엔드만 변경됨)
agents = factory.create_all_agents(
    use_ollama=True,
    ollama_model="llama3:latest"
)

# 각 에이전트 사용
pm_agent = agents["pm"]  # 일반 PM 에이전트 (Ollama 버전 없음)
frontend_agent = agents["frontend"]  # Ollama 기반 프론트엔드 에이전트
backend_agent = agents["backend"]  # Ollama 기반 백엔드 에이전트
```

## 에이전트 기능 사용하기

### 프론트엔드 에이전트 (FrontendAgentOllama)

```python
# 컴포넌트 생성
button_component = frontend_agent.generate_component(
    "Button", 
    {"type": "button", "color": "primary"}
)

# 화면 구현
home_screen = frontend_agent.implement_screen(
    "HomeScreen",
    ["Button", "Card", "Header"],
    {"layout": "flex", "theme": "light"}
)

print(button_component["code"])  # 컴포넌트 코드 출력
print(home_screen["code"])  # 화면 코드 출력
```

### 백엔드 에이전트 (BackendAgentOllama)

```python
# API 엔드포인트 생성
api_endpoint = backend_agent.create_api_endpoint(
    "사용자 프로필 정보를 가져오는 GET API 엔드포인트"
)

# 데이터베이스 스키마 생성
db_schema = backend_agent.create_database_schema(
    "온라인 쇼핑몰 제품 카탈로그 데이터베이스 스키마"
)

# 인증 시스템 생성
auth_system = backend_agent.create_authentication_system(
    "OAuth 및 JWT를 사용한 사용자 인증 시스템"
)

print(api_endpoint["code"])  # API 엔드포인트 코드 출력
print(db_schema["code"])  # 데이터베이스 스키마 코드 출력
print(auth_system["code"])  # 인증 시스템 코드 출력
```

## MCP 통합

AgentFactory는 MCP(Model Context Protocol) 지원도 제공합니다. Ollama 에이전트와 함께 MCP를 사용하려면:

```python
from agents.agent_factory import AgentFactory

factory = AgentFactory()

# MCP 헬퍼 생성
mcp_helper = factory.create_mcp_helper(
    unity_mcp_host="http://localhost:8045",
    github_token="your-github-token",
    figma_token="your-figma-token"
)

# MCP 지원 포함하여 Ollama 에이전트 생성
backend_agent = factory.create_agent(
    "backend_ollama",
    ollama_model="codellama:7b-instruct",
    use_mcp=True,  # MCP 사용 설정
    mcp_helper=mcp_helper  # 또는 자동 생성 사용 (use_mcp=True만 설정)
)
```

## 환경 변수

다음 환경 변수를 설정하여 기본값을 구성할 수 있습니다:

```bash
# Ollama 설정
export OLLAMA_API_BASE="http://localhost:11434/api"

# API 키
export OPENAI_API_KEY="your-openai-api-key"

# MCP 관련 설정
export UNITY_MCP_HOST="http://localhost:8045"
export GITHUB_TOKEN="your-github-token"
export FIGMA_TOKEN="your-figma-token"
export DB_CONNECTION_STRING="your-db-connection-string"
```

## 유의사항

1. Ollama 사용 시 필요한 모델이 먼저 설치되어 있어야 합니다.
2. 일반 API 기반 에이전트보다 품질이 낮을 수 있습니다.
3. Ollama 서버는 로컬에서 실행 중이어야 합니다.
4. PM 에이전트와 Designer 에이전트는 현재 Ollama 버전이 없습니다.

## 문제 해결

- Ollama 서버 연결 실패: `OLLAMA_API_BASE` 환경 변수나 `ollama_api_base` 매개변수가 올바른지 확인하세요.
- 모델 로드 실패: 해당 모델을 `ollama pull` 명령으로 다운로드했는지 확인하세요.
- 응답 품질 문제: 더 큰 모델(예: 7B 대신 70B)을 사용하거나 temperature 값을 조정해 보세요. 