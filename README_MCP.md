# PMAgent MCP Server

PMAgent MCP Server는 프로젝트 관리를 위한 Model Context Protocol(MCP) 기반 서버입니다. 주로 AI 에이전트가 태스크를 관리하고 작업 흐름을 조율하는 데 활용됩니다.

## 주요 기능

- 프로젝트 요청 및 태스크 관리
- 태스크 진행 상황 추적
- 태스크 승인 및 완료 처리
- JSON-RPC 2.0 호환 API
- WebSocket 지원
- Cursor 편집기 통합

## 설치

### 요구 사항

- Python 3.8 이상
- FastAPI
- Uvicorn
- aiohttp (클라이언트용)
- 기타 의존성은 requirements.txt 참조

### 설치 방법

```bash
# 저장소 복제
git clone https://github.com/your-username/pmagent-mcp-server.git
cd pmagent-mcp-server

# 의존성 설치
pip install -r requirements.txt
```

## 실행 방법

### 서버 실행

```bash
# 기본 설정으로 실행
python run_server.py

# 사용자 지정 설정 실행
python run_server.py --host 127.0.0.1 --port 8082 --data-dir ./custom_data
```

서버는 기본적으로 `http://localhost:8082`에서 실행됩니다.

### 테스트 클라이언트 실행

```bash
# 테스트 클라이언트 실행
python test_task_client.py

# 사용자 지정 서버 주소 지정
python test_task_client.py --server http://localhost:8082
```

## API 엔드포인트

- **도구 목록**: `/tools` - 사용 가능한 MCP 도구 목록 제공
- **도구 호출**: `/invoke` - MCP 도구 호출 (POST)
- **루트**: `/` - 서버 상태 확인 또는 JSON-RPC 요청 처리
- **WebSocket**: `/ws` 또는 `/mcp` - WebSocket 연결 엔드포인트

## MCP 도구 목록

PMAgent MCP 서버는 다음과 같은 MCP 도구를 제공합니다:

| 도구 이름 | 설명 | 주요 매개변수 |
|----------|------|-------------|
| `request_planning` | 새 요청을 등록하고 태스크를 계획 | `originalRequest`, `tasks` |
| `get_next_task` | 다음 대기 중인 태스크를 가져옴 | `requestId` |
| `mark_task_done` | 태스크를 완료 상태로 표시 | `requestId`, `taskId` |
| `approve_task_completion` | 완료된 태스크를 승인 | `requestId`, `taskId` |
| `approve_request_completion` | 요청 전체의 완료를 승인 | `requestId` |
| `add_tasks_to_request` | 기존 요청에 새 태스크를 추가 | `requestId`, `tasks` |
| `update_task` | 태스크 정보를 업데이트 | `requestId`, `taskId`, `title`, `description` |
| `delete_task` | 태스크를 삭제 | `requestId`, `taskId` |
| `list_requests` | 모든 요청 목록을 가져옴 | - |
| `open_task_details` | 태스크 상세 정보를 가져옴 | `taskId` |

## Cursor 통합

PMAgent MCP 서버는 Cursor 편집기와의 통합을 지원합니다. 다음 단계에 따라 Cursor에 서버를 등록하세요:

1. 서버 실행: `python run_server.py`
2. Cursor 실행
3. Cursor 명령 팔레트 열기 (Cmd/Ctrl+Shift+P)
4. `MCP: Add Server` 명령 선택
5. 서버 URL 입력: `http://localhost:8082`
6. 등록 완료 후 `MCP: Execute Method` 명령으로 도구 사용

## 태스크 흐름

PMAgent MCP 서버의 태스크 관리 흐름은 다음과 같습니다:

1. `request_planning`: 요청 등록 및 태스크 계획
2. `get_next_task`: 다음 대기 중인 태스크 가져오기
3. `mark_task_done`: 태스크 완료 처리
4. `approve_task_completion`: 태스크 완료 승인
5. 모든 태스크 완료 후 `approve_request_completion`: 요청 전체 완료

## 데이터 저장

서버는 다음 파일에 데이터를 저장합니다:

- 요청 데이터: `{DATA_DIR}/requests.json`
- 태스크 데이터: `{DATA_DIR}/tasks.json`

## 라이선스

MIT 