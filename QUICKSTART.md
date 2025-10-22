# PMAgent 빠른 시작 가이드

이 가이드는 PMAgent MCP 서버를 빠르게 시작하고 사용하는 방법을 안내합니다.

## 목차

1. [사전 요구사항](#사전-요구사항)
2. [설치](#설치)
3. [환경 설정](#환경-설정)
4. [서버 시작](#서버-시작)
5. [기본 사용법](#기본-사용법)
6. [문제 해결](#문제-해결)

## 사전 요구사항

- Python 3.10 이상
- pip (Python 패키지 관리자)
- (선택) Ollama 로컬 LLM 서버

## 설치

### 1. 저장소 클론

```bash
git clone https://github.com/contentscoin/pmagent.git
cd pmagent
```

### 2. Python 패키지 설치

```bash
# 핵심 의존성만 설치 (빠른 시작)
pip install fastapi uvicorn pydantic sqlalchemy pyjwt python-dotenv aiohttp requests

# 또는 전체 의존성 설치
pip install -r requirements.txt
```

## 환경 설정

### 1. 환경 변수 파일 생성

`.env.example` 파일을 복사하여 `.env` 파일을 생성합니다:

```bash
cp .env.example .env
```

### 2. 필수 환경 변수 설정

`.env` 파일을 편집하여 관리자 비밀번호를 설정합니다:

```bash
# 강력한 비밀번호로 변경하세요
DEFAULT_ADMIN_PASSWORD=your_strong_password_here
```

**⚠️ 중요**: 프로덕션 환경에서는 반드시 강력한 비밀번호를 설정하세요!

### 3. 선택 사항: Ollama 설정

Ollama를 사용하려면 다음 설정을 추가하세요:

```bash
OLLAMA_API_BASE=http://localhost:11434/api
OLLAMA_MODEL=llama3.2:latest
```

## 서버 시작

### 방법 1: 실행 스크립트 사용 (권장)

```bash
python run_server.py
```

### 방법 2: 모듈로 실행

```bash
python -m pmagent.mcp_server
```

### 서버 시작 확인

서버가 성공적으로 시작되면 다음과 같은 메시지가 표시됩니다:

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8082
```

웹 브라우저에서 `http://localhost:8082`를 열어 서버 상태를 확인할 수 있습니다.

## 기본 사용법

### CLI 도구 사용

PMAgent는 명령줄 관리 도구를 제공합니다:

#### 1. 서버 상태 확인

```bash
python cli.py check
```

#### 2. 사용 가능한 MCP 도구 조회

```bash
python cli.py tools
```

#### 3. 프로젝트 생성

```bash
python cli.py create-project "나의 첫 프로젝트" --description "테스트 프로젝트입니다"
```

#### 4. 프로젝트 목록 조회

```bash
python cli.py projects
```

#### 5. 작업 생성

```bash
python cli.py create-task <PROJECT_ID> "UI 디자인" --description "메인 화면 UI 디자인"
```

#### 6. 작업 목록 조회

```bash
python cli.py tasks <PROJECT_ID>
```

#### 7. 데모 실행

전체 기능을 한 번에 테스트하려면:

```bash
python cli.py demo
```

### 테스트 클라이언트 사용

자동화된 테스트를 실행하려면:

```bash
python test_client.py
```

### HTTP API 직접 호출

#### 서버 상태 확인

```bash
curl http://localhost:8082/
```

#### MCP JSON-RPC 호출

```bash
curl -X POST http://localhost:8082/mcp/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "list_projects",
    "params": {}
  }'
```

## 주요 기능

### 1. 프로젝트 관리

- **create_project**: 새 프로젝트 생성
- **list_projects**: 프로젝트 목록 조회
- **get_project**: 특정 프로젝트 상세 조회
- **update_project**: 프로젝트 정보 수정

### 2. 작업 관리

- **create_task**: 새 작업 생성
- **list_tasks**: 작업 목록 조회
- **get_task**: 특정 작업 상세 조회
- **update_task**: 작업 정보 수정
- **assign_task**: 작업을 에이전트에 할당

### 3. 에이전트 관리

- **list_agents**: 사용 가능한 에이전트 목록
- **get_agent_status**: 에이전트 상태 조회
- **execute_agent_task**: 에이전트에 작업 실행 요청

## 문제 해결

### 서버가 시작되지 않는 경우

#### 1. 포트 충돌 확인

8082 포트가 이미 사용 중인지 확인:

```bash
# Linux/Mac
lsof -i :8082

# Windows
netstat -ano | findstr :8082
```

다른 포트로 변경하려면 `.env` 파일 수정:

```bash
SERVER_PORT=8083
```

#### 2. 의존성 확인

필요한 패키지가 설치되어 있는지 확인:

```bash
python -c "import fastapi, uvicorn, pydantic, sqlalchemy; print('OK')"
```

#### 3. 데이터베이스 초기화 오류

데이터 디렉토리 권한 확인:

```bash
mkdir -p data pmagent/data
chmod 755 data pmagent/data
```

### CLI 도구가 서버에 연결하지 못하는 경우

1. 서버가 실행 중인지 확인
2. 올바른 URL 사용:

```bash
python cli.py --url http://localhost:8082 check
```

### 관리자 비밀번호 분실

비밀번호를 잊었다면:

1. 서버를 중지
2. 데이터베이스 파일 삭제:
   ```bash
   rm -rf pmagent/data/*.sqlite
   ```
3. `.env` 파일에서 `DEFAULT_ADMIN_PASSWORD` 재설정
4. 서버 재시작

### Ollama 연결 오류

1. Ollama가 실행 중인지 확인:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. `.env`에서 올바른 URL 설정 확인

## 다음 단계

- [API 문서](docs/API.md) - 전체 API 레퍼런스
- [Cursor 통합](docs/integration_plan.md) - Cursor 편집기와 통합
- [에이전트 가이드](docs/agents.md) - AI 에이전트 활용법
- [배포 가이드](docs/INSTALLATION.md) - 프로덕션 배포

## 도움말

문제가 계속되면 다음을 확인하세요:

1. 서버 로그: `pmagent.log`
2. GitHub Issues: https://github.com/contentscoin/pmagent/issues
3. README: [README.md](README.md)

---

**즐거운 개발 되세요! 🚀**
