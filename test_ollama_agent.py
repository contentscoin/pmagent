import os
import requests
from typing import Dict, Any, Optional

class AIProvider:
    """AI 모델 제공자를 추상화한 클래스"""
    
    def __init__(self, provider_name: str = "ollama", model_name: Optional[str] = None):
        """
        AI 제공자 초기화
        
        Args:
            provider_name: AI 제공자 이름 ('ollama', 'openai', 'gemini' 등)
            model_name: 모델 이름 (제공자별 기본값 있음)
        """
        self.provider_name = provider_name
        
        # 제공자별 기본 모델 설정
        if provider_name == "ollama":
            self.model_name = model_name or "codellama"  # 코드 생성에 좋은 CodeLlama 기본 사용
            self.api_base = "http://localhost:11434/api"  # Ollama 기본 엔드포인트
        else:
            raise ValueError(f"지원되지 않는 AI 제공자: {provider_name}")
    
    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """
        텍스트 생성 메서드
        
        Args:
            prompt: 프롬프트 텍스트
            temperature: 창의성 조절 (0.0~1.0)
            max_tokens: 최대 생성 토큰 수
            
        Returns:
            str: 생성된 텍스트
        """
        if self.provider_name == "ollama":
            try:
                response = requests.post(
                    f"{self.api_base}/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": False
                    },
                    timeout=60  # 타임아웃 60초
                )
                response.raise_for_status()  # HTTP 에러 체크
                result = response.json()
                return result.get("response", "")
            except requests.exceptions.RequestException as e:
                print(f"Ollama API 호출 오류: {e}")
                return f"Ollama API 오류: {e}. Ollama가 설치되어 있고 실행 중인지 확인하세요."
    
    def generate_code(self, language: str, requirements: str) -> str:
        """
        코드 생성 특화 메서드
        
        Args:
            language: 프로그래밍 언어 (예: 'typescript', 'python')
            requirements: 코드 요구사항
            
        Returns:
            str: 생성된 코드
        """
        prompt = f"""
다음 요구사항에 맞게 {language} 코드를 작성해주세요.
코드만 반환하고, 설명이나 주석은 최소화해주세요.

요구사항:
{requirements}

{language} 코드:
"""
        return self.generate_text(prompt, temperature=0.2)  # 코드 생성은 낮은 온도로 일관성 높임

def test_ollama_connection():
    """Ollama 연결 테스트"""
    print("=== Ollama 연결 테스트 ===")
    
    try:
        # 기본 모델 정보 요청
        response = requests.get("http://localhost:11434/api/tags")
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"사용 가능한 모델 목록: {[model['name'] for model in models]}")
            print("Ollama 서버가 정상적으로 실행 중입니다.")
            return True
        else:
            print(f"Ollama 서버 응답 오류: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Ollama 서버 연결 오류: {e}")
        print("Ollama가 설치되어 있고 실행 중인지 확인하세요.")
        return False

def test_code_generation():
    """코드 생성 테스트"""
    print("\n=== 코드 생성 테스트 ===")
    
    # AIProvider 초기화
    ai = AIProvider(provider_name="ollama", model_name="codellama")
    
    # 간단한 Express.js API 엔드포인트 생성 요청
    requirements = "사용자 정보를 조회하는 GET /api/users/:id 엔드포인트 구현"
    
    print("요청 중... (20-30초 소요될 수 있습니다)")
    code = ai.generate_code("typescript", requirements)
    
    print("\n생성된 Express.js 코드:")
    print("-----------------------------------")
    print(code)
    print("-----------------------------------")

if __name__ == "__main__":
    # Ollama 서버 연결 테스트
    if test_ollama_connection():
        # 코드 생성 테스트
        test_code_generation() 