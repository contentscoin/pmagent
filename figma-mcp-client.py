import os
import json
import requests
from typing import Dict, Any, Optional, List, Union

class FigmaMCPClient:
    """
    Figma MCP 클라이언트 클래스
    
    이 클래스는 Figma MCP 서버와 통신하여 디자인 데이터를 가져오고
    Figma 디자인을 코드로 변환하는 기능을 제공합니다.
    """
    
    def __init__(
        self,
        token: Optional[str] = None,
        config_path: str = "figma-mcp-config.json",
        server_url: Optional[str] = None
    ):
        """
        Figma MCP 클라이언트 초기화
        
        Args:
            token (Optional[str]): Figma API 토큰 (기본값: 환경 변수 FIGMA_TOKEN)
            config_path (str): Figma MCP 설정 파일 경로 (기본값: "figma-mcp-config.json")
            server_url (Optional[str]): 서버 URL (설정 파일에 없는 경우 사용)
        """
        self.token = token or os.environ.get("FIGMA_TOKEN", "")
        self.config_path = config_path
        self.server_url = server_url
        self.config = {}
        
        # 설정 파일 로드
        self._load_config()
        
        # 서버 URL 설정
        if not self.server_url:
            if self.config and "mcpServers" in self.config and "TalkToFigma" in self.config["mcpServers"]:
                runtime = self.config["mcpServers"]["TalkToFigma"].get("runtime", {})
                server = runtime.get("server", "")
                if server:
                    self.server_url = f"http://{server}"
                    print(f"Figma MCP 서버 URL 설정: {self.server_url}")
        
        if not self.server_url:
            self.server_url = "http://localhost:8080"
            print(f"기본 Figma MCP 서버 URL 사용: {self.server_url}")
        
        # API 버전 설정
        self.api_version = "1.0.0"
        if self.config and "mcpServers" in self.config and "TalkToFigma" in self.config["mcpServers"]:
            runtime = self.config["mcpServers"]["TalkToFigma"].get("runtime", {})
            self.api_version = runtime.get("apiVersion", "1.0.0")
        
        self.headers = {
            "Content-Type": "application/json",
            "X-Figma-Token": self.token
        }
        
        print(f"Figma MCP 클라이언트 초기화 완료 (서버: {self.server_url}, API 버전: {self.api_version})")
    
    def _load_config(self) -> None:
        """Figma MCP 설정 파일 로드"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                print(f"Figma MCP 설정 파일 로드 완료: {self.config_path}")
            except Exception as e:
                print(f"Figma MCP 설정 파일 로드 실패: {str(e)}")
                self.config = {}
        else:
            print(f"Figma MCP 설정 파일을 찾을 수 없습니다: {self.config_path}")
            self.config = {}
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Figma MCP 서버에 API 요청
        
        Args:
            endpoint (str): API 엔드포인트
            method (str): HTTP 메서드 ("GET", "POST", "PUT" 등)
            data (Optional[Dict[str, Any]]): 요청 데이터
            
        Returns:
            Dict[str, Any]: 응답 데이터
            
        Raises:
            Exception: API 요청 실패 시
        """
        url = f"{self.server_url}/api/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=data or {})
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data or {})
            else:
                raise ValueError(f"지원되지 않는 HTTP 메서드: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Figma MCP API 요청 실패: {str(e)}")
            return {"error": str(e)}
    
    def get_file_info(self, file_key: str) -> Dict[str, Any]:
        """
        Figma 파일 정보 가져오기
        
        Args:
            file_key (str): Figma 파일 키
            
        Returns:
            Dict[str, Any]: 파일 정보
        """
        return self._make_request(f"figma/files/{file_key}")
    
    def get_components(self, file_key: str) -> List[Dict[str, Any]]:
        """
        Figma 파일의 컴포넌트 목록 가져오기
        
        Args:
            file_key (str): Figma 파일 키
            
        Returns:
            List[Dict[str, Any]]: 컴포넌트 목록
        """
        response = self._make_request(f"figma/files/{file_key}/components")
        return response.get("components", [])
    
    def get_component_code(self, file_key: str, node_id: str, format: str = "react") -> Dict[str, Any]:
        """
        Figma 컴포넌트를 코드로 변환
        
        Args:
            file_key (str): Figma 파일 키
            node_id (str): 컴포넌트 노드 ID
            format (str): 코드 형식 ("react", "vue", "html", "tailwind" 등)
            
        Returns:
            Dict[str, Any]: 변환된 코드와 메타데이터
        """
        data = {
            "format": format,
            "nodeId": node_id
        }
        return self._make_request(f"figma/files/{file_key}/code", method="POST", data=data)
    
    def get_design_tokens(self, file_key: str) -> Dict[str, Any]:
        """
        Figma 파일의 디자인 토큰 가져오기 (색상, 타이포그래피, 간격 등)
        
        Args:
            file_key (str): Figma 파일 키
            
        Returns:
            Dict[str, Any]: 디자인 토큰
        """
        return self._make_request(f"figma/files/{file_key}/tokens")
    
    def extract_design_system(self, file_key: str) -> Dict[str, Any]:
        """
        Figma 파일에서 디자인 시스템 추출
        
        Args:
            file_key (str): Figma 파일 키
            
        Returns:
            Dict[str, Any]: 디자인 시스템 정보
        """
        return self._make_request(f"figma/files/{file_key}/design-system")
    
    def generate_component(self, description: str) -> Dict[str, Any]:
        """
        설명을 기반으로 Figma 컴포넌트 생성
        
        Args:
            description (str): 컴포넌트 설명
            
        Returns:
            Dict[str, Any]: 생성된 컴포넌트 정보와 코드
        """
        data = {
            "description": description
        }
        return self._make_request("figma/generate/component", method="POST", data=data)
    
    def get_figma_url_info(self, figma_url: str) -> Dict[str, Any]:
        """
        Figma URL 정보 가져오기
        
        Args:
            figma_url (str): Figma URL
            
        Returns:
            Dict[str, Any]: URL 정보 (파일 키, 노드 ID 등)
        """
        data = {
            "url": figma_url
        }
        return self._make_request("figma/url-info", method="POST", data=data)


# 사용 예시
if __name__ == "__main__":
    # Figma MCP 클라이언트 생성
    figma_client = FigmaMCPClient()
    
    # 테스트 파일 키 (실제 사용 시 변경 필요)
    test_file_key = "abcdefghijklmnopqrst"
    
    try:
        # Figma 파일 정보 가져오기
        file_info = figma_client.get_file_info(test_file_key)
        print(f"파일 정보: {json.dumps(file_info, indent=2, ensure_ascii=False)}")
        
        # 컴포넌트 목록 가져오기
        components = figma_client.get_components(test_file_key)
        print(f"컴포넌트 수: {len(components)}")
        
        # 디자인 토큰 가져오기
        design_tokens = figma_client.get_design_tokens(test_file_key)
        print(f"디자인 토큰: {json.dumps(design_tokens, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}") 