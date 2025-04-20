#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent 사용 예제
"""

import sys
import logging
from datetime import datetime
from pmagent import PMAgent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    """예제 프로그램"""
    
    # 서버 URL 설정 (기본값 사용 또는 커맨드 라인에서 지정)
    server_url = "http://localhost:8000" if len(sys.argv) < 2 else sys.argv[1]
    
    # PMAgent 인스턴스 생성
    agent = PMAgent(server_url)
    
    try:
        # 1. 모든 프로젝트 조회
        logger.info("프로젝트 목록 조회:")
        projects = agent.list_projects_sync()
        for project in projects:
            logger.info(f"  - {project['id']}: {project['name']}")
        
        # 2. 새 프로젝트 생성
        project_name = f"테스트 프로젝트 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logger.info(f"새 프로젝트 생성: {project_name}")
        new_project = agent.create_project_sync(
            name=project_name,
            description="PMAgent 예제 프로젝트입니다."
        )
        project_id = new_project["id"]
        logger.info(f"생성된 프로젝트 ID: {project_id}")
        
        # 3. 프로젝트에 태스크 추가
        logger.info("태스크 생성:")
        task1 = agent.create_task_sync(
            project_id=project_id,
            name="기능 구현",
            description="핵심 기능 구현하기",
            status="TODO",
            due_date="2023-12-31",
            assignee="김개발"
        )
        logger.info(f"  - 태스크 생성됨: {task1['id']} - {task1['name']}")
        
        # 4. 프로젝트 태스크 목록 조회
        logger.info(f"프로젝트 {project_id}의 태스크 목록:")
        tasks = agent.get_tasks_sync(project_id=project_id)
        for task in tasks:
            logger.info(f"  - {task['id']}: {task['name']} ({task['status']})")
        
        # 5. 태스크 상태 업데이트
        task_id = task1["id"]
        logger.info(f"태스크 {task_id} 상태 업데이트:")
        updated_task = agent.update_task_sync(
            project_id=project_id,
            task_id=task_id,
            status="IN_PROGRESS"
        )
        logger.info(f"  - 업데이트됨: {updated_task['name']} - 상태: {updated_task['status']}")
        
        # 6. 태스크 삭제 (선택적)
        # logger.info(f"태스크 {task_id} 삭제:")
        # agent.delete_task_sync(project_id=project_id, task_id=task_id)
        # logger.info("  - 삭제 완료")
        
        # 7. 프로젝트 삭제 (선택적)
        # logger.info(f"프로젝트 {project_id} 삭제:")
        # agent.delete_project_sync(project_id=project_id)
        # logger.info("  - 삭제 완료")
        
    except Exception as e:
        logger.error(f"오류 발생: {e}")
    finally:
        # 세션 종료
        agent.close()

if __name__ == "__main__":
    main() 