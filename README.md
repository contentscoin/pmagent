# PMAgent MCP 서버

프로젝트 관리를 위한 MCP(Model Context Protocol) 서버입니다.

## 개요

PMAgent MCP 서버는 프로젝트와 태스크 관리를 위한 도구를 제공하는 MCP 서버입니다. 이 서버는 MCP 클라이언트가 프로젝트와 태스크를 생성, 조회, 업데이트, 삭제할 수 있도록 API를 제공합니다.

## 배포 정보

- 서버 주소: https://pmagent.vercel.app
- 문서: https://github.com/contentscoin/pmagent

## 사용 가능한 도구

PMAgent MCP 서버에서는 다음과 같은 도구들을 사용할 수 있습니다.

- `list_projects`: 모든 프로젝트 목록을 가져옵니다.
- `create_project`: 새 프로젝트를 생성합니다.
- `get_project`: 특정 프로젝트의 정보를 가져옵니다.
- `update_project`: 프로젝트 정보를 업데이트합니다.
- `delete_project`: 프로젝트를 삭제합니다.
- `list_tasks`: 특정 프로젝트의 모든 태스크 목록을 가져옵니다.
- `create_task`: 새 태스크를 생성합니다.
- `get_task`: 특정 태스크의 정보를 가져옵니다.
- `update_task`: 태스크 정보를 업데이트합니다.
- `delete_task`: 태스크를 삭제합니다.

## API 직접 사용하기

PMAgent MCP 서버는 JSON-RPC 2.0 프로토콜을 사용합니다. 다음과 같이 API를 직접 호출할 수 있습니다.

### 모든 프로젝트 목록 가져오기

```bash
curl -X POST https://pmagent.vercel.app/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "list_projects",
    "params": {},
    "id": 1
  }'
```

### 새 프로젝트 생성하기

```bash
curl -X POST https://pmagent.vercel.app/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "create_project",
    "params": {
      "name": "새 프로젝트",
      "description": "프로젝트 설명"
    },
    "id": 1
  }'
```

### 특정 프로젝트 정보 가져오기

```bash
curl -X POST https://pmagent.vercel.app/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_project",
    "params": {
      "project_id": "프로젝트_ID"
    },
    "id": 1
  }'
```

### 프로젝트 업데이트하기

```bash
curl -X POST https://pmagent.vercel.app/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "update_project",
    "params": {
      "project_id": "프로젝트_ID",
      "name": "업데이트된 이름",
      "description": "업데이트된 설명"
    },
    "id": 1
  }'
```

### 프로젝트 삭제하기

```bash
curl -X POST https://pmagent.vercel.app/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "delete_project",
    "params": {
      "project_id": "프로젝트_ID"
    },
    "id": 1
  }'
```

### 태스크 목록 가져오기

```bash
curl -X POST https://pmagent.vercel.app/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "list_tasks",
    "params": {
      "project_id": "프로젝트_ID"
    },
    "id": 1
  }'
```

### 새 태스크 생성하기

```bash
curl -X POST https://pmagent.vercel.app/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "create_task",
    "params": {
      "project_id": "프로젝트_ID",
      "name": "새 태스크",
      "description": "태스크 설명",
      "status": "todo",
      "due_date": "2023-12-31",
      "assignee": "담당자"
    },
    "id": 1
  }'
```

### 특정 태스크 정보 가져오기

```bash
curl -X POST https://pmagent.vercel.app/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_task",
    "params": {
      "project_id": "프로젝트_ID",
      "task_id": "태스크_ID"
    },
    "id": 1
  }'
```

### 태스크 업데이트하기

```bash
curl -X POST https://pmagent.vercel.app/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "update_task",
    "params": {
      "project_id": "프로젝트_ID",
      "task_id": "태스크_ID",
      "name": "업데이트된 태스크 이름",
      "description": "업데이트된 태스크 설명",
      "status": "in_progress",
      "due_date": "2023-12-31",
      "assignee": "새 담당자"
    },
    "id": 1
  }'
```

### 태스크 삭제하기

```bash
curl -X POST https://pmagent.vercel.app/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "delete_task",
    "params": {
      "project_id": "프로젝트_ID",
      "task_id": "태스크_ID"
    },
    "id": 1
  }'
```

## 로컬에서 개발하기

### 저장소 클론

```bash
git clone https://github.com/contentscoin/pmagent.git
cd pmagent
```

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 서버 실행

```bash
python -m pmagent.server
```

기본적으로 서버는 `http://localhost:8081`에서 실행됩니다.

### MCP 레지스트리에 등록하기

```bash
python register_mcp.py
```

## 라이센스

MIT 라이센스