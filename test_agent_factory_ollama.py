import unittest
import os
import json
from unittest.mock import patch, MagicMock

from agents.agent_factory import AgentFactory
from agents.frontend_agent_ollama import FrontendAgentOllama
from agents.backend_agent_ollama import BackendAgentOllama

class TestAgentFactoryOllama(unittest.TestCase):
    """
    AgentFactory의 Ollama 에이전트 생성 및 사용을 테스트하는 클래스
    """
    
    def setUp(self):
        """테스트 설정"""
        # 테스트용 팩토리 인스턴스 생성
        self.factory = AgentFactory()
        
        # API 키 설정
        os.environ["OPENAI_API_KEY"] = "sk-test-key"
        
    def tearDown(self):
        """테스트 종료 후 정리"""
        # 캐시 정리
        self.factory.clear_cache()
        
        # 환경 변수 정리
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
            
    @patch('requests.get')
    def test_create_frontend_ollama_agent(self, mock_get):
        """FrontendAgentOllama 생성 테스트"""
        # 모델 확인 응답 모의 설정
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "models": [
                    {"name": "llama3:latest"}
                ]
            }
        )
        
        # FrontendAgentOllama 생성
        agent = self.factory.create_agent(
            "frontend_ollama",
            ollama_model="llama3:latest",
            ollama_api_base="http://localhost:11434/api"
        )
        
        # 타입 확인
        self.assertIsInstance(agent, FrontendAgentOllama)
        self.assertEqual(agent.model, "llama3:latest")
        self.assertEqual(agent.api_base, "http://localhost:11434/api")
        
        # 캐시 확인
        cached_agent = self.factory.create_agent(
            "frontend_ollama",
            ollama_model="llama3:latest"
        )
        self.assertIs(agent, cached_agent)
        
    @patch('requests.get')
    def test_create_backend_ollama_agent(self, mock_get):
        """BackendAgentOllama 생성 테스트"""
        # 모델 확인 응답 모의 설정
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "models": [
                    {"name": "codellama:7b-instruct"}
                ]
            }
        )
        
        # BackendAgentOllama 생성
        agent = self.factory.create_agent(
            "backend_ollama",
            ollama_model="codellama:7b-instruct",
            ollama_api_base="http://localhost:11434/api"
        )
        
        # 타입 확인
        self.assertIsInstance(agent, BackendAgentOllama)
        self.assertEqual(agent.model, "codellama:7b-instruct")
        self.assertEqual(agent.api_base, "http://localhost:11434/api")
        
        # 캐시 확인
        cached_agent = self.factory.create_agent(
            "backend_ollama",
            ollama_model="codellama:7b-instruct"
        )
        self.assertIs(agent, cached_agent)
        
    @patch('requests.get')
    def test_use_ollama_flag(self, mock_get):
        """use_ollama 플래그 테스트"""
        # 모델 확인 응답 모의 설정
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "models": [
                    {"name": "llama3:latest"}
                ]
            }
        )
        
        # use_ollama=True로 frontend 에이전트 생성
        agent = self.factory.create_agent(
            "frontend",
            use_ollama=True,
            ollama_model="llama3:latest"
        )
        
        # FrontendAgentOllama 타입 확인
        self.assertIsInstance(agent, FrontendAgentOllama)
        
        # use_ollama=True로 backend 에이전트 생성
        agent = self.factory.create_agent(
            "backend",
            use_ollama=True,
            ollama_model="llama3:latest"
        )
        
        # BackendAgentOllama 타입 확인
        self.assertIsInstance(agent, BackendAgentOllama)
        
    @patch('requests.get')
    @patch('requests.post')
    def test_backend_ollama_api_endpoint(self, mock_post, mock_get):
        """BackendAgentOllama API 엔드포인트 생성 테스트"""
        # 모델 확인 응답 모의 설정
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "models": [
                    {"name": "codellama:7b-instruct"}
                ]
            }
        )
        
        # Ollama API 응답 모의 설정
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "response": json.dumps({
                    "endpoint": "/api/users/profile",
                    "method": "GET",
                    "description": "사용자 프로필 정보 조회",
                    "code": "app.get('/api/users/profile', auth, (req, res) => { /* 코드 */ });"
                })
            }
        )
        
        # BackendAgentOllama 생성
        agent = self.factory.create_agent("backend_ollama", ollama_model="codellama:7b-instruct")
        
        # API 엔드포인트 생성 테스트
        result = agent.create_api_endpoint("사용자 프로필 정보를 가져오는 GET API 엔드포인트")
        
        # 응답 확인
        self.assertIn("endpoint", result)
        self.assertIn("method", result)
        self.assertIn("description", result)
        self.assertIn("code", result)
        
    @patch('requests.get')
    @patch('requests.post')
    def test_frontend_ollama_component(self, mock_post, mock_get):
        """FrontendAgentOllama 컴포넌트 생성 테스트"""
        # 모델 확인 응답 모의 설정
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "models": [
                    {"name": "llama3:latest"}
                ]
            }
        )
        
        # Ollama API 응답 모의 설정
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "response": "import React from 'react';\n\nconst Button = () => {\n  return <button>Click me</button>;\n};\n\nexport default Button;"
            }
        )
        
        # FrontendAgentOllama 생성
        agent = self.factory.create_agent("frontend_ollama", ollama_model="llama3:latest")
        
        # 컴포넌트 생성 테스트
        result = agent.generate_component("Button", {"type": "button", "color": "primary"})
        
        # 응답 확인
        self.assertEqual(result["name"], "Button")
        self.assertEqual(result["type"], "button")
        self.assertIn("code", result)
        self.assertIn("path", result)
        
    @patch('requests.get')
    def test_create_all_agents_with_ollama(self, mock_get):
        """create_all_agents에서 use_ollama 플래그 테스트"""
        # 모델 확인 응답 모의 설정
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "models": [
                    {"name": "llama3:latest"}
                ]
            }
        )
        
        # use_ollama=True로 모든 에이전트 생성
        agents = self.factory.create_all_agents(
            use_ollama=True,
            ollama_model="llama3:latest"
        )
        
        # 에이전트 타입 확인
        self.assertIsInstance(agents["frontend"], FrontendAgentOllama)
        self.assertIsInstance(agents["backend"], BackendAgentOllama)


if __name__ == "__main__":
    unittest.main() 