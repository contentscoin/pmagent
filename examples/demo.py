#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent 데모 스크립트

이 스크립트는 PMAgent의 주요 기능을 보여주기 위한 데모입니다.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pmagent.agent import PMAgent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # 에이전트 초기화
    agent = PMAgent(server_url="http://localhost:8000")
    
    try:
        # 사용 가능한 도구 확인
        tools = await agent.get_tools()
        logger.info(f"사용 가능한 도구: {', '.join(tools)}")
        
        # 1. 프로젝트 생성
        logger.info("\n=== 새 프로젝트 생성 ===")
        project = await agent.create_project(
            name="웹 애플리케이션 개발",
            description="React와 FastAPI를 사용한 웹 애플리케이션 개발 프로젝트"
        )
        project_id = project["id"]
        logger.info(f"생성된 프로젝트: {project}")
        
        # 2. 여러 태스크 생성
        logger.info("\n=== 태스크 생성 ===")
        
        # 오늘 날짜 기준으로 마감일 계산
        today = datetime.now()
        
        # 백엔드 태스크
        backend_task = await agent.create_task(
            project_id=project_id,
            name="백엔드 API 개발",
            description="FastAPI를 사용한 RESTful API 개발",
            status="TODO",
            due_date=(today + timedelta(days=14)).isoformat(),
            assignee="김서버"
        )
        logger.info(f"백엔드 태스크 생성됨: {backend_task}")
        
        # 프론트엔드 태스크
        frontend_task = await agent.create_task(
            project_id=project_id,
            name="프론트엔드 개발",
            description="React 컴포넌트 및 페이지 개발",
            status="TODO",
            due_date=(today + timedelta(days=21)).isoformat(),
            assignee="이프론트"
        )
        logger.info(f"프론트엔드 태스크 생성됨: {frontend_task}")
        
        # 테스트 태스크
        test_task = await agent.create_task(
            project_id=project_id,
            name="테스트 작성",
            description="단위 테스트 및 통합 테스트 작성",
            status="TODO",
            due_date=(today + timedelta(days=28)).isoformat(),
            assignee="박테스터"
        )
        logger.info(f"테스트 태스크 생성됨: {test_task}")
        
        # 3. 태스크 목록 조회
        logger.info("\n=== 태스크 목록 조회 ===")
        tasks = await agent.list_tasks(project_id)
        logger.info(f"프로젝트 '{project['name']}'의 태스크 ({len(tasks)}개):")
        for task in tasks:
            logger.info(f"  - {task['name']} ({task['status']}) - 담당: {task['assignee']}, 마감일: {task['due_date']}")
        
        # 4. 태스크 상태 업데이트
        logger.info("\n=== 태스크 상태 업데이트 ===")
        updated_task = await agent.update_task(
            project_id=project_id,
            task_id=backend_task["id"],
            status="IN_PROGRESS"
        )
        logger.info(f"업데이트된 태스크: {updated_task}")
        
        # 5. 업데이트된 태스크 목록 다시 조회
        logger.info("\n=== 업데이트 후 태스크 목록 ===")
        tasks = await agent.list_tasks(project_id)
        for task in tasks:
            logger.info(f"  - {task['name']} ({task['status']}) - 담당: {task['assignee']}")
        
        # 6. 실제 환경에서는 삭제하지 않을 수 있으므로 주석 처리
        # 태스크 삭제
        #logger.info("\n=== 태스크 삭제 ===")
        #success = await agent.delete_task(project_id, test_task["id"])
        #logger.info(f"태스크 삭제 {'성공' if success else '실패'}")
        
        # 프로젝트 삭제
        #logger.info("\n=== 프로젝트 삭제 ===")
        #success = await agent.delete_project(project_id)
        #logger.info(f"프로젝트 삭제 {'성공' if success else '실패'}")
        
        logger.info("\n=== 데모 완료 ===")
        logger.info(f"생성된 프로젝트 ID: {project_id}")
        for task in tasks:
            logger.info(f"생성된 태스크 ID: {task['id']} ({task['name']})")
        
    except Exception as e:
        logger.error(f"데모 실행 중 오류 발생: {e}", exc_info=True)
    finally:
        # 세션 종료
        await agent.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 