#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
순환 임포트 테스트 스크립트

순환 임포트 문제가 해결되었는지 확인합니다.
"""

import sys
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """순환 임포트 문제가 해결되었는지 확인"""
    logger.info("=== 순환 임포트 테스트 시작 ===")
    
    try:
        # 1. mcp_common에서 MCPServer 가져오기
        logger.info("1. mcp_common에서 MCPServer 가져오기")
        from pmagent.mcp_common import MCPServer
        logger.info("성공: MCPServer를 mcp_common에서 가져왔습니다.")
        
        # 2. mcp_agent_api에서 create_mcp_api 가져오기
        logger.info("2. mcp_agent_api에서 create_mcp_api 가져오기")
        from pmagent.mcp_agent_api import create_mcp_api
        logger.info("성공: create_mcp_api를 mcp_agent_api에서 가져왔습니다.")
        
        # 3. mcp_server에서 start_server 가져오기
        logger.info("3. mcp_server에서 start_server 가져오기")
        from pmagent.mcp_server import start_server
        logger.info("성공: start_server를 mcp_server에서 가져왔습니다.")
        
        # 4. API 생성 테스트
        logger.info("4. API 생성 테스트")
        mcp_api = create_mcp_api()
        logger.info(f"성공: API 생성 완료 (MCP 서버: {type(mcp_api.mcp_server).__name__})")
        
        logger.info("모든 임포트 테스트 성공!")
        return True
    except ImportError as e:
        logger.error(f"임포트 오류: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"기타 오류: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 