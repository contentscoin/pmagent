#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent MCP 서버 등록 및 테스트 스크립트

이 스크립트는 다음 작업을 수행합니다:
1. 서버가 실행 중인지 확인
2. 서버에서 사용 가능한 도구 목록 가져오기
3. 테스트 프로젝트 생성
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def check_server_status(server_url):
    """서버가 실행 중인지 확인합니다."""
    try:
        response = requests.get(server_url)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"서버 상태: 실행 중 ({data.get('name')} {data.get('version')})")
            return True
        else:
            logger.error(f"서버 응답 오류: 상태 코드 {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"서버 연결 오류: {e}")
        return False

def get_available_tools(server_url):
    """서버에서 사용 가능한 도구 목록을 가져옵니다."""
    try:
        response = requests.get(f"{server_url}/tools")
        if response.status_code == 200:
            tools = response.json().get("tools", [])
            logger.info(f"{len(tools)}개의 도구를 사용할 수 있습니다:")
            for tool in tools:
                logger.info(f"  - {tool['name']}: {tool.get('description', '설명 없음')}")
            return tools
        else:
            logger.error(f"도구 목록 가져오기 실패: 상태 코드 {response.status_code}")
            return []
    except requests.RequestException as e:
        logger.error(f"도구 목록 가져오기 실패: {e}")
        return []

def invoke_tool(server_url, tool_name, parameters):
    """도구를 호출합니다."""
    try:
        response = requests.post(
            f"{server_url}/invoke",
            json={"name": tool_name, "parameters": parameters}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"도구 호출 실패: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        logger.error(f"도구 호출 중 오류 발생: {e}")
        return None

def create_test_project(server_url):
    """테스트 프로젝트를 생성합니다."""
    logger.info("테스트 프로젝트 생성 중...")
    project_name = f"테스트 프로젝트 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    result = invoke_tool(server_url, "create_project", {
        "name": project_name,
        "description": "이 프로젝트는 PMAgent MCP 서버 테스트용입니다."
    })
    
    if result and "project" in result:
        project = result["project"]
        logger.info(f"프로젝트 생성 성공: {project['name']} (ID: {project['id']})")
        
        # 테스트 태스크 생성
        create_test_task(server_url, project["id"])
        
        return project
    else:
        logger.error("프로젝트 생성 실패")
        return None

def create_test_task(server_url, project_id):
    """테스트 태스크를 생성합니다."""
    logger.info(f"프로젝트 {project_id}에 테스트 태스크 생성 중...")
    
    result = invoke_tool(server_url, "create_task", {
        "project_id": project_id,
        "name": "테스트 태스크",
        "description": "이 태스크는 PMAgent MCP 서버 테스트용입니다.",
        "status": "TODO",
        "assignee": "테스터"
    })
    
    if result and "task" in result:
        task = result["task"]
        logger.info(f"태스크 생성 성공: {task['name']} (ID: {task['id']})")
        return task
    else:
        logger.error("태스크 생성 실패")
        return None

def list_projects(server_url):
    """모든 프로젝트 목록을 가져옵니다."""
    logger.info("프로젝트 목록 가져오는 중...")
    
    result = invoke_tool(server_url, "list_projects", {})
    
    if result and "projects" in result:
        projects = result["projects"]
        logger.info(f"{len(projects)}개의 프로젝트를 찾았습니다:")
        for project in projects:
            logger.info(f"  - {project['name']} (ID: {project['id']})")
            
            # 각 프로젝트의 태스크 목록 가져오기
            list_tasks(server_url, project["id"])
        
        return projects
    else:
        logger.error("프로젝트 목록 가져오기 실패")
        return []

def list_tasks(server_url, project_id):
    """프로젝트의 모든 태스크 목록을 가져옵니다."""
    logger.info(f"프로젝트 {project_id}의 태스크 목록 가져오는 중...")
    
    result = invoke_tool(server_url, "list_tasks", {
        "project_id": project_id
    })
    
    if result and "tasks" in result:
        tasks = result["tasks"]
        logger.info(f"  {len(tasks)}개의 태스크를 찾았습니다:")
        for task in tasks:
            logger.info(f"    - {task['name']} ({task['status']}) - 담당: {task.get('assignee', 'N/A')}")
        return tasks
    else:
        logger.error(f"프로젝트 {project_id}의 태스크 목록 가져오기 실패")
        return []

def register_with_smithery():
    """스미더리 레지스트리에 서버를 등록합니다. (가상 함수)"""
    logger.info("스미더리 레지스트리에 서버 등록 시뮬레이션...")
    logger.info("실제 환경에서는 스미더리 CLI 또는 API를 사용하여 등록하세요.")
    logger.info("명령 예시: smithery register --name pmagent --url http://localhost:8080 --version 0.1.0")
    
    # 실제 스미더리 등록 코드를 여기에 추가할 수 있습니다.
    # 이 예제에서는 시뮬레이션만 수행합니다.
    
    return True

def main():
    """메인 함수"""
    server_url = os.environ.get("SERVER_URL", "http://localhost:8080")
    
    logger.info(f"PMAgent MCP 서버 테스트 시작 (서버 URL: {server_url})")
    
    # 1. 서버 상태 확인
    if not check_server_status(server_url):
        logger.error(f"서버가 실행 중이 아닙니다. {server_url}에서 서버를 실행해 주세요.")
        return
    
    # 2. 사용 가능한 도구 목록 가져오기
    tools = get_available_tools(server_url)
    if not tools:
        logger.error("도구 목록을 가져올 수 없습니다.")
        return
    
    # 3. 프로젝트 목록 가져오기
    projects = list_projects(server_url)
    
    # 4. 테스트 프로젝트 생성
    if len(projects) == 0:
        project = create_test_project(server_url)
        if project:
            logger.info("테스트 완료: 테스트 프로젝트 및 태스크가 성공적으로 생성되었습니다.")
    else:
        logger.info("이미 프로젝트가 존재합니다. 새 테스트 프로젝트를 생성하지 않습니다.")
    
    # 5. 스미더리 등록 시뮬레이션
    register_with_smithery()
    
    logger.info("PMAgent MCP 서버 테스트 완료!")
    logger.info("이제 다른 MCP 클라이언트가 이 서버에 연결할 수 있습니다.")

if __name__ == "__main__":
    main() 