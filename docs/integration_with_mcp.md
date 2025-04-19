# MCP 통합 가이드

## 개요

PPLShop 프로젝트는 MCP(Model Context Protocol)와의 통합을 지원합니다. MCP는 에이전트가 다양한 외부 서비스(Unity, GitHub, Figma, 데이터베이스 등)와 상호 작용할 수 있게 해주는 프로토콜입니다. 이 문서는 에이전트와 MCP의 통합 방법을 설명합니다.

## MCP란?

MCP(Model Context Protocol)는 AI 모델이 외부 시스템과 상호 작용할 수 있게 해주는 프로토콜입니다. 이를 통해 다음과 같은 작업이 가능합니다:

1. **Unity 게임 엔진** 제어
2. **GitHub** 저장소 관리
3. **Figma** 디자인 데이터 가져오기
4. **데이터베이스** 조회 및 조작

## 설정 방법

### 1. 필요한 패키지 설치

```bash
pip install unity-mcp-client
```

### 2. 환경 변수 설정

```bash
# Unity MCP 호스트
export UNITY_MCP_HOST="http://localhost:8045"

# GitHub 토큰
export GITHUB_TOKEN="your-github-token"

# Figma 토큰
export FIGMA_TOKEN="your-figma-token"

# 데이터베이스 연결 문자열
export DB_CONNECTION_STRING="your-db-connection-string"
```

### 3. MCP 헬퍼 생성

```python
from agents.mcp_helper import MCPAgentHelper

# 환경 변수에서 설정을 가져와 생성
mcp_helper = MCPAgentHelper()

# 또는 직접 설정값 전달
mcp_helper = MCPAgentHelper(
    unity_mcp_host="http://localhost:8045",
    github_token="your-github-token",
    figma_token="your-figma-token",
    db_connection_string="your-db-connection-string"
)
```

## AgentFactory와 함께 사용하기

```python
from agents.agent_factory import AgentFactory

factory = AgentFactory()

# MCP 헬퍼 생성
mcp_helper = factory.create_mcp_helper()

# MCP 지원 포함하여 백엔드 에이전트 생성
backend_agent = factory.create_agent(
    "backend",
    use_mcp=True,  # MCP 사용 설정
    mcp_helper=mcp_helper  # 또는 헬퍼를 전달하지 않고 자동 생성
)

# Ollama 에이전트와 함께 사용
backend_ollama = factory.create_agent(
    "backend_ollama",
    ollama_model="codellama:7b-instruct",
    use_mcp=True
)
```

## MCP 지원 서비스 확인

```python
# 사용 가능한 MCP 서비스 확인
available_mcps = mcp_helper.get_available_mcps()
print(available_mcps)
# 출력 예: {"unity_mcp": True, "github_mcp": True, "figma_mcp": False, "db_mcp": True}

# 개별 서비스 확인
if mcp_helper.has_unity_mcp():
    print("Unity MCP 사용 가능")
    
if mcp_helper.has_github_mcp():
    print("GitHub MCP 사용 가능")
```

## Unity MCP 사용하기

Unity MCP 서버가 실행 중이어야 합니다.

```python
# Unity 게임 오브젝트 생성
if mcp_helper.has_unity_mcp():
    unity_mcp = mcp_helper.unity_mcp
    
    # 게임 오브젝트 생성
    unity_mcp.create_gameobject("Cube")
    
    # 컴포넌트 추가
    unity_mcp.add_component_to_gameobject("Cube", "BoxCollider")
    
    # 속성 설정
    unity_mcp.set_component_property("Cube", "Transform", "position", {"x": 0, "y": 1, "z": 0})
```

## GitHub MCP 사용하기

```python
# GitHub에 파일 커밋
if mcp_helper.has_github_mcp():
    result = mcp_helper.commit_to_github(
        repository="user/repo",
        file_path="src/components/Button.js",
        content="// Button component code\nfunction Button() { return <button>Click me</button>; }",
        commit_message="Add Button component"
    )
    print(result["message"])
```

## Figma MCP 사용하기

```python
# Figma 디자인 데이터 가져오기
if mcp_helper.has_figma_mcp():
    design_data = mcp_helper.get_design_data("https://figma.com/file/example")
    print(f"디자인 이름: {design_data['name']}")
    print(f"컴포넌트: {design_data['components']}")
    print(f"색상: {design_data['colors']}")
```

## 데이터베이스 MCP 사용하기

```python
# SQL 쿼리 실행
if mcp_helper.has_db_mcp():
    result = mcp_helper.execute_sql(
        "SELECT * FROM users WHERE status = :status LIMIT 10",
        {"status": "active"}
    )
    print(result["message"])
```

## 에러 처리

```python
try:
    # MCP 기능 호출
    result = mcp_helper.commit_to_github(
        repository="user/repo",
        file_path="src/components/Button.js",
        content="...",
        commit_message="Add Button component"
    )
except ValueError as e:
    print(f"MCP 에러: {str(e)}")
    # 예: "GitHub MCP가 구성되지 않았습니다. GitHub 토큰을 확인하세요."
```

## 유의사항

1. Unity MCP를 사용하려면 별도의 Unity 프로젝트와 MCP 서버가 필요합니다.
2. 현재 구현은 실제 API 호출을 시뮬레이션하는 더미 클래스를 포함합니다(테스트 목적).
3. 프로덕션 환경에서는 각 MCP 서비스의 실제 구현으로 대체해야 합니다.
4. API 토큰은 안전하게 관리하고 소스 코드에 직접 포함하지 마세요. 