# PMAgent
[![smithery badge](https://smithery.ai/badge/@contentscoin/pmagent)](https://smithery.ai/server/@contentscoin/pmagent)

PMAgent는 프로젝트 관리를 위한 MCP(Model Context Protocol) 서버 및 Python 클라이언트 라이브러리입니다. 이 도구를 사용하면 프로젝트와 태스크를 쉽게 생성, 관리, 업데이트할 수 있습니다.

## 특징

- 프로젝트 및 태스크 관리 (생성, 조회, 업데이트, 삭제)
- 비동기 및 동기 API 지원
- 직관적인 커맨드 라인 인터페이스
- RESTful API 서버
- 확장 가능한 MCP 아키텍처

## 설치

### Installing via Smithery

To install  PMAgent MCP Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@contentscoin/pmagent):

```bash
npx -y @smithery/cli install @contentscoin/pmagent --client claude
```

### Installing Manually
Python 패키지로 설치할 수 있습니다:

```bash
pip install pmagent
```

## 서버 실행

PMAgent 서버는 다음과 같이 실행합니다:

```bash
python -m pmagent.server
```

기본적으로 서버는 `http://localhost:8000`에서 실행됩니다.

## 기본 사용법

### Python API 사용

```python
import asyncio
from pmagent.agent import PMAgent

async def main():
    # 에이전트 초기화
    agent = PMAgent(server_url="http://localhost:8000")
    
    # 새 프로젝트 생성
    project = await agent.create_project(
        name="웹 개발 프로젝트", 
        description="React와 Django를 사용한 웹 애플리케이션 개발"
    )
    
    # 프로젝트에 태스크 추가
    task = await agent.create_task(
        project_id=project["id"],
        name="프론트엔드 설계",
        description="React 컴포넌트 구조 설계 및 상태 관리 계획",
        status="TODO",
        due_date="2023-12-31",
        assignee="홍길동"
    )
    
    # 태스크 목록 조회
    tasks = await agent.list_tasks(project["id"])
    print(f"프로젝트 태스크: {tasks}")
    
    # 세션 정리
    await agent.close_session()

if __name__ == "__main__":
    asyncio.run(main())
```

동기 API를 사용하려면:

```python
from pmagent.agent import PMAgent

# 에이전트 초기화
agent = PMAgent(server_url="http://localhost:8000")

# 프로젝트 목록 조회
projects = agent.list_projects_sync()
print(f"프로젝트 목록: {projects}")

# 세션 종료
agent.close()
```

### 커맨드 라인 인터페이스 사용

테스트 클라이언트를 사용하여 커맨드 라인에서 PMAgent를 사용할 수 있습니다:

```bash
# 프로젝트 목록 조회
python -m pmagent.test_client --action list --type project

# 새 프로젝트 생성
python -m pmagent.test_client --action create --type project --name "새 프로젝트" --description "프로젝트 설명"

# 태스크 생성
python -m pmagent.test_client --action create --type task --project-id <프로젝트_ID> --name "새 태스크" --description "태스크 설명" --status "TODO"
```

자세한 사용법은 [CLI 사용 가이드](docs/cli_usage.md)를 참조하세요.

## 문서

- [CLI 사용 가이드](docs/cli_usage.md)
- [로드맵](docs/ROADMAP.md)

## 라이선스

MIT License

## 기여

기여는 언제나 환영합니다! 이슈 제기, 풀 리퀘스트 제출, 또는 문서 개선에 참여해 주세요.
