# PMAgent 테스트 클라이언트 사용법

PMAgent 테스트 클라이언트는 PMAgent MCP 서버와 통신하여 프로젝트 및 태스크를 관리하는 커맨드라인 도구입니다.

## 설치

PMAgent는 Python 패키지로 설치할 수 있습니다:

```bash
pip install pmagent
```

## 기본 사용법

테스트 클라이언트는 다음과 같이 실행합니다:

```bash
python -m pmagent.test_client [옵션]
```

### 기본 옵션

- `--url`: MCP 서버 URL (기본값: http://localhost:8080)
- `--action`: 수행할 작업 (`list`, `create`, `update`, `delete`, `get` 중 하나)
- `--type`: 작업 대상 (`project` 또는 `task`, 기본값: `project`)
- `--project-id`: 프로젝트 ID (작업/태스크 관련 명령에 필요)
- `--task-id`: 태스크 ID (태스크 업데이트/삭제/조회에 필요)
- `--name`: 프로젝트 또는 태스크 이름
- `--description`: 프로젝트 또는 태스크 설명
- `--status`: 태스크 상태
- `--due-date`: 태스크 마감일 (YYYY-MM-DD 형식)
- `--assignee`: 태스크 담당자

## 사용 예제

### 프로젝트 관리

#### 프로젝트 목록 조회

```bash
python -m pmagent.test_client --action list --type project
```

#### 프로젝트 생성

```bash
python -m pmagent.test_client --action create --type project --name "새 프로젝트" --description "프로젝트 설명"
```

#### 프로젝트 조회

```bash
python -m pmagent.test_client --action get --type project --project-id <프로젝트_ID>
```

#### 프로젝트 업데이트

```bash
python -m pmagent.test_client --action update --type project --project-id <프로젝트_ID> --name "새 이름" --description "새 설명"
```

#### 프로젝트 삭제

```bash
python -m pmagent.test_client --action delete --type project --project-id <프로젝트_ID>
```

### 태스크 관리

#### 태스크 목록 조회

```bash
python -m pmagent.test_client --action list --type task --project-id <프로젝트_ID>
```

#### 태스크 생성

```bash
python -m pmagent.test_client --action create --type task --project-id <프로젝트_ID> --name "새 태스크" --description "태스크 설명" --status "TODO" --due-date "2023-12-31" --assignee "홍길동"
```

#### 태스크 조회

```bash
python -m pmagent.test_client --action get --type task --project-id <프로젝트_ID> --task-id <태스크_ID>
```

#### 태스크 업데이트

```bash
python -m pmagent.test_client --action update --type task --project-id <프로젝트_ID> --task-id <태스크_ID> --name "새 이름" --description "새 설명" --status "IN_PROGRESS" --due-date "2023-12-15" --assignee "김철수"
```

#### 태스크 삭제

```bash
python -m pmagent.test_client --action delete --type task --project-id <프로젝트_ID> --task-id <태스크_ID>
```

## 상태 값

태스크의 상태(`--status`)는 다음 값 중 하나를 사용할 수 있습니다:

- `TODO`: 할 일
- `IN_PROGRESS`: 진행 중
- `REVIEW`: 검토 중
- `DONE`: 완료됨

## 오류 처리

테스트 클라이언트는 오류가 발생하면 적절한 오류 메시지를 표시합니다. 대부분의 오류는 잘못된 매개변수 또는 서버 연결 문제로 인해 발생합니다.

## 로깅

모든 출력은 INFO 레벨로 로깅됩니다. 오류는 ERROR 레벨로 로깅됩니다. 