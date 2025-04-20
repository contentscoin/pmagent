#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent 비동기 API 사용 예제
"""

import sys
import logging
import asyncio
from datetime import datetime
from pmagent import PMAgent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def main():
    """비동기 예제 프로그램"""
    
    # 서버 URL 설정 (기본값 사용 또는 커맨드 라인에서 지정)
    server_url = "http://localhost:8000" if len(sys.argv) < 2 else sys.argv[1]
    
    # PMAgent 인스턴스 생성
    agent = PMAgent(server_url)
    
    try:
        # 세션 초기화
        await agent.init_session()
        
        # 1. 모든 프로젝트 조회
        logger.info("프로젝트 목록 조회:")
        projects = await agent.list_projects()
        for project in projects:
            logger.info(f"  - {project['id']}: {project['name']}")
        
        # 2. 새 프로젝트 생성
        project_name = f"비동기 테스트 프로젝트 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logger.info(f"새 프로젝트 생성: {project_name}")
        new_project = await agent.create_project(
            name=project_name,
            description="PMAgent 비동기 예제 프로젝트입니다."
        )
        project_id = new_project["id"]
        logger.info(f"생성된 프로젝트 ID: {project_id}")
        
        # 3. 여러 태스크 동시에 생성
        logger.info("여러 태스크 동시 생성:")
        task_names = ["UI 개발", "API 개발", "테스트 작성", "문서화"]
        
        # 비동기 태스크 생성 함수
        async def create_task(name, index):
            result = await agent.create_task(
                project_id=project_id,
                name=name,
                description=f"{name} 작업 수행하기",
                status="TODO",
                due_date="2023-12-31",
                assignee=f"개발자{index}"
            )
            return result
        
        # 여러 태스크를 동시에 생성
        tasks_futures = [create_task(name, i) for i, name in enumerate(task_names)]
        tasks_results = await asyncio.gather(*tasks_futures)
        
        # 생성된 태스크 출력
        for task in tasks_results:
            logger.info(f"  - 태스크 생성됨: {task['id']} - {task['name']}")
        
        # 4. 프로젝트 태스크 목록 조회
        logger.info(f"프로젝트 {project_id}의 태스크 목록:")
        tasks = await agent.get_tasks(project_id=project_id)
        task_ids = []
        for task in tasks:
            logger.info(f"  - {task['id']}: {task['name']} ({task['status']})")
            task_ids.append(task['id'])
        
        # 5. 태스크 동시 업데이트
        logger.info("여러 태스크 동시 업데이트:")
        
        # 비동기 태스크 업데이트 함수
        async def update_task(task_id):
            result = await agent.update_task(
                project_id=project_id,
                task_id=task_id,
                status="IN_PROGRESS"
            )
            return result
        
        # 여러 태스크를 동시에 업데이트
        update_futures = [update_task(task_id) for task_id in task_ids[:2]]
        update_results = await asyncio.gather(*update_futures)
        
        # 업데이트된 태스크 출력
        for task in update_results:
            logger.info(f"  - 업데이트됨: {task['id']} - {task['name']} - 상태: {task['status']}")
        
        # 6. 태스크 목록 다시 조회
        logger.info(f"업데이트 후 프로젝트 {project_id}의 태스크 목록:")
        tasks = await agent.get_tasks(project_id=project_id)
        for task in tasks:
            logger.info(f"  - {task['id']}: {task['name']} ({task['status']})")
        
        # 7. 프로젝트 정보 업데이트
        logger.info("프로젝트 정보 업데이트:")
        updated_project = await agent.update_project(
            project_id=project_id,
            description="업데이트된 프로젝트 설명입니다."
        )
        logger.info(f"  - 업데이트됨: {updated_project['name']} - 설명: {updated_project['description']}")
        
    except Exception as e:
        logger.error(f"오류 발생: {e}")
    finally:
        # 세션 종료
        await agent.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 