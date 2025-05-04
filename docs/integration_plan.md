# PMAgent MCP 서버 - Cursor 통합 계획

## 개요

이 문서는 PMAgent MCP 서버를 Cursor 편집기에 통합하는 방법에 대한 계획을 설명합니다. 클라이언트 UI 개발 없이 Cursor에서 MCP 프로토콜을 통해 PMAgent 서비스를 활용하는 방법을 다룹니다.

## 1. 아키텍처

### 1.1. 구성 요소

1. **PMAgent MCP 서버**
   - JSON-RPC 2.0 기반 API 제공
   - 파일 기반 데이터 지속성 구현
   - 에이전트 관리 (PM, 디자이너, 프론트엔드, 백엔드, AI 엔지니어)

2. **Cursor MCP 클라이언트**
   - Cursor의 내장 MCP 클라이언트 활용
   - PMAgent MCP 서버와 통신
   - 사용자 코드 편집 컨텍스트 제공

### 1.2. 통신 흐름

```
[사용자] <-> [Cursor 편집기] <-> [MCP 클라이언트] <-> [PMAgent MCP 서버] <-> [각종 에이전트]
```

## 2. 통합 방법

### 2.1. 서버 배포 옵션

1. **로컬 실행**
   - 사용자 머신에서 PMAgent MCP 서버 실행
   - 데이터는 로컬 파일 시스템에 저장
   - 설치 및 실행 스크립트 제공

2. **클라우드 배포**
   - 서버를 Vercel 또는 다른 클라우드 서비스에 배포
   - 공유 환경에서 사용 가능
   - 환경 변수를 통한 구성

### 2.2. Cursor에서 서버 등록

1. Cursor 명령 팔레트에서 `MCP: Add Server` 선택
2. PMAgent MCP 서버 URL 입력 (예: `http://localhost:8082` 또는 클라우드 URL)
3. 서버가 등록되면 사용 가능한 메서드 목록 표시

## 3. 사용 시나리오

### 3.1. 프로젝트 관리

1. **새 프로젝트 생성**
   - 사용자가 MCP 명령 실행: `pmagent.create_session`
   - 세션 ID를 받아 이후 작업에 사용

2. **작업 계획**
   - 사용자가 요구사항 작성
   - MCP 명령 실행: `pmagent.request_planning`
   - 태스크 목록 생성 및 표시

3. **태스크 추적**
   - MCP 명령으로 다음 태스크 가져오기: `pmagent.get_next_task`
   - 작업 완료 후 태스크 완료 처리: `pmagent.mark_task_done`
   - 각 태스크 승인: `pmagent.approve_task_completion`

### 3.2. 에이전트 활용

1. **디자이너 에이전트**
   - 사용자가 디자인 요구사항 작성
   - MCP 명령으로 에이전트 생성: `pmagent.create_agent` (타입: "designer")
   - 디자인 태스크 할당: `pmagent.assign_task_to_agent`
   - 디자인 결과 확인: `pmagent.get_agent_result`

2. **프론트엔드 에이전트**
   - 디자인 결과를 바탕으로 UI 구현
   - MCP 명령으로 에이전트 생성: `pmagent.create_agent` (타입: "frontend")
   - 구현 태스크 할당 및 결과 확인

3. **백엔드 에이전트**
   - API 설계 및 구현
   - 데이터베이스 모델 생성
   - 서버 로직 구현

4. **AI 엔지니어 에이전트**
   - 머신러닝 모델 통합
   - AI 기능 구현

### 3.3. 데이터 관리

1. **데이터 내보내기**
   - 프로젝트 종료 시 데이터 백업
   - MCP 명령 실행: `pmagent.export_data`
   - 데이터는 자동으로 로컬 파일에 저장됨

2. **데이터 가져오기**
   - 새 세션 시작 시 기존 데이터 불러오기
   - MCP 명령 실행: `pmagent.import_data` (파라미터: "fromFile": true)

## 4. 구현 로드맵

### 4.1. Phase 1: 기본 통합

1. PMAgent MCP 서버 완성
   - ✅ JSON-RPC 2.0 API 구현
   - ✅ 기본 프로젝트 관리 기능
   - ✅ 데이터 지속성 구현

2. Cursor 통합 테스트
   - MCP 서버 등록 및 발견 테스트
   - 기본 API 호출 테스트

### 4.2. Phase 2: 에이전트 기능 개선

1. 에이전트 시스템 고도화
   - ✅ 디자이너 에이전트 구현
   - ⬜ 프론트엔드 에이전트 개선
   - ⬜ 백엔드 에이전트 개선
   - ⬜ AI 엔지니어 에이전트 개선

2. 코드 생성 및 적용 기능
   - ⬜ 생성된 코드를 Cursor 편집기에 적용
   - ⬜ 디자인 시스템과 코드 연동

### 4.3. Phase 3: 고급 기능

1. 프로젝트 컨텍스트 인식
   - ⬜ Cursor 워크스페이스 분석
   - ⬜ 프로젝트 구조 이해 및 활용

2. 협업 기능
   - ⬜ 다중 사용자 지원
   - ⬜ 클라우드 저장소 연동

## 5. 사용자 가이드

### 5.1. 시작하기

PMAgent MCP 서버를 Cursor에 연결하려면:

1. PMAgent MCP 서버 설치 및 실행
   ```bash
   git clone https://github.com/your-username/pmagent-mcp-server.git
   cd pmagent-mcp-server
   pip install -r requirements.txt
   python server.py
   ```

2. Cursor에서 MCP 서버 등록
   - 명령 팔레트 열기 (Cmd/Ctrl+Shift+P)
   - `MCP: Add Server` 입력
   - 서버 URL 입력: `http://localhost:8082`

3. 세션 생성
   - 명령 팔레트에서 `MCP: Execute Method` 선택
   - `pmagent.create_session` 메서드 선택
   - 세션 ID를 저장하여 이후 작업에 사용

### 5.2. 주요 명령어

| 명령어 | 설명 | 파라미터 |
|--------|------|----------|
| `pmagent.create_session` | 새 세션 생성 | - |
| `pmagent.request_planning` | 요구사항 기반 태스크 계획 | `originalRequest`, `tasks` |
| `pmagent.get_next_task` | 다음 태스크 가져오기 | `requestId` |
| `pmagent.mark_task_done` | 태스크 완료 처리 | `requestId`, `taskId` |
| `pmagent.create_agent` | 새 에이전트 생성 | `type`, `name`, `config` |
| `pmagent.assign_task_to_agent` | 에이전트에 태스크 할당 | `agentId`, `task` |
| `pmagent.export_data` | 데이터 내보내기 | `sessionId` |
| `pmagent.import_data` | 데이터 가져오기 | `sessionId`, `fromFile` | 