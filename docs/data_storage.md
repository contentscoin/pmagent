# PMAgent MCP 서버 데이터 저장소

이 문서는 PMAgent MCP 서버의 데이터 저장 기능에 대해 설명합니다.

## 개요

PMAgent MCP 서버는 기본적으로 인메모리 저장소를 사용하지만, 지속성을 위해 로컬 파일 시스템에 JSON 형식으로 데이터를 저장하고 불러오는 기능을 제공합니다.

## 데이터 저장 구조

모든 데이터는 다음과 같은 구조로 저장됩니다:

```
api/data/
└── sessions/
    ├── {session_id1}.json
    ├── {session_id2}.json
    └── ...
```

각 JSON 파일은 다음 구조를 가집니다:

```json
{
  "projects": { /* 프로젝트 데이터 */ },
  "tasks": { /* 태스크 데이터 */ },
  "requests": { /* 요청 데이터 */ },
  "agents": { /* 에이전트 데이터 */ },
  "export_time": "2023-04-21T10:00:00",
  "session_id": "session-uuid"
}
```

## 주요 기능

### 1. 데이터 내보내기 (export_data)

클라이언트는 `export_data` 메서드를 통해 현재 서버에 저장된 데이터를 가져올 수 있습니다.

**요청:**
```json
{
  "jsonrpc": "2.0",
  "method": "export_data",
  "params": [
    {
      "sessionId": "session-uuid" // 선택적
    }
  ],
  "id": 1
}
```

**응답:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "data": {
      "projects": {},
      "tasks": {},
      "requests": {},
      "agents": {},
      "export_time": "2023-04-21T10:00:00",
      "session_id": "session-uuid",
      "saved_file_path": "api/data/sessions/session-uuid.json"
    },
    "message": "Data exported successfully"
  },
  "id": 1
}
```

### 2. 데이터 가져오기 (import_data)

클라이언트는 `import_data` 메서드를 통해 이전에 내보낸 데이터를 서버에 적용할 수 있습니다.

**요청 (데이터 직접 전송):**
```json
{
  "jsonrpc": "2.0",
  "method": "import_data",
  "params": [
    {
      "data": {
        "projects": {},
        "tasks": {},
        "requests": {},
        "agents": {}
      },
      "sessionId": "session-uuid" // 선택적
    }
  ],
  "id": 1
}
```

**요청 (파일에서 불러오기):**
```json
{
  "jsonrpc": "2.0",
  "method": "import_data",
  "params": [
    {
      "sessionId": "session-uuid",
      "fromFile": true
    }
  ],
  "id": 1
}
```

**응답:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "message": "Data imported successfully",
    "projects_count": 10,
    "tasks_count": 25,
    "requests_count": 5,
    "agents_count": 3
  },
  "id": 1
}
```

## 데이터 지속성 유틸리티

`api/data_persistence.py` 모듈은 파일 기반 데이터 저장을 위한 다음 함수들을 제공합니다:

1. `save_data_to_file(session_id, data)`: 데이터를 파일로 저장
2. `load_data_from_file(session_id)`: 파일에서 데이터 불러오기
3. `list_all_sessions()`: 저장된 모든 세션 목록 조회
4. `delete_session_data(session_id)`: 세션 데이터 삭제

## 클라이언트 사용 지침

### 데이터 내보내기 및 백업

1. 주기적으로 `export_data`를 호출하여 중요한 데이터를 백업합니다.
2. 백업 데이터는 클라이언트 측에서 안전하게 보관하세요.

### 데이터 불러오기

1. 서버 재시작 후 이전 상태를 복원하려면 `import_data`를 호출합니다.
2. 새 세션을 생성한 후 바로 이전 데이터를 불러와 작업을 계속할 수 있습니다.

### 권장 사항

- 중요한 작업을 수행한 후에는 항상 데이터를 내보내 백업하세요.
- 새 세션을 시작할 때 이전 세션의 데이터를 불러와 연속성을 유지하세요.
- 장기 프로젝트의 경우 여러 백업본을 유지하는 것이 좋습니다. 