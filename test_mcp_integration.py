import os
import sys
from typing import Optional

try:
    from unity_mcp_client import UnityMCP
    UNITY_MCP_AVAILABLE = True
except ImportError:
    UNITY_MCP_AVAILABLE = False

def test_unity_mcp():
    """Unity MCP 클라이언트 테스트"""
    print("=== Unity MCP 클라이언트 테스트 ===")
    
    if not UNITY_MCP_AVAILABLE:
        print("Unity MCP 클라이언트가 설치되어 있지 않습니다.")
        print("설치 방법: pip install unity-mcp-client")
        return False
    
    try:
        # MCP 서버 URL (실제 서버가 없으므로 테스트용 URL 사용)
        mcp_host = os.environ.get("MCP_HOST", "http://localhost:8045")
        
        # MCP 클라이언트 초기화
        client = UnityMCP(host=mcp_host)
        
        # 사용 가능한 MCP 기능 출력
        print(f"Unity MCP 클라이언트 초기화 성공: {client}")
        print(f"MCP 호스트: {mcp_host}")
        print("사용 가능한 기능들:")
        for method_name in dir(client):
            if not method_name.startswith('_') and callable(getattr(client, method_name)):
                print(f"  - {method_name}")
        
        return True
    except Exception as e:
        print(f"Unity MCP 연결 오류: {e}")
        return False

def create_mcp_agent_helper():
    """MCP와 통합된 에이전트 헬퍼 클래스 생성"""
    class MCPAgentHelper:
        """MCP 도구들과 에이전트 연결을 관리하는 헬퍼 클래스"""
        
        def __init__(self, mcp_host: Optional[str] = None, github_token: Optional[str] = None, figma_token: Optional[str] = None):
            self.mcp_host = mcp_host or os.environ.get("MCP_HOST", "http://localhost:8045")
            self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
            self.figma_token = figma_token or os.environ.get("FIGMA_TOKEN")
            
            # Unity MCP 클라이언트 초기화 (설치된 경우)
            self.unity_mcp = None
            if UNITY_MCP_AVAILABLE:
                try:
                    self.unity_mcp = UnityMCP(host=self.mcp_host)
                    print(f"Unity MCP 클라이언트 초기화 성공")
                except Exception as e:
                    print(f"Unity MCP 초기화 오류: {e}")
            
            # 다른 MCP 도구들 초기화 (주석 처리됨)
            # self.github_mcp = None
            # self.figma_mcp = None
            
            # # GitHub MCP 초기화 (토큰이 있는 경우)
            # if self.github_token:
            #     try:
            #         # from some_github_lib import GitHubMCP
            #         # self.github_mcp = GitHubMCP(token=self.github_token)
            #         print("GitHub MCP 초기화됨 (시뮬레이션)")
            #     except Exception as e:
            #         print(f"GitHub MCP 초기화 오류: {e}")
            
            # # Figma MCP 초기화 (토큰이 있는 경우)
            # if self.figma_token:
            #     try:
            #         # from some_figma_lib import FigmaMCP
            #         # self.figma_mcp = FigmaMCP(token=self.figma_token)
            #         print("Figma MCP 초기화됨 (시뮬레이션)")
            #     except Exception as e:
            #         print(f"Figma MCP 초기화 오류: {e}")
        
        def has_unity_mcp(self) -> bool:
            """Unity MCP 클라이언트가 사용 가능한지 확인"""
            return self.unity_mcp is not None
        
        def has_github_mcp(self) -> bool:
            """GitHub MCP가 사용 가능한지 확인"""
            return hasattr(self, 'github_mcp') and self.github_mcp is not None
        
        def has_figma_mcp(self) -> bool:
            """Figma MCP가 사용 가능한지 확인"""
            return hasattr(self, 'figma_mcp') and self.figma_mcp is not None
        
        def get_available_mcps(self) -> dict:
            """사용 가능한 MCP 목록 반환"""
            return {
                "unity_mcp": self.has_unity_mcp(),
                "github_mcp": self.has_github_mcp(),
                "figma_mcp": self.has_figma_mcp()
            }
    
    return MCPAgentHelper()

if __name__ == "__main__":
    # Unity MCP 클라이언트 테스트
    test_unity_mcp()
    
    print("\n=== MCP 에이전트 헬퍼 테스트 ===")
    helper = create_mcp_agent_helper()
    available_mcps = helper.get_available_mcps()
    
    print("사용 가능한 MCP:")
    for mcp_name, available in available_mcps.items():
        status = "사용 가능" if available else "사용 불가"
        print(f"  - {mcp_name}: {status}") 