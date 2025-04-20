#!/usr/bin/env python
# -*- coding: utf-8 -*-

import aiohttp
import requests
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class PMAgent:
    """프로젝트 관리 MCP 에이전트 클래스"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        PMAgent 초기화
        
        Args:
            server_url: MCP 서버 URL
        """
        self.server_url = server_url
        self.session = None
        self.sync_session = None
        self.tools = {}
    
    async def init_session(self) -> None:
        """HTTP 세션을 초기화합니다."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            logger.info(f"MCP 서버({self.server_url})에 연결됨")
    
    def init_sync_session(self) -> None:
        """동기 HTTP 세션을 초기화합니다."""
        if self.sync_session is None:
            self.sync_session = requests.Session()
            logger.info(f"MCP 서버({self.server_url})에 동기 연결됨")
    
    async def close_session(self) -> None:
        """HTTP 세션을 종료합니다."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("MCP 서버 비동기 연결 종료됨")
    
    def close_sync_session(self) -> None:
        """동기 HTTP 세션을 종료합니다."""
        if self.sync_session:
            self.sync_session.close()
            self.sync_session = None
            logger.info("MCP 서버 동기 연결 종료됨")
    
    def close(self) -> None:
        """모든 세션을 종료합니다."""
        if self.session and not self.session.closed:
            asyncio.run(self.close_session())
        self.close_sync_session()
    
    async def get_tools(self) -> List[str]:
        """
        서버에서 사용 가능한 도구 목록을 가져옵니다.
        
        Returns:
            사용 가능한 도구 이름 목록
        """
        await self.init_session()
        
        async with self.session.get(f"{self.server_url}/tools") as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"도구 목록 조회 실패: {text}")
            
            data = await response.json()
            self.tools = {tool["name"]: tool for tool in data["tools"]}
            return list(self.tools.keys())
    
    def get_tools_sync(self) -> List[str]:
        """
        서버에서 사용 가능한 도구 목록을 동기적으로 가져옵니다.
        
        Returns:
            사용 가능한 도구 이름 목록
        """
        self.init_sync_session()
        
        response = self.sync_session.get(f"{self.server_url}/tools")
        if response.status_code != 200:
            raise Exception(f"도구 목록 조회 실패: {response.text}")
        
        data = response.json()
        self.tools = {tool["name"]: tool for tool in data["tools"]}
        return list(self.tools.keys())
    
    async def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        지정된 도구를 호출합니다.
        
        Args:
            tool_name: 호출할 도구 이름
            params: 도구 호출 매개변수
            
        Returns:
            도구 호출 결과
        """
        if not self.tools:
            await self.get_tools()
            
        if tool_name not in self.tools:
            raise ValueError(f"존재하지 않는 도구: {tool_name}")
        
        await self.init_session()
        
        payload = {
            "name": tool_name,
            "parameters": params
        }
        
        logger.debug(f"도구 호출: {tool_name}, 매개변수: {params}")
        
        async with self.session.post(
            f"{self.server_url}/invoke", 
            json=payload
        ) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"도구 호출 실패({tool_name}): {text}")
            
            result = await response.json()
            return result
    
    def _call_tool_sync(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        지정된 도구를 동기적으로 호출합니다.
        
        Args:
            tool_name: 호출할 도구 이름
            params: 도구 호출 매개변수
            
        Returns:
            도구 호출 결과
        """
        if not self.tools:
            self.get_tools_sync()
            
        if tool_name not in self.tools:
            raise ValueError(f"존재하지 않는 도구: {tool_name}")
        
        self.init_sync_session()
        
        payload = {
            "name": tool_name,
            "parameters": params
        }
        
        logger.debug(f"도구 호출: {tool_name}, 매개변수: {params}")
        
        response = self.sync_session.post(
            f"{self.server_url}/invoke", 
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"도구 호출 실패({tool_name}): {response.text}")
        
        return response.json()
    
    # 비동기 메서드
    async def list_projects(self) -> List[Dict[str, Any]]:
        """
        모든 프로젝트 목록을 가져옵니다.
        
        Returns:
            프로젝트 목록
        """
        result = await self._call_tool("list_projects", {})
        return result.get("projects", [])
    
    async def create_project(self, name: str, description: str = None) -> Dict[str, Any]:
        """
        새 프로젝트를 생성합니다.
        
        Args:
            name: 프로젝트 이름
            description: 프로젝트 설명
            
        Returns:
            생성된 프로젝트 정보
        """
        params = {"name": name}
        if description:
            params["description"] = description
            
        result = await self._call_tool("create_project", params)
        return result.get("project", {})
    
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        프로젝트 정보를 가져옵니다.
        
        Args:
            project_id: 프로젝트 ID
            
        Returns:
            프로젝트 정보
        """
        result = await self._call_tool("get_project", {
            "project_id": project_id
        })
        return result.get("project", {})
    
    async def update_project(self, project_id: str, name: str = None, description: str = None) -> Dict[str, Any]:
        """
        프로젝트 정보를 업데이트합니다.
        
        Args:
            project_id: 프로젝트 ID
            name: 새 프로젝트 이름 (선택)
            description: 새 프로젝트 설명 (선택)
            
        Returns:
            업데이트된 프로젝트 정보
        """
        params = {"project_id": project_id}
        
        if name is not None:
            params["name"] = name
        if description is not None:
            params["description"] = description
            
        result = await self._call_tool("update_project", params)
        return result.get("project", {})
    
    async def delete_project(self, project_id: str) -> bool:
        """
        프로젝트를 삭제합니다.
        
        Args:
            project_id: 프로젝트 ID
            
        Returns:
            성공 여부
        """
        result = await self._call_tool("delete_project", {
            "project_id": project_id
        })
        return result.get("success", False)
    
    async def list_tasks(self, project_id: str) -> List[Dict[str, Any]]:
        """
        프로젝트의 모든 태스크 목록을 가져옵니다.
        
        Args:
            project_id: 프로젝트 ID
            
        Returns:
            태스크 목록
        """
        result = await self._call_tool("list_tasks", {
            "project_id": project_id
        })
        return result.get("tasks", [])
    
    async def create_task(self, project_id: str, name: str, description: str = None, 
                       status: str = "TODO", due_date: str = None, assignee: str = None) -> Dict[str, Any]:
        """
        새 태스크를 생성합니다.
        
        Args:
            project_id: 프로젝트 ID
            name: 태스크 이름
            description: 태스크 설명 (선택)
            status: 태스크 상태 (선택, 기본값: "TODO")
            due_date: 마감일 (선택, ISO 형식)
            assignee: 담당자 (선택)
            
        Returns:
            생성된 태스크 정보
        """
        params = {
            "project_id": project_id,
            "name": name,
            "status": status
        }
        
        if description is not None:
            params["description"] = description
        if due_date is not None:
            params["due_date"] = due_date
        if assignee is not None:
            params["assignee"] = assignee
            
        result = await self._call_tool("create_task", params)
        return result.get("task", {})
    
    async def get_task(self, project_id: str, task_id: str) -> Dict[str, Any]:
        """
        특정 태스크 정보를 가져옵니다.
        
        Args:
            project_id: 프로젝트 ID
            task_id: 태스크 ID
            
        Returns:
            태스크 정보
        """
        result = await self._call_tool("get_task", {
            "project_id": project_id,
            "task_id": task_id
        })
        return result.get("task", {})
    
    async def update_task(self, project_id: str, task_id: str, name: Optional[str] = None, 
                         description: Optional[str] = None, status: Optional[str] = None,
                         due_date: Optional[str] = None, assignee: Optional[str] = None) -> Dict[str, Any]:
        """
        태스크 정보를 업데이트합니다.
        
        Args:
            project_id: 프로젝트 ID
            task_id: 태스크 ID
            name: 태스크 이름 (선택)
            description: 태스크 설명 (선택)
            status: 태스크 상태 (선택)
            due_date: 태스크 마감일 (선택)
            assignee: 태스크 담당자 (선택)
            
        Returns:
            업데이트된 태스크 정보
        """
        params = {
            "project_id": project_id,
            "task_id": task_id
        }
        
        if name is not None:
            params["name"] = name
        if description is not None:
            params["description"] = description
        if status is not None:
            params["status"] = status
        if due_date is not None:
            params["due_date"] = due_date
        if assignee is not None:
            params["assignee"] = assignee
            
        result = await self._call_tool("update_task", params)
        return result.get("task", {})
    
    async def delete_task(self, project_id: str, task_id: str) -> bool:
        """
        태스크를 삭제합니다.
        
        Args:
            project_id: 프로젝트 ID
            task_id: 태스크 ID
            
        Returns:
            성공 여부
        """
        result = await self._call_tool("delete_task", {
            "project_id": project_id,
            "task_id": task_id
        })
        return result.get("success", False)
    
    async def get_tasks(self, project_id: str) -> List[Dict[str, Any]]:
        """
        프로젝트의 모든 태스크 목록을 가져옵니다.
        
        주의: 이 메서드는 deprecated 되었으며, list_tasks()를 사용하세요.
        
        Args:
            project_id: 프로젝트 ID
            
        Returns:
            태스크 목록
        """
        import warnings
        warnings.warn(
            "get_tasks()는 향후 버전에서 제거될 예정입니다. 대신 list_tasks()를 사용하세요.",
            DeprecationWarning, 
            stacklevel=2
        )
        return await self.list_tasks(project_id)
    
    # 동기 메서드
    def list_projects_sync(self) -> List[Dict[str, Any]]:
        """
        모든 프로젝트 목록을 동기적으로 가져옵니다.
        
        Returns:
            프로젝트 목록
        """
        result = self._call_tool_sync("list_projects", {})
        return result.get("projects", [])
    
    def create_project_sync(self, name: str, description: str = None) -> Dict[str, Any]:
        """
        새 프로젝트를 동기적으로 생성합니다.
        
        Args:
            name: 프로젝트 이름
            description: 프로젝트 설명 (선택)
            
        Returns:
            생성된 프로젝트 정보
        """
        params = {"name": name}
        if description:
            params["description"] = description
            
        result = self._call_tool_sync("create_project", params)
        return result.get("project", {})
    
    def get_project_sync(self, project_id: str) -> Dict[str, Any]:
        """
        프로젝트 정보를 동기적으로 가져옵니다.
        
        Args:
            project_id: 프로젝트 ID
            
        Returns:
            프로젝트 정보
        """
        result = self._call_tool_sync("get_project", {
            "project_id": project_id
        })
        return result.get("project", {})
    
    def update_project_sync(self, project_id: str, name: str = None, description: str = None) -> Dict[str, Any]:
        """
        프로젝트 정보를 동기적으로 업데이트합니다.
        
        Args:
            project_id: 프로젝트 ID
            name: 새 프로젝트 이름 (선택)
            description: 새 프로젝트 설명 (선택)
            
        Returns:
            업데이트된 프로젝트 정보
        """
        params = {"project_id": project_id}
        
        if name is not None:
            params["name"] = name
        if description is not None:
            params["description"] = description
            
        result = self._call_tool_sync("update_project", params)
        return result.get("project", {})
    
    def delete_project_sync(self, project_id: str) -> bool:
        """
        프로젝트를 동기적으로 삭제합니다.
        
        Args:
            project_id: 프로젝트 ID
            
        Returns:
            성공 여부
        """
        result = self._call_tool_sync("delete_project", {
            "project_id": project_id
        })
        return result.get("success", False)
    
    def list_tasks_sync(self, project_id: str) -> List[Dict[str, Any]]:
        """
        프로젝트의 모든 태스크 목록을 가져옵니다 (동기 버전).
        
        Args:
            project_id: 프로젝트 ID
            
        Returns:
            태스크 목록
        """
        result = self._call_tool_sync("list_tasks", {
            "project_id": project_id
        })
        return result.get("tasks", [])
    
    def get_tasks_sync(self, project_id: str) -> List[Dict[str, Any]]:
        """
        프로젝트의 모든 태스크 목록을 동기적으로 가져옵니다.
        
        주의: 이 메서드는 deprecated 되었으며, list_tasks_sync()를 사용하세요.
        
        Args:
            project_id: 프로젝트 ID
            
        Returns:
            태스크 목록
        """
        import warnings
        warnings.warn(
            "get_tasks_sync()는 향후 버전에서 제거될 예정입니다. 대신 list_tasks_sync()를 사용하세요.",
            DeprecationWarning, 
            stacklevel=2
        )
        return self.list_tasks_sync(project_id)
    
    def create_task_sync(self, project_id: str, name: str, description: str = None, 
                      status: str = "TODO", due_date: str = None, assignee: str = None) -> Dict[str, Any]:
        """
        새 태스크를 동기적으로 생성합니다.
        
        Args:
            project_id: 프로젝트 ID
            name: 태스크 이름
            description: 태스크 설명 (선택)
            status: 태스크 상태 (선택, 기본값: "TODO")
            due_date: 마감일 (선택, ISO 형식)
            assignee: 담당자 (선택)
            
        Returns:
            생성된 태스크 정보
        """
        params = {
            "project_id": project_id,
            "name": name,
            "status": status
        }
        
        if description is not None:
            params["description"] = description
        if due_date is not None:
            params["due_date"] = due_date
        if assignee is not None:
            params["assignee"] = assignee
            
        result = self._call_tool_sync("create_task", params)
        return result.get("task", {})
    
    def get_task_sync(self, project_id: str, task_id: str) -> Dict[str, Any]:
        """
        태스크 정보를 동기적으로 가져옵니다.
        
        Args:
            project_id: 프로젝트 ID
            task_id: 태스크 ID
            
        Returns:
            태스크 정보
        """
        result = self._call_tool_sync("get_task", {
            "project_id": project_id,
            "task_id": task_id
        })
        return result.get("task", {})
    
    def update_task_sync(self, project_id: str, task_id: str, name: str = None, 
                      description: str = None, status: str = None, 
                      due_date: str = None, assignee: str = None) -> Dict[str, Any]:
        """
        태스크 정보를 동기적으로 업데이트합니다.
        
        Args:
            project_id: 프로젝트 ID
            task_id: 태스크 ID
            name: 새 태스크 이름 (선택)
            description: 새 태스크 설명 (선택)
            status: 새 태스크 상태 (선택)
            due_date: 새 마감일 (선택, ISO 형식)
            assignee: 새 담당자 (선택)
            
        Returns:
            업데이트된 태스크 정보
        """
        params = {
            "project_id": project_id,
            "task_id": task_id
        }
        
        if name is not None:
            params["name"] = name
        if description is not None:
            params["description"] = description
        if status is not None:
            params["status"] = status
        if due_date is not None:
            params["due_date"] = due_date
        if assignee is not None:
            params["assignee"] = assignee
            
        result = self._call_tool_sync("update_task", params)
        return result.get("task", {})
    
    def delete_task_sync(self, project_id: str, task_id: str) -> bool:
        """
        태스크를 동기적으로 삭제합니다.
        
        Args:
            project_id: 프로젝트 ID
            task_id: 태스크 ID
            
        Returns:
            성공 여부
        """
        result = self._call_tool_sync("delete_task", {
            "project_id": project_id,
            "task_id": task_id
        })
        return result.get("success", False) 