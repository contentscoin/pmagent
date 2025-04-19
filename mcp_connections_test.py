#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP 연결 테스트

이 스크립트는 MCP(Model Context Protocol) 연결을 테스트합니다.
"""

import os
import sys
import traceback

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Unity MCP 클라이언트 가져오기
try:
    from unity_mcp_client import UnityMCP
    UNITY_MCP_AVAILABLE = True
except ImportError:
    UNITY_MCP_AVAILABLE = False

# 에이전트 디렉토리에서 MCP 헬퍼 가져오기
try:
    from agents.mcp_agent_helper import MCPAgentHelper
    MCP_HELPER_AVAILABLE = True
except ImportError:
    MCP_HELPER_AVAILABLE = False


def test_mcp_connections():
    """MCP 연결 테스트"""
    print("\n===== MCP 연결 테스트 =====\n")
    
    # Unity MCP 테스트
    if UNITY_MCP_AVAILABLE:
        print("Unity MCP 클라이언트 가져오기 성공")
        try:
            unity_mcp = UnityMCP(host="http://localhost:8045")
            print(f"Unity MCP 클라이언트 초기화 성공: {unity_mcp}")
            print(f"MCP 호스트: {unity_mcp.host}")
            print("사용 가능한 함수:")
            for method in [m for m in dir(unity_mcp) if not m.startswith('_')]:
                print(f"  - {method}")
        except Exception as e:
            print(f"Unity MCP 클라이언트 초기화 실패: {e}")
            traceback.print_exc()
    else:
        print("Unity MCP 클라이언트를 가져올 수 없습니다.")
        
    print("\n------------------------------\n")
    
    # MCP 헬퍼 테스트
    if MCP_HELPER_AVAILABLE:
        print("MCP 헬퍼 가져오기 성공")
        try:
            mcp_helper = MCPAgentHelper(
                unity_mcp_host="http://localhost:8045",
                github_token="dummy_token",
                figma_token="dummy_token",
                db_connection_string="dummy_connection_string"
            )
            print(f"MCP 헬퍼 초기화 성공: {mcp_helper}")
            
            # 사용 가능한 MCP 확인
            available_mcps = mcp_helper.get_available_mcps()
            print("\n사용 가능한 MCP:")
            for mcp_name, available in available_mcps.items():
                status = "✅ 사용 가능" if available else "❌ 사용 불가"
                print(f"  - {mcp_name}: {status}")
            
            # GitHub MCP 테스트
            if mcp_helper.has_github_mcp():
                print("\nGitHub MCP 테스트:")
                result = mcp_helper.commit_to_github("test.txt", "테스트 커밋", "테스트 내용")
                print(f"GitHub 커밋 결과: {result}")
            
            # Figma MCP 테스트
            if mcp_helper.has_figma_mcp():
                print("\nFigma MCP 테스트:")
                design_data = mcp_helper.get_design_data("design_id")
                print(f"Figma 디자인 데이터: {design_data}")
            
            # DB MCP 테스트
            if mcp_helper.has_db_mcp():
                print("\nDB MCP 테스트:")
                query_result = mcp_helper.execute_sql("SELECT * FROM users LIMIT 10")
                print(f"SQL 쿼리 결과: {query_result}")
                
        except Exception as e:
            print(f"MCP 헬퍼 초기화 실패: {e}")
            traceback.print_exc()
    else:
        print("MCP 헬퍼를 가져올 수 없습니다.")
    
    print("\n===== 테스트 완료 =====\n")


if __name__ == "__main__":
    test_mcp_connections() 