# PMAgent MCP 서버

프로젝트 관리를 위한 MCP(Model Context Protocol) 서버입니다.

## 개요

PMAgent MCP 서버는 프로젝트와 태스크 관리를 위한 도구를 제공하는 MCP 서버입니다. 이 서버는 MCP 클라이언트가 프로젝트와 태스크를 생성, 조회, 업데이트, 삭제할 수 있도록 API를 제공합니다.

## 배포 정보

- 프로덕션 URL: https://pmagent.vercel.app
- 서버 정보 확인: https://pmagent.vercel.app/
- 도구 목록 확인: https://pmagent.vercel.app/tools

## MCP 도구 목록

PMAgent MCP 서버는 다음과 같은 도구를 제공합니다:

- `list_projects`: 프로젝트 목록을 가져옵니다.
- `create_project`: 새 프로젝트를 생성합니다.
- `get_project`: 프로젝트 정보를 가져옵니다.
- `update_project`: 프로젝트 정보를 업데이트합니다.
- `delete_project`: 프로젝트를 삭제합니다.
- `list_tasks`: 프로젝트의 모든 태스크 목록을 가져옵니다.
- `create_task`: 새 태스크를 생성합니다.
- `get_task`: 태스크 정보를 가져옵니다.
- `update_task`: 태스크 정보를 업데이트합니다.
- `delete_task`: 태스크를 삭제합니다.

## MCP 서버 직접 사용 방법

### 1. API 직접 호출

```bash
# 서버 정보 확인
curl https://pmagent.vercel.app/

# 도구 목록 확인
curl https://pmagent.vercel.app/tools

# 도구 호출 (프로젝트 목록 조회)
curl -X POST https://pmagent.vercel.app/invoke \
  -H "Content-Type: application/json" \
  -d '{"name": "list_projects", "parameters": {}}'

# 프로젝트 생성
curl -X POST https://pmagent.vercel.app/invoke \
  -H "Content-Type: application/json" \
  -d '{"name": "create_project", "parameters": {"name": "API 테스트 프로젝트", "description": "API로 생성된 테스트 프로젝트"}}'
```

### 2. MCP 툴박스 수동 추가

MCP 클라이언트에서 다음 정보를 사용하여 서버를 수동으로 추가할 수 있습니다:

```
서버 이름: pmagent
표시 이름: PM Agent MCP Server
설명: 프로젝트 관리를 위한 MCP(Model Context Protocol) 서버
버전: 0.1.0
기본 URL: https://pmagent.vercel.app
```

또는 `smithery-simple.json` 파일을 직접 다운로드하여 클라이언트에 로드할 수 있습니다:

```bash
# 간소화된 smithery 파일 다운로드
curl -O https://pmagent.vercel.app/smithery-simple.json

# MCP 클라이언트에서 수동으로 로드
# 'Add Server > Import from file' 메뉴에서 smithery-simple.json 파일 선택
```

### 3. JSON-RPC 호출 (고급)

```bash
# JSON-RPC 초기화
curl -X POST https://pmagent.vercel.app/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize"
  }'

# JSON-RPC로 도구 목록 조회
curl -X POST https://pmagent.vercel.app/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }'

# JSON-RPC로 도구 호출 (프로젝트 생성)
curl -X POST https://pmagent.vercel.app/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/invoke",
    "params": {
      "name": "create_project",
      "parameters": {
        "name": "JSON-RPC 테스트 프로젝트",
        "description": "JSON-RPC로 생성된 테스트 프로젝트"
      }
    }
  }'
```

## 스미더리 레지스트리 등록 방법

1. 스미더리 CLI 설치:
   ```
   npm install -g smithery-cli
   ```

2. smithery.json 파일로 등록:
   ```
   smithery register --file smithery.json
   ```

## 로컬 개발 환경 설정

1. 저장소 클론:
   ```
   git clone https://github.com/contentscoin/pmagent.git
   cd pmagent-mcp-server
   ```

2. 의존성 설치:
   ```
   pip install -r requirements.txt
   ```

3. 서버 실행:
   ```
   python -m pmagent.server
   ```

4. 테스트 스크립트 실행:
   ```
   python register_mcp.py
   ```

## 클라이언트 사용 예시

Python:

```python
from pmagent.agent import PMAgent

async def main():
    agent = PMAgent(server_url="https://pmagent.vercel.app")
    
    # 도구 목록 가져오기
    tools = await agent.get_tools()
    print(f"사용 가능한 도구: {tools}")
    
    # 프로젝트 생성
    project = await agent.create_project(
        name="테스트 프로젝트",
        description="테스트용 프로젝트입니다."
    )
    print(f"생성된 프로젝트: {project}")
    
    # 세션 종료
    await agent.close_session()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## 라이선스

MIT