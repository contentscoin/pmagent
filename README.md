# PMAgent MCP Server

PM Agent MCP(Model Context Protocol) 서버는 프로젝트 관리 및 다양한 AI 에이전트 조정을 위한 JSON-RPC 2.0 기반 서버입니다.

## 주요 기능

- 프로젝트 및 태스크 관리
- 다양한 AI 에이전트 관리 (PM, 디자이너, 프론트엔드, 백엔드, AI 엔지니어)
- 데이터 지속성 (로컬 파일 저장)
- Cursor 편집기와의 통합

## 설치

```bash
# 저장소 복제
git clone https://github.com/your-username/pmagent-mcp-server.git
cd pmagent-mcp-server

# 의존성 설치
pip install -r requirements.txt
```

## 실행

```bash
# 서버 실행
python server.py
```

서버는 기본적으로 `http://localhost:8082`에서 실행됩니다.

## API 엔드포인트

- **메인 API**: `/api` - JSON-RPC 2.0 요청 처리
- **루트**: `/` - 서버 상태 확인

## 주요 메서드

### 프로젝트 관리

- `request_planning`: 새 요청 등록 및 태스크 계획
- `get_next_task`: 다음 대기 중인 태스크 가져오기
- `mark_task_done`: 태스크 완료 처리
- `approve_task_completion`: 태스크 완료 승인
- `approve_request_completion`: 전체 요청 완료 승인

### 세션 및 데이터 관리

- `create_session`: 새 세션 생성
- `export_data`: 세션 데이터 내보내기 (JSON 형식)
- `import_data`: 데이터 가져오기

### 에이전트 관리

- `create_agent`: 새 에이전트 생성
- `get_agent`: 에이전트 정보 조회
- `list_agents`: 에이전트 목록 조회
- `assign_task_to_agent`: 에이전트에 태스크 할당
- `get_agent_result`: 에이전트 태스크 결과 조회

## 데이터 지속성

PMAgent MCP 서버는 세션 데이터를 로컬 파일 시스템에 JSON 형식으로 저장합니다.

### 데이터 저장 경로

- 세션 데이터: `api/data/sessions/{session_id}.json`

### 데이터 관리 메서드

- `export_data`: 현재 세션 데이터를 JSON으로 내보내고 파일로 저장
- `import_data`: 파일에서 데이터 불러오기 (파라미터: "fromFile": true)

자세한 내용은 [데이터 저장소 문서](docs/data_storage.md)를 참조하세요.

## Cursor 통합

PMAgent MCP 서버는 Cursor 편집기와의 통합을 지원합니다. Cursor의 내장 MCP 클라이언트를 통해 서버에 연결하고 다양한 기능을 사용할 수 있습니다.

### 통합 단계

1. PMAgent MCP 서버 실행
2. Cursor에서 `MCP: Add Server` 명령을 사용하여 서버 등록 (`http://localhost:8082`)
3. 메서드 호출 및 에이전트 활용

자세한 내용은 [통합 계획 문서](docs/integration_plan.md)를 참조하세요.

## 에이전트 유형

### PM 에이전트
프로젝트 관리 및 조정을 담당합니다. 요구사항을 분석하고 태스크를 계획합니다.

### 디자이너 에이전트
UI/UX 디자인을 생성합니다. 컴포넌트, 화면, 테마 등을 디자인합니다.

### 프론트엔드 에이전트
사용자 인터페이스 구현을 담당합니다. 디자이너의 결과물을 코드로 구현합니다.

### 백엔드 에이전트
서버 측 로직 및 API를 구현합니다. 데이터베이스 모델 및 비즈니스 로직을 개발합니다.

### AI 엔지니어 에이전트
AI 기능 및 모델을 통합합니다.

## 문서

- [API 문서](docs/api.md)
- [에이전트 시스템](docs/agents.md)
- [데이터 저장소](docs/data_storage.md)
- [Cursor 통합 계획](docs/integration_plan.md)
- [CLI 사용법](docs/cli_usage.md)
- [설치 가이드](docs/INSTALLATION.md)
- [로드맵](docs/ROADMAP.md)

## 라이센스

MIT

## 설정 파일

프로젝트의 모든 설정은 `config.json` 파일에 통합되어 있습니다:

```json
{
  "url": "https://successive-glenn-contentscoin-34b6608c.koyeb.app",
  "apiKey": "0c8f6386-e443-4b8b-95ba-22a40d5f5e38",
  "mcpUrl": "https://successive-glenn-contentscoin-34b6608c.koyeb.app/mcp",
  "localUrl": "http://localhost:4000/api/mcp",
  "environments": {
    "production": "https://successive-glenn-contentscoin-34b6608c.koyeb.app",
    "local": "http://localhost:4000/api/mcp"
  },
  "client": {
    // MCP 클라이언트 설정...
  }
}
```

### MCP 서버 테스트

MCP 서버를 테스트하려면 다음 명령을 사용하세요:

```bash
# 프로덕션 서버 테스트
npm run test:mcp

# 로컬 서버 테스트
npm run test:mcp:local
```

이 스크립트는 MCP 서버에 연결하여 다음 작업을 수행합니다:
1. 서버 정보 확인
2. 사용 가능한 도구 목록 가져오기
3. 프로젝트 목록 가져오기
4. 테스트 프로젝트 및 태스크 생성

## Smithery 설정 및 등록

PMAgent MCP Server를 Cursor에 등록하려면 다음 명령을 사용하세요:

```bash
# 간단한 스미더리 등록 (권장)
npm run smithery:simple

# 기존 방식의 등록
npm run smithery:register

# 로컬 서버 모드로 등록
npm run smithery:local

# 기존 설치 제거 후 재설치
npm run smithery:reinstall

# 스미더리 설정 파일 제거 (문제 해결시)
npm run smithery:clean
```

만약 스크립트를 통한 방법이 실패한다면, `smithery_install_commands.txt` 파일에 있는 명령어를 터미널에서 직접 실행해보세요.

추가 옵션은 다음 명령으로 확인할 수 있습니다:

```bash
node register_smithery.js --help
```

### 설정 파일

- `config.json`: 메인 설정 파일로 URL과 API 키 정보를 포함합니다.
- `smithery-simple.json`: Smithery 서버 상세 설정을 포함합니다.

### 문제 해결

스미더리 등록 중 "No connection configuration found" 오류가 발생하면 다음 단계를 시도하세요:

1. 스미더리 설정 초기화: `npm run smithery:clean`
2. 간단한 등록 스크립트 사용: `npm run smithery:simple`
3. Cursor를 재시작한 후 스미더리가 정상적으로 표시되는지 확인