#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
에이전트 테스트 스크립트

각 유형의 에이전트를 생성하고 에이전트 코디네이터에 등록하는 테스트를 수행합니다.
"""

import os
import sys
import logging
from pprint import pprint

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 에이전트 팩토리 임포트
from agents.agent_factory import AgentFactory
from pmagent.agent_coordinator import AgentCoordinator

def test_agent_creation():
    """에이전트 생성 테스트"""
    logger.info("=== 에이전트 생성 테스트 시작 ===")
    
    # 에이전트 팩토리 초기화
    agent_factory = AgentFactory()
    
    # 에이전트 코디네이터 초기화
    coordinator = AgentCoordinator()
    
    # 에이전트 유형 목록
    agent_types = ["pm", "designer", "frontend", "backend", "ai_engineer"]
    
    # 각 유형의 에이전트 생성 및 등록
    for agent_type in agent_types:
        try:
            logger.info(f"{agent_type} 에이전트 생성 시도...")
            agent = agent_factory.create_agent(
                agent_type=agent_type,
                ollama_model="llama3:latest",
                use_mcp=True
            )
            
            if agent:
                logger.info(f"{agent_type} 에이전트 생성 성공!")
                
                # 에이전트 등록
                agent_id = coordinator.register_agent(
                    agent_type=agent_type,
                    agent_instance=agent,
                    capabilities=["task_execution", "collaboration"]
                )
                logger.info(f"{agent_type} 에이전트 등록 성공 (ID: {agent_id})")
            else:
                logger.error(f"{agent_type} 에이전트 생성 실패!")
        except Exception as e:
            logger.error(f"{agent_type} 에이전트 처리 중 오류 발생: {str(e)}")
    
    # 등록된 에이전트 목록 조회
    all_agents = coordinator.get_all_agents()
    logger.info("=== 등록된 에이전트 목록 ===")
    pprint(all_agents)
    
    logger.info("=== 에이전트 생성 테스트 완료 ===")

def test_mcp_server():
    """MCP 서버 테스트"""
    logger.info("=== MCP 서버 테스트 시작 ===")
    
    try:
        from pmagent.mcp_agent_api import create_mcp_api
        
        # MCP API 생성
        mcp_api = create_mcp_api()
        
        logger.info("MCP API 생성 성공!")
        logger.info(f"API 앱: {mcp_api.api_app}")
        logger.info(f"MCP 서버: {mcp_api.mcp_server}")
        
        # 서버 실행은 하지 않고 객체만 생성 테스트
        # 실제로 실행하려면: mcp_api.start()
    except Exception as e:
        logger.error(f"MCP 서버 테스트 중 오류 발생: {str(e)}")
    
    logger.info("=== MCP 서버 테스트 완료 ===")

if __name__ == "__main__":
    # 에이전트 생성 테스트
    test_agent_creation()
    
    # MCP 서버 테스트
    test_mcp_server() 