# PMAgent API 문서

이 문서는 PMAgent MCP 서버의 API와 클라이언트 라이브러리 사용법을 설명합니다.

## 서버 API

PMAgent MCP 서버는 다음과 같은 엔드포인트를 제공합니다.

### 도구 목록 조회

도구 목록을 가져옵니다.

```
GET /tools
```

**응답 예시:**
```json
{
  "tools": [
    {
      "name": "list_projects",
      "description": "모든 프로젝트 목록을 가져옵니다.",
      "parameters": {}
    },
    {
      "name": "create_project",
      "description": "새 프로젝트를 생성합니다.",
      "parameters": {
        "name": "프로젝트 이름",
        "description": "프로젝트 설명 (선택)"
      }
    },
    ... 
  ]
}
```

### 도구 호출

특정 도구를 호출합니다.

```
POST /invoke
```

**요청 본문:**
```json
{
  "name": "도구_이름",
  "parameters": {
    "매개변수_이름": "매개변수_값",
    ...
  }
}
```

**응답:**
도구 실행 결과에 따라 다양한 응답을 반환합니다.

## 주요 도구 및 매개변수

### 프로젝트 관련 도구

#### list_projects

모든 프로젝트 목록을 가져옵니다.

**매개변수:** 없음

**응답 예시:**
```json
{
  "projects": [
    {
      "id": "project_id",
      "name": "프로젝트 이름",
      "description": "프로젝트 설명",
      "created_at": "2023-01-01T00:00:00Z"
    },
    ...
  ]
}
```

#### create_project

새 프로젝트를 생성합니다.

**매개변수:**
- `name` (필수): 프로젝트 이름
- `description` (선택): 프로젝트 설명

**응답 예시:**
```json
{
  "project": {
    "id": "project_id",
    "name": "프로젝트 이름",
    "description": "프로젝트 설명",
    "created_at": "2023-01-01T00:00:00Z"
  }
}
```

#### get_project

특정 프로젝트 정보를 가져옵니다.

**매개변수:**
- `project_id` (필수): 프로젝트 ID

**응답 예시:**
```json
{
  "project": {
    "id": "project_id",
    "name": "프로젝트 이름",
    "description": "프로젝트 설명",
    "created_at": "2023-01-01T00:00:00Z"
  }
}
```

#### update_project

프로젝트 정보를 업데이트합니다.

**매개변수:**
- `project_id` (필수): 프로젝트 ID
- `name` (선택): 새 프로젝트 이름
- `description` (선택): 새 프로젝트 설명

**응답 예시:**
```json
{
  "project": {
    "id": "project_id",
    "name": "업데이트된 이름",
    "description": "업데이트된 설명",
    "created_at": "2023-01-01T00:00:00Z"
  }
}
```

#### delete_project

프로젝트를 삭제합니다.

**매개변수:**
- `project_id` (필수): 프로젝트 ID

**응답 예시:**
```json
{
  "success": true
}
```

### 태스크 관련 도구

#### list_tasks

프로젝트의 모든 태스크 목록을 가져옵니다.

**매개변수:**
- `project_id` (필수): 프로젝트 ID

**응답 예시:**
```json
{
  "tasks": [
    {
      "id": "task_id",
      "project_id": "project_id",
      "name": "태스크 이름",
      "description": "태스크 설명",
      "status": "TODO",
      "due_date": "2023-12-31",
      "assignee": "담당자",
      "created_at": "2023-01-01T00:00:00Z"
    },
    ...
  ]
}
```

#### create_task

새 태스크를 생성합니다.

**매개변수:**
- `project_id` (필수): 프로젝트 ID
- `name` (필수): 태스크 이름
- `description` (선택): 태스크 설명
- `status` (선택): 태스크 상태 (기본값: "TODO")
- `due_date` (선택): 마감일 (ISO 형식)
- `assignee` (선택): 담당자

**응답 예시:**
```json
{
  "task": {
    "id": "task_id",
    "project_id": "project_id",
    "name": "태스크 이름",
    "description": "태스크 설명",
    "status": "TODO",
    "due_date": "2023-12-31",
    "assignee": "담당자",
    "created_at": "2023-01-01T00:00:00Z"
  }
}
```

#### get_task

특정 태스크 정보를 가져옵니다.

**매개변수:**
- `project_id` (필수): 프로젝트 ID
- `task_id` (필수): 태스크 ID

**응답 예시:**
```json
{
  "task": {
    "id": "task_id",
    "project_id": "project_id",
    "name": "태스크 이름",
    "description": "태스크 설명",
    "status": "TODO",
    "due_date": "2023-12-31",
    "assignee": "담당자",
    "created_at": "2023-01-01T00:00:00Z"
  }
}
```

#### update_task

태스크 정보를 업데이트합니다.

**매개변수:**
- `project_id` (필수): 프로젝트 ID
- `task_id` (필수): 태스크 ID
- `name` (선택): 새 태스크 이름
- `description` (선택): 새 태스크 설명
- `status` (선택): 새 태스크 상태
- `due_date` (선택): 새 마감일 (ISO 형식)
- `assignee` (선택): 새 담당자

**응답 예시:**
```json
{
  "task": {
    "id": "task_id",
    "project_id": "project_id",
    "name": "업데이트된 이름",
    "description": "업데이트된 설명",
    "status": "IN_PROGRESS",
    "due_date": "2023-12-31",
    "assignee": "새 담당자",
    "created_at": "2023-01-01T00:00:00Z"
  }
}
```

#### delete_task

태스크를 삭제합니다.

**매개변수:**
- `project_id` (필수): 프로젝트 ID
- `task_id` (필수): 태스크 ID

**응답 예시:**
```json
{
  "success": true
}
```

## 클라이언트 라이브러리 사용법

### 기본 사용법

```python
from pmagent import PMAgent

# 인스턴스 생성
agent = PMAgent("http://localhost:8000")

# 동기 메서드 사용 예시
projects = agent.list_projects_sync()
for project in projects:
    print(f"프로젝트: {project['name']}")

# 세션 종료
agent.close()
```

### 비동기 사용법

```python
import asyncio
from pmagent import PMAgent

async def main():
    # 인스턴스 생성
    agent = PMAgent("http://localhost:8000")
    
    try:
        # 세션 초기화
        await agent.init_session()
        
        # 비동기 메서드 사용 예시
        projects = await agent.list_projects()
        for project in projects:
            print(f"프로젝트: {project['name']}")
    finally:
        # 세션 종료
        await agent.close_session()

if __name__ == "__main__":
    asyncio.run(main())
```

### 에러 처리 예시

```python
from pmagent import PMAgent

agent = PMAgent("http://localhost:8000")

try:
    # 존재하지 않는 프로젝트 ID로 태스크 조회 시도
    tasks = agent.get_tasks_sync("non_existent_project_id")
except Exception as e:
    print(f"오류 발생: {e}")
finally:
    agent.close()
```

## 커맨드 라인 인터페이스(CLI) 사용법

PMAgent 패키지는 `pmagent` 명령어를 제공합니다:

```bash
# 프로젝트 목록 조회
pmagent --action list --type project

# 새 프로젝트 생성
pmagent --action create --type project --name "새 프로젝트" --description "프로젝트 설명"

# 프로젝트 태스크 목록 조회
pmagent --action list --type task --project-id PROJECT_ID

# 새 태스크 생성
pmagent --action create --type task --project-id PROJECT_ID --name "새 태스크" --description "태스크 설명" --status TODO --due-date 2023-12-31 --assignee "담당자"
```

더 많은 옵션과 예제는 `pmagent --help`를 통해 확인할 수 있습니다. 