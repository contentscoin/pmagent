#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ollama 기반 에이전트 테스트 스크립트
"""

import os
import sys
from typing import Dict, Any
import traceback

# 현재 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_separator():
    """구분선 출력"""
    print("\n" + "="*50 + "\n")

def test_agent_factory():
    """AgentFactory 테스트"""
    try:
        from agents.agent_factory import AgentFactory
        
        print("AgentFactory 클래스 가져오기 성공")
        factory = AgentFactory()
        print(f"AgentFactory 인스턴스 생성 성공: {factory}")
        
        # 사용 가능한 메서드 출력
        methods = [method for method in dir(factory) if callable(getattr(factory, method)) and not method.startswith('__')]
        print(f"사용 가능한 메서드: {methods}")
        
        return factory
    except Exception as e:
        print(f"AgentFactory 테스트 실패: {e}")
        traceback.print_exc()
        return None

def test_single_agent(factory, agent_type: str):
    """단일 에이전트 생성 테스트"""
    try:
        print(f"\n{agent_type} 에이전트 생성 시도 중...")
        agent = factory.create_agent(agent_type)
        print(f"{agent_type} 에이전트 생성 성공: {type(agent).__name__}")
        
        # 에이전트 메서드 출력
        methods = [method for method in dir(agent) if callable(getattr(agent, method)) and not method.startswith('__')]
        print(f"사용 가능한 메서드: {methods[:10]}...")  # 처음 10개만 출력
        
        return agent
    except Exception as e:
        print(f"{agent_type} 에이전트 생성 실패: {e}")
        traceback.print_exc()
        return None

def test_create_all_agents(factory):
    """모든 에이전트 생성 테스트"""
    try:
        # PM 에이전트 객체에 get_available_models 메서드가 없는 문제 해결
        print("\n개별적으로 모든 에이전트 생성 시도 중...")
        agents = {}
        
        # 모든 에이전트 유형 처리
        agent_types = ["designer", "frontend", "backend", "ai_engineer", "pm"]
        for agent_type in agent_types:
            try:
                agents[agent_type] = factory.create_agent(agent_type)
                print(f"- {agent_type}: {type(agents[agent_type]).__name__}")
            except Exception as e:
                print(f"- {agent_type} 생성 실패: {str(e)}")
        
        print(f"생성된 에이전트: {len(agents)} 에이전트")
        return agents
    except Exception as e:
        print(f"모든 에이전트 생성 시도 실패: {e}")
        traceback.print_exc()
        return None

def test_mcp_helper(factory):
    """MCP 헬퍼 테스트"""
    try:
        print("\nMCP 헬퍼 생성 시도 중...")
        mcp_helper = factory.create_mcp_helper()
        print(f"MCP 헬퍼 생성 성공: {type(mcp_helper).__name__}")
        
        # 사용 가능한 MCPs 확인
        available_mcps = mcp_helper.get_available_mcps()
        print(f"사용 가능한 MCPs: {available_mcps}")
        
        return mcp_helper
    except Exception as e:
        print(f"MCP 헬퍼 생성 실패: {e}")
        traceback.print_exc()
        return None

def main():
    """메인 함수"""
    print_separator()
    print("Ollama 기반 에이전트 테스트 시작")
    print_separator()
    
    # AgentFactory 테스트
    factory = test_agent_factory()
    if not factory:
        print("AgentFactory 테스트 실패로 인해 프로그램을 종료합니다.")
        return
    
    print_separator()
    
    # 개별 에이전트 테스트
    agent_types = [
        "pm", 
        "designer", 
        "frontend", 
        "backend", 
        "ai_engineer"
    ]
    
    for agent_type in agent_types:
        test_single_agent(factory, agent_type)
        print_separator()
    
    # 모든 에이전트 생성 테스트
    test_create_all_agents(factory)
    print_separator()
    
    # MCP 헬퍼 테스트
    test_mcp_helper(factory)
    print_separator()
    
    print("모든 테스트 완료")

if __name__ == "__main__":
    main() 