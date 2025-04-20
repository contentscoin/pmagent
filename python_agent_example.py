#!/usr/bin/env python3
"""
Python 기반 MCP 클라이언트 예제
"""

import json
import asyncio
import aiohttp
import logging
import sys

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MCP-Agent")

class MCPClient:
    """MCP 서버에 연결하는 클라이언트"""
    
    def __init__(self, config_file='mcp-client-config.json'):
        # 설정 파일 로드
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.server_url = self.config['mcp_server']['url']
        self.timeout = self.config['mcp_server']['timeout'] / 1000  # 초 단위로 변환
        
        logger.info(f"MCP 클라이언트 초기화 - 서버: {self.server_url}")
    
    async def _send_jsonrpc_request(self, method, params=None):
        """JSON-RPC 요청 전송"""
        request_data = {
            'jsonrpc': '2.0',
            'id': int(asyncio.get_event_loop().time() * 1000),
            'method': method
        }
        
        if params is not None:
            request_data['params'] = params
        
        logger.debug(f"요청: {json.dumps(request_data)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.server_url,
                json=request_data,
                timeout=self.timeout
            ) as response:
                response_data = await response.json()
                logger.debug(f"응답: {json.dumps(response_data)}")
                return response_data
    
    async def initialize(self):
        """MCP 서버 초기화 및 정보 가져오기"""
        logger.info("서버 초기화 중...")
        response = await self._send_jsonrpc_request('initialize')
        logger.info(f"서버 정보: {response.get('result', {})}")
        return response
    
    async def get_tools(self):
        """사용 가능한 도구 목록 가져오기"""
        logger.info("도구 목록 요청 중...")
        response = await self._send_jsonrpc_request('tools/list')
        tools = response.get('result', {}).get('tools', [])
        logger.info(f"사용 가능한 도구: {len(tools)}개")
        return tools
    
    async def call_tool(self, tool_name, parameters):
        """특정 도구 호출"""
        logger.info(f"도구 '{tool_name}' 호출 중...")
        response = await self._send_jsonrpc_request('tools/call', {
            'tool': tool_name,
            'parameters': parameters
        })
        
        if 'error' in response:
            logger.error(f"도구 호출 오류: {response['error']}")
        else:
            logger.info(f"도구 '{tool_name}' 호출 성공")
        
        return response

class PMAgent:
    """PM(Project Manager) 에이전트"""
    
    def __init__(self, server_url="http://localhost:3000"):
        self.server_url = server_url
        self.session = None
        self.tools = {}
        
    async def init_session(self):
        """MCP 서버에 연결하고 세션을 초기화합니다."""
        self.session = aiohttp.ClientSession()
        tools = await self.get_tools()
        print(f"사용 가능한 도구: {len(tools)}개")
        return tools
        
    async def close_session(self):
        """세션을 닫습니다."""
        if self.session:
            await self.session.close()
            
    async def get_tools(self):
        """사용 가능한 도구 목록을 가져옵니다."""
        async with self.session.get(f"{self.server_url}/api/tools") as response:
            if response.status == 200:
                data = await response.json()
                self.tools = {tool['name']: tool for tool in data['tools']}
                return data['tools']
            else:
                print(f"도구 목록을 가져오는 데 실패했습니다: {response.status}")
                return []
                
    async def call_tool(self, tool_name, params=None):
        """도구를 실행합니다."""
        if tool_name not in self.tools:
            print(f"오류: '{tool_name}' 도구를 찾을 수 없습니다.")
            return None
            
        payload = {
            "name": tool_name,
            "parameters": params or {}
        }
        
        async with self.session.post(
            f"{self.server_url}/api/invoke", 
            json=payload
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                print(f"도구 실행 오류 ({response.status}): {error_text}")
                return None

    async def create_project(self, project_name):
        """새 프로젝트를 생성합니다."""
        result = await self.call_tool("pm_create_project", {
            "project_name": project_name
        })
        return result
        
    async def list_projects(self):
        """모든 프로젝트 목록을 가져옵니다."""
        result = await self.call_tool("pm_list_projects", {})
        return result
        
    async def create_task(self, project_id, task_name, description=""):
        """프로젝트에 새 작업을 추가합니다."""
        result = await self.call_tool("pm_create_task", {
            "project_id": project_id,
            "task_name": task_name,
            "description": description
        })
        return result

async def main():
    agent = PMAgent()
    try:
        # 세션 초기화
        tools = await agent.init_session()
        print(f"도구 목록: {json.dumps([t['name'] for t in tools], indent=2)}")
        
        # 프로젝트 목록 가져오기
        projects = await agent.list_projects()
        if projects:
            print(f"프로젝트 목록: {json.dumps(projects, indent=2)}")
            
            # 예시: 새 프로젝트 생성
            if len(sys.argv) > 1:
                new_project = await agent.create_project(sys.argv[1])
                if new_project:
                    print(f"새 프로젝트 생성됨: {new_project['project_id']}")
                    
                    # 예시: 새 작업 생성
                    task = await agent.create_task(
                        new_project['project_id'],
                        "첫 번째 작업",
                        "이것은 예제 작업입니다."
                    )
                    if task:
                        print(f"새 작업 생성됨: {task['task_id']}")
        
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        await agent.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 