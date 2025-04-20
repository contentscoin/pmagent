# PMAgent 설치 및 시작 가이드

이 문서에서는 PMAgent MCP 서버와 클라이언트를 설치하고 실행하는 방법을 설명합니다.

## 요구사항

- Python 3.7 이상
- pip (Python 패키지 관리자)

## 설치 방법

### 패키지로 설치

PMAgent는 pip를 통해 설치할 수 있습니다:

```bash
pip install pmagent
```

### 소스코드에서 설치

또는 소스코드에서 직접 설치할 수 있습니다:

```bash
git clone https://github.com/yourusername/pmagent-mcp-server.git
cd pmagent-mcp-server
pip install -e .
```

### 개발 환경 설정

개발 목적으로 설치할 경우, 추가 패키지가 필요합니다:

```bash
pip install -r requirements-dev.txt
```

## MCP 서버 실행

### 기본 실행

기본 설정으로 서버를 실행하려면:

```bash
python server.py
```

서버는 기본적으로 `http://localhost:8000`에서 실행됩니다.

### 환경 변수 설정

서버 실행 시 다음과 같은 환경 변수를 설정할 수 있습니다:

- `PORT`: 서버 포트 (기본값: 8000)
- `HOST`: 서버 호스트 (기본값: 0.0.0.0)
- `LOG_LEVEL`: 로깅 레벨 (기본값: INFO)

예시:
```bash
PORT=9000 LOG_LEVEL=DEBUG python server.py
```

## 클라이언트 사용

### 명령행 인터페이스 (CLI)

PMAgent는 명령행 도구를 제공합니다:

```bash
# 도움말 보기
pmagent --help

# 프로젝트 목록 조회
pmagent --action list --type project

# 서버 URL 지정
pmagent --url http://custom-server:8000 --action list --type project
```

### 파이썬 스크립트에서 사용

PMAgent 라이브러리를 파이썬 코드에서 사용할 수 있습니다:

```python
from pmagent import PMAgent

# 동기 API 사용
agent = PMAgent("http://localhost:8000")
projects = agent.list_projects_sync()
print(projects)
agent.close()

# 비동기 API 사용
import asyncio

async def main():
    agent = PMAgent("http://localhost:8000")
    await agent.init_session()
    projects = await agent.list_projects()
    print(projects)
    await agent.close_session()

asyncio.run(main())
```

## 예제 실행

PMAgent에는 몇 가지 사용 예제가 포함되어 있습니다:

```bash
# 동기 예제 실행
python examples/example.py

# 비동기 예제 실행
python examples/async_example.py
```

## 테스트 실행

테스트를 실행하려면:

```bash
# 모든 테스트 실행
python run_tests.py

# 특정 테스트 파일 실행
python run_tests.py tests/test_agent.py
```

## 문제 해결

### 일반적인 오류

1. **연결 오류**
   
   ```
   ConnectionError: 서버에 연결할 수 없습니다.
   ```
   
   해결 방법:
   - 서버가 실행 중인지 확인
   - 올바른 URL을 사용 중인지 확인
   - 방화벽 설정 확인

2. **인증 오류**
   
   ```
   AuthenticationError: 인증에 실패했습니다.
   ```
   
   해결 방법:
   - 인증 정보가 올바른지 확인
   - 토큰이 만료되지 않았는지 확인

3. **파라미터 오류**
   
   ```
   ValidationError: 필수 파라미터가 누락되었습니다.
   ```
   
   해결 방법:
   - API 문서를 참조하여 필요한 모든 파라미터를 제공했는지 확인

## 추가 리소스

- [API 문서](./API.md): 자세한 API 설명
- [로드맵](./ROADMAP.md): 향후 개발 계획
- [GitHub 저장소](https://github.com/yourusername/pmagent-mcp-server): 최신 소스코드 및 이슈 추적 