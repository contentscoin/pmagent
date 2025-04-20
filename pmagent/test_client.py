#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import argparse
import logging
from datetime import datetime
import sys
from .agent import PMAgent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description='MCP 프로젝트 관리 에이전트 테스트 클라이언트')
    parser.add_argument('--url', default='http://localhost:8080', help='MCP 서버 URL')
    parser.add_argument('--action', choices=['list', 'create', 'update', 'delete', 'get'], 
                      required=True, help='수행할 작업')
    parser.add_argument('--type', choices=['project', 'task'], default='project', 
                      help='작업 대상 (프로젝트 또는 작업)')
    parser.add_argument('--project-id', help='프로젝트 ID (작업 관련 명령에 필요)')
    parser.add_argument('--task-id', help='작업 ID (작업 업데이트/삭제/조회에 필요)')
    parser.add_argument('--name', help='프로젝트 또는 작업 이름')
    parser.add_argument('--description', help='프로젝트 또는 작업 설명')
    parser.add_argument('--status', help='프로젝트 또는 작업 상태')
    parser.add_argument('--due-date', help='작업 마감일 (YYYY-MM-DD)')
    parser.add_argument('--assignee', help='작업 담당자')
    
    args = parser.parse_args()
    
    agent = PMAgent(server_url=args.url)
    
    try:
        # 도구 목록 조회
        tools = await agent.get_tools()
        logger.info(f"사용 가능한 도구: {', '.join(tools)}")
        
        # 작업 수행
        if args.action == 'list':
            if args.type == 'project':
                projects = await agent.list_projects()
                if projects:
                    logger.info(f"{len(projects)}개의 프로젝트를 찾았습니다:")
                    for project in projects:
                        logger.info(f"  ID: {project['id']}, 이름: {project['name']}, " +
                                  f"상태: {project.get('status', 'N/A')}")
                else:
                    logger.info("프로젝트가 없습니다.")
            elif args.type == 'task':
                if not args.project_id:
                    logger.error("작업 목록 조회 시 프로젝트 ID가 필요합니다.")
                    return
                
                tasks = await agent.list_tasks(args.project_id)
                if tasks:
                    logger.info(f"{len(tasks)}개의 작업을 찾았습니다:")
                    for task in tasks:
                        logger.info(f"  ID: {task['id']}, 이름: {task['name']}, " +
                                  f"상태: {task.get('status', 'N/A')}")
                else:
                    logger.info("작업이 없습니다.")
            
        elif args.action == 'create':
            if args.type == 'project':
                if not args.name or not args.description:
                    logger.error("프로젝트 생성 시 이름과 설명이 필요합니다.")
                    return
                
                project = await agent.create_project(args.name, args.description)
                logger.info(f"프로젝트 생성됨: {project}")
            elif args.type == 'task':
                if not args.project_id or not args.name or not args.description:
                    logger.error("작업 생성 시 프로젝트 ID, 이름, 설명이 필요합니다.")
                    return
                
                task = await agent.create_task(
                    args.project_id,
                    args.name, 
                    args.description,
                    status=args.status,
                    due_date=args.due_date,
                    assignee=args.assignee
                )
                logger.info(f"작업 생성됨: {task}")
                
        elif args.action == 'get':
            if args.type == 'project':
                if not args.project_id:
                    logger.error("프로젝트 조회에는 프로젝트 ID가 필요합니다.")
                    return
                project = await agent.get_project(args.project_id)
                logger.info(f"조회된 프로젝트: {project}")
            elif args.type == 'task':
                if not args.project_id or not args.task_id:
                    logger.error("태스크 조회에는 프로젝트 ID와 태스크 ID가 필요합니다.")
                    return
                task = await agent.get_task(args.project_id, args.task_id)
                logger.info(f"조회된 태스크: {task}")
            
        elif args.action == 'update':
            if args.type == 'project':
                if not args.project_id:
                    logger.error("프로젝트 업데이트에는 프로젝트 ID가 필요합니다.")
                    return
                project = await agent.update_project(
                    args.project_id,
                    name=args.name,
                    description=args.description
                )
                logger.info(f"프로젝트 업데이트 결과: {project}")
            elif args.type == 'task':
                if not args.project_id or not args.task_id:
                    logger.error("태스크 업데이트에는 프로젝트 ID와 태스크 ID가 필요합니다.")
                    return
                task = await agent.update_task(
                    args.project_id,
                    args.task_id,
                    name=args.name,
                    description=args.description,
                    status=args.status,
                    due_date=args.due_date,
                    assignee=args.assignee
                )
                logger.info(f"태스크 업데이트 결과: {task}")
            
        elif args.action == 'delete':
            if args.type == 'project':
                if not args.project_id:
                    logger.error("프로젝트 삭제에는 프로젝트 ID가 필요합니다.")
                    return
                
                success = await agent.delete_project(args.project_id)
                if success:
                    logger.info(f"프로젝트 삭제 성공 (ID: {args.project_id})")
                else:
                    logger.error(f"프로젝트 삭제 실패 (ID: {args.project_id})")
            elif args.type == 'task':
                if not args.project_id or not args.task_id:
                    logger.error("태스크 삭제에는 프로젝트 ID와 태스크 ID가 필요합니다.")
                    return
                
                success = await agent.delete_task(args.project_id, args.task_id)
                if success:
                    logger.info(f"태스크 삭제 성공 (ID: {args.task_id})")
                else:
                    logger.error(f"태스크 삭제 실패 (ID: {args.task_id})")
        else:
            logger.error(f"알 수 없는 액션: {args.action}")
            return
                    
    except Exception as e:
        logger.error(f"오류 발생: {e}")
    finally:
        await agent.close_session()

def cli_entry_point():
    """CLI 진입점"""
    asyncio.run(main())

if __name__ == "__main__":
    cli_entry_point() 