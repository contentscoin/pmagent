#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
간단한 에이전트 테스트 스크립트
결과를 파일로 출력하여 PowerShell 렌더링 문제를 우회합니다.
"""

import os
import sys
from typing import Dict, Any

# 현재 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent_factory import AgentFactory

def main():
    # 결과를 저장할 파일
    with open("test_results.txt", "w", encoding="utf-8") as f:
        f.write("\n" + "=" * 50 + "\n")
        f.write(" 간단한 에이전트 시스템 테스트 ".center(50, "=") + "\n")
        f.write("=" * 50 + "\n\n")

        # AgentFactory 인스턴스 생성
        factory = AgentFactory()
        
        # 테스트 1: 존재하지 않는 모델로 에이전트 생성 (자동 대체 테스트)
        f.write("\n=== 테스트 1: 모델 자동 대체 기능 ===\n")
        designer_agent = factory.create_agent(
            "designer", 
            ollama_model="llama3:latest"  # 존재하지 않으면 자동으로 다른 모델로 대체됨
        )
        f.write(f"디자이너 에이전트 생성 성공: {type(designer_agent).__name__}\n")
        f.write(f"사용된 모델: {designer_agent.model}\n")
        
        # 테스트 2: create_all_agents 테스트
        f.write("\n=== 테스트 2: 모든 에이전트 생성 ===\n")
        try:
            all_agents = factory.create_all_agents(
                ollama_model="llama3:latest",  # 존재하지 않으면 자동으로 다른 모델로 대체됨
                connect_to_pm=True
            )
            f.write("모든 에이전트 생성 성공!\n")
            f.write(f"생성된 에이전트: {', '.join(all_agents.keys())}\n")
            
            # 각 에이전트 유형과 사용 모델 출력
            f.write("\n생성된 에이전트 정보:\n")
            for agent_type, agent in all_agents.items():
                f.write(f"- {agent_type}: {type(agent).__name__}, 모델: {agent.model}\n")
                
        except Exception as e:
            f.write(f"모든 에이전트 생성 중 오류 발생: {str(e)}\n")
            import traceback
            f.write(traceback.format_exc())
        
        # 테스트 3: MCP 헬퍼 생성 테스트
        f.write("\n=== 테스트 3: MCP 헬퍼 ===\n")
        try:
            mcp_helper = factory.create_mcp_helper()
            mcps = mcp_helper.get_available_mcps()
            f.write("사용 가능한 MCP:\n")
            for mcp_name, available in mcps.items():
                status = "✅ 사용 가능" if available else "❌ 사용 불가"
                f.write(f"- {mcp_name}: {status}\n")
        except Exception as e:
            f.write(f"MCP 헬퍼 테스트 중 오류 발생: {str(e)}\n")
        
        f.write("\n" + "=" * 50 + "\n")
        f.write(" 테스트 완료 ".center(50, "=") + "\n")
        f.write("=" * 50 + "\n")
    
    print(f"테스트 완료! 결과는 'test_results.txt' 파일에 저장되었습니다.")

if __name__ == "__main__":
    main() 