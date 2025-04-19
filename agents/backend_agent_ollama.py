import os
import requests
import json
from typing import Dict, List, Any, Optional, Union
import logging
try:
    from .mcp_agent_helper import MCPAgentHelper
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from .base_tool import BaseTool

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BackendAgentOllama")

class BackendAgentOllama(BaseTool):
    """
    Ollama를 통해 백엔드 개발 작업을 수행하는 에이전트
    
    BackendAgent와 동일한 인터페이스를 제공하되 Ollama API를 통해 로컬 LLM을 활용
    """
    
    def __init__(self, 
                api_key: Optional[str] = None, 
                api_base: Optional[str] = None,
                model: str = "llama3.2:latest",
                use_mcp: bool = False,
                mcp_helper = None,
                temperature: float = 0.7):
        """
        Ollama 백엔드 에이전트 초기화
        
        Args:
            api_key: 사용하지 않음 (호환성 유지용)
            api_base: Ollama API 기본 URL (기본값: http://localhost:11434/api)
            model: 사용할 Ollama 모델 (기본값: llama3.2:latest)
            use_mcp: MCP 사용 여부
            mcp_helper: MCP 헬퍼 인스턴스
            temperature: 생성 온도 (0.0 ~ 1.0)
        """
        super().__init__()
        
        self.api_key = api_key  # 호환성 유지용
        self.api_base = api_base or os.environ.get("OLLAMA_API_BASE", "http://localhost:11434/api")
        self.model = model
        self.temperature = temperature
        self.use_mcp = use_mcp
        self.mcp_helper = mcp_helper
        
        # 프로젝트 구성 초기화
        self.project_config = self._initialize_project_config()
        
        # Ollama 모델 상태 확인
        self._check_model_availability()
        
        logger.info(f"Ollama 백엔드 에이전트 초기화 완료 - 모델: {model}, API 기본 URL: {api_base}")
        
    def _initialize_project_config(self) -> Dict[str, Any]:
        """
        프로젝트 구성을 초기화합니다.
        
        Returns:
            Dict[str, Any]: 프로젝트 구성 정보
        """
        return {
            "framework": "Express.js",  # 기본값: Express.js
            "database": "MongoDB",      # 기본값: MongoDB
            "auth_provider": "JWT",     # 기본값: JWT
            "api_version": "v1",        # 기본값: v1
            "api_path": "src/api",      # 기본값: src/api
            "models_path": "src/models" # 기본값: src/models
        }
        
    def _check_model_availability(self) -> bool:
        """
        Ollama 모델 사용 가능 여부 확인
        
        Returns:
            모델 사용 가능 여부
        """
        try:
            logger.info(f"Ollama 모델 확인 중: {self.model}")
            models_url = f"{self.api_base}/tags"
            response = requests.get(models_url)
            
            if response.status_code != 200:
                logger.warning(f"Ollama API 응답 오류: {response.status_code}")
                return False
            
            models_data = response.json()
            models = [model.get("name", "") for model in models_data.get("models", [])]
            
            if self.model in models:
                logger.info(f"Ollama 모델 사용 가능: {self.model}")
                return True
            else:
                logger.warning(f"Ollama 모델을 찾을 수 없음: {self.model}")
                logger.info(f"사용 가능한 모델: {', '.join(models)}")
                
                # 대체 모델 사용 시도
                if len(models) > 0:
                    fallback_model = models[0]
                    logger.warning(f"⚠️ 경고: 모델 '{self.model}'은(는) 사용할 수 없습니다. 사용 가능한 모델: {', '.join(models)}")
                    logger.warning(f"⚠️ 대체 모델 '{fallback_model}'(을)를 사용합니다.")
                    self.model = fallback_model
                else:
                    logger.warning(f"⚠️ 경고: 모델 '{self.model}'은(는) 사용할 수 없으며, 사용 가능한 대체 모델이 없습니다.")
                    logger.warning("Ollama가 실행 중이고 모델이 정확한지 확인하세요.")
                return False
                
        except Exception as e:
            logger.error(f"Ollama 모델 확인 중 오류 발생: {str(e)}")
            logger.warning("Ollama가 실행 중인지 확인하세요.")
            return False
            
    def _ollama_request(self, prompt: str) -> Dict[str, Any]:
        """
        Ollama API 요청 수행
        
        Args:
            prompt: 요청 프롬프트
            
        Returns:
            Ollama API 응답
        """
        # MCP 우선 사용(설정된 경우)
        if self.use_mcp and self.mcp_helper:
            try:
                result = self.mcp_helper.generate_text(prompt=prompt)
                if result and isinstance(result, str):
                    return {"response": result}
                elif result and isinstance(result, dict):
                    return result
            except Exception as e:
                logger.warning(f"MCP 사용 실패, Ollama로 대체합니다: {str(e)}")
                # MCP 실패 시 Ollama로 계속 진행
        
        try:
            generate_url = f"{self.api_base}/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": self.temperature,
                "stream": False
            }
            
            response = requests.post(generate_url, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Ollama API 오류: {response.status_code}, {response.text}")
                raise Exception(f"Ollama API 오류: {response.status_code}")
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Ollama API 요청 중 오류 발생: {str(e)}")
            raise
            
    def create_api_endpoint(self, description: str) -> Dict[str, Any]:
        """
        API 엔드포인트 생성
        
        Args:
            description: API 엔드포인트 설명
            
        Returns:
            생성된 API 엔드포인트 정보
        """
        logger.info(f"API 엔드포인트 생성 요청: {description}")
        
        # HTTP 메서드 감지
        http_method = self.detect_http_method(description)
        endpoint = self.detect_endpoint(description)
        
        # Ollama API 요청 프롬프트 작성
        prompt = f"""
당신은 숙련된 백엔드 개발자입니다. 다음 설명을 바탕으로 API 엔드포인트를 구현해야 합니다:

설명: {description}
HTTP 메서드: {http_method}
엔드포인트 경로: {endpoint}
프레임워크: {self.project_config.get('framework', 'Express.js')}
데이터베이스: {self.project_config.get('database', 'MongoDB')}

요청 형식:
1. 엔드포인트 경로와 HTTP 메서드를 확인하세요.
2. 필요한 요청 파라미터와 응답 형식을 명시하세요.
3. 엔드포인트 구현에 필요한 전체 코드를 작성하세요.
4. 오류 처리 로직을 포함하세요.
5. API 응답은 일관된 형식을 따라야 합니다.

JSON 형식으로 응답하세요:
```json
{{
    "endpoint": "엔드포인트 경로",
    "method": "HTTP 메서드",
    "description": "간단한 설명",
    "parameters": [{{"name": "파라미터명", "type": "타입", "description": "설명", "required": true}}, ...],
    "responses": [{{"status": 200, "description": "설명", "example": {{}}}}],
    "code": "// 구현 코드"
}}
```
"""
        
        # Ollama 요청 수행
        try:
            response = self._ollama_request(prompt)
            
            # 응답 파싱
            output = response.get("response", "")
            
            # JSON 추출
            json_match = None
            try:
                # JSON 블록이 있는 경우 추출
                if "```json" in output and "```" in output.split("```json", 1)[1]:
                    json_text = output.split("```json", 1)[1].split("```", 1)[0].strip()
                    json_match = json.loads(json_text)
                else:
                    # 그냥 JSON인 경우
                    json_match = json.loads(output)
            except:
                # JSON 파싱 오류인 경우 텍스트 그대로 반환
                logger.warning("JSON 파싱 실패, 텍스트 응답으로 처리합니다")
                return {
                    "endpoint": endpoint,
                    "method": http_method,
                    "description": description,
                    "code": output
                }
            
            if json_match:
                return json_match
            else:
                return {
                    "endpoint": endpoint,
                    "method": http_method,
                    "description": description,
                    "code": output
                }
                
        except Exception as e:
            logger.error(f"API 엔드포인트 생성 중 오류 발생: {str(e)}")
            return {
                "endpoint": endpoint,
                "method": http_method,
                "description": description,
                "error": str(e)
            }
            
    def create_database_schema(self, description: str) -> Dict[str, Any]:
        """
        데이터베이스 스키마 생성
        
        Args:
            description: 데이터베이스 스키마 설명
            
        Returns:
            생성된 데이터베이스 스키마 정보
        """
        logger.info(f"데이터베이스 스키마 생성 요청: {description}")
        
        # Ollama API 요청 프롬프트 작성
        prompt = f"""
당신은 숙련된 백엔드 개발자입니다. 다음 설명을 바탕으로 데이터베이스 스키마를 구현해야 합니다:

설명: {description}
데이터베이스: {self.project_config.get('database', 'MongoDB')}
프레임워크: {self.project_config.get('framework', 'Express.js')}

요청 형식:
1. 데이터베이스 스키마 설계를 위한 엔티티를 식별하세요.
2. 각 엔티티의 속성과 데이터 타입을 명시하세요.
3. 엔티티 간의 관계를 정의하세요.
4. 스키마 구현에 필요한 전체 코드를 작성하세요.

JSON 형식으로 응답하세요:
```json
{{
    "database": "데이터베이스 종류",
    "entities": [
        {{
            "name": "엔티티명",
            "description": "설명",
            "attributes": [
                {{"name": "속성명", "type": "타입", "description": "설명", "required": true, "unique": true}},
                ...
            ],
            "relationships": [
                {{"entity": "관련 엔티티", "type": "관계 타입", "description": "설명"}},
                ...
            ]
        }},
        ...
    ],
    "code": "// 구현 코드"
}}
```
"""
        
        # Ollama 요청 수행
        try:
            response = self._ollama_request(prompt)
            
            # 응답 파싱
            output = response.get("response", "")
            
            # JSON 추출
            json_match = None
            try:
                # JSON 블록이 있는 경우 추출
                if "```json" in output and "```" in output.split("```json", 1)[1]:
                    json_text = output.split("```json", 1)[1].split("```", 1)[0].strip()
                    json_match = json.loads(json_text)
                else:
                    # 그냥 JSON인 경우
                    json_match = json.loads(output)
            except:
                # JSON 파싱 오류인 경우 텍스트 그대로 반환
                logger.warning("JSON 파싱 실패, 텍스트 응답으로 처리합니다")
                return {
                    "database": self.project_config.get('database', 'MongoDB'),
                    "description": description,
                    "code": output
                }
            
            if json_match:
                return json_match
            else:
                return {
                    "database": self.project_config.get('database', 'MongoDB'),
                    "description": description,
                    "code": output
                }
                
        except Exception as e:
            logger.error(f"데이터베이스 스키마 생성 중 오류 발생: {str(e)}")
            return {
                "database": self.project_config.get('database', 'MongoDB'),
                "description": description,
                "error": str(e)
            }
            
    def create_authentication_system(self, description: str) -> Dict[str, Any]:
        """
        인증 시스템 생성
        
        Args:
            description: 인증 시스템 설명
            
        Returns:
            생성된 인증 시스템 정보
        """
        logger.info(f"인증 시스템 생성 요청: {description}")
        
        # Ollama API 요청 프롬프트 작성
        prompt = f"""
당신은 숙련된 백엔드 개발자입니다. 다음 설명을 바탕으로 인증 시스템을 구현해야 합니다:

설명: {description}
프레임워크: {self.project_config.get('framework', 'Express.js')}
인증 방식: {self.project_config.get('auth_method', 'JWT')}

요청 형식:
1. 인증 시스템의 주요 기능을 식별하세요.
2. 사용자 인증 흐름을 설계하세요.
3. 보안 고려사항을 반영하세요.
4. 인증 시스템 구현에 필요한 전체 코드를 작성하세요.

JSON 형식으로 응답하세요:
```json
{{
    "auth_method": "인증 방식",
    "features": ["기능1", "기능2", ...],
    "flow": ["단계1", "단계2", ...],
    "endpoints": [
        {{"path": "경로", "method": "HTTP 메서드", "description": "설명"}},
        ...
    ],
    "security_considerations": ["고려사항1", "고려사항2", ...],
    "code": "// 구현 코드"
}}
```
"""
        
        # Ollama 요청 수행
        try:
            response = self._ollama_request(prompt)
            
            # 응답 파싱
            output = response.get("response", "")
            
            # JSON 추출
            json_match = None
            try:
                # JSON 블록이 있는 경우 추출
                if "```json" in output and "```" in output.split("```json", 1)[1]:
                    json_text = output.split("```json", 1)[1].split("```", 1)[0].strip()
                    json_match = json.loads(json_text)
                else:
                    # 그냥 JSON인 경우
                    json_match = json.loads(output)
            except:
                # JSON 파싱 오류인 경우 텍스트 그대로 반환
                logger.warning("JSON 파싱 실패, 텍스트 응답으로 처리합니다")
                return {
                    "auth_method": self.project_config.get('auth_method', 'JWT'),
                    "description": description,
                    "code": output
                }
            
            if json_match:
                return json_match
            else:
                return {
                    "auth_method": self.project_config.get('auth_method', 'JWT'),
                    "description": description,
                    "code": output
                }
                
        except Exception as e:
            logger.error(f"인증 시스템 생성 중 오류 발생: {str(e)}")
            return {
                "auth_method": self.project_config.get('auth_method', 'JWT'),
                "description": description,
                "error": str(e)
            }
            
    def run_task(self, description: str) -> Dict[str, Any]:
        """
        BackendAgent 메서드 오버라이드: 태스크 실행
        
        Ollama API를 통해 태스크 수행
        
        Args:
            description: 태스크 설명
            
        Returns:
            태스크 결과
        """
        # API 엔드포인트 관련 태스크인지 확인
        api_keywords = ["api", "endpoint", "route", "handler", "controller", "get", "post", "put", "delete", "patch"]
        
        # 데이터베이스 스키마 관련 태스크인지 확인
        schema_keywords = ["schema", "model", "database", "table", "entity", "attribute", "field", "column"]
        
        # 인증 시스템 관련 태스크인지 확인
        auth_keywords = ["auth", "authentication", "login", "register", "jwt", "token", "oauth", "permission"]
        
        # 태스크 유형 결정
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in api_keywords):
            logger.info(f"API 엔드포인트 태스크로 인식: {description}")
            return self.create_api_endpoint(description)
        elif any(keyword in description_lower for keyword in schema_keywords):
            logger.info(f"데이터베이스 스키마 태스크로 인식: {description}")
            return self.create_database_schema(description)
        elif any(keyword in description_lower for keyword in auth_keywords):
            logger.info(f"인증 시스템 태스크로 인식: {description}")
            return self.create_authentication_system(description)
        else:
            # 일반 태스크
            logger.info(f"일반 백엔드 태스크 실행: {description}")
            
            # Ollama API 요청 프롬프트 작성
            prompt = f"""
당신은 숙련된 백엔드 개발자입니다. 다음 설명을 바탕으로 백엔드 작업을 수행해야 합니다:

설명: {description}
프레임워크: {self.project_config.get('framework', 'Express.js')}
데이터베이스: {self.project_config.get('database', 'MongoDB')}

작업 결과를 JSON 형식으로 반환하세요. 코드가 필요한 경우 포함하세요.
"""
            
            # Ollama 요청 수행
            try:
                response = self._ollama_request(prompt)
                
                # 응답 파싱
                output = response.get("response", "")
                
                # JSON 추출 시도
                try:
                    if "```json" in output and "```" in output.split("```json", 1)[1]:
                        json_text = output.split("```json", 1)[1].split("```", 1)[0].strip()
                        return json.loads(json_text)
                    else:
                        # 텍스트 응답을 JSON으로 변환 시도
                        json_data = json.loads(output)
                        return json_data
                except:
                    # JSON 파싱 실패 시 텍스트로 반환
                    return {
                        "task": description,
                        "result": output
                    }
                    
            except Exception as e:
                logger.error(f"태스크 실행 중 오류 발생: {str(e)}")
                return {
                    "task": description,
                    "error": str(e)
                }
                
    def _run(self, tool_input: str) -> str:
        """
        BaseTool 메서드 오버라이드: 도구 실행
        
        Args:
            tool_input: 도구 입력 텍스트
            
        Returns:
            도구 실행 결과
        """
        try:
            # 결과를 문자열로 변환하여 반환
            result = self.run_task(tool_input)
            if isinstance(result, dict):
                return json.dumps(result, indent=2, ensure_ascii=False)
            else:
                return str(result)
        except Exception as e:
            logger.error(f"도구 실행 중 오류 발생: {str(e)}")
            return f"오류: {str(e)}"
            
    def detect_http_method(self, description: str) -> str:
        """
        설명에서 HTTP 메서드 감지
        
        Args:
            description: API 설명 텍스트
            
        Returns:
            감지된 HTTP 메서드 (GET, POST, PUT, DELETE 등)
        """
        description = description.lower()
        
        if "get" in description or "retrieve" in description or "fetch" in description or "list" in description or "query" in description:
            return "GET"
        elif "create" in description or "add" in description or "post" in description or "insert" in description:
            return "POST"
        elif "update" in description or "edit" in description or "modify" in description or "put" in description or "patch" in description:
            return "PUT"
        elif "delete" in description or "remove" in description:
            return "DELETE"
        
        # 기본값은 GET
        return "GET"
    
    def detect_endpoint(self, description: str) -> str:
        """
        설명에서 엔드포인트 경로 감지
        
        Args:
            description: API 설명 텍스트
            
        Returns:
            감지된 엔드포인트 경로 (/api/resource 형식)
        """
        words = description.lower().split()
        resources = []
        
        # 일반적인 리소스 키워드 찾기
        resource_indicators = ["user", "users", "product", "products", "order", "orders", 
                              "item", "items", "profile", "profiles", "cart", "carts",
                              "auth", "login", "logout", "register", "payment", "payments",
                              "category", "categories", "comment", "comments", "post", "posts"]
        
        for word in words:
            # 단어 정리 (특수문자 제거)
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word in resource_indicators:
                resources.append(clean_word)
        
        # 리소스 찾았는지 확인
        if not resources:
            # 설명에서 리소스 추측
            if "user" in description or "profile" in description:
                resources.append("users")
            elif "product" in description or "item" in description:
                resources.append("products")
            elif "order" in description:
                resources.append("orders")
            elif "auth" in description or "login" in description or "register" in description:
                resources.append("auth")
            elif "payment" in description:
                resources.append("payments")
            else:
                # 기본값
                resources.append("resources")
        
        # 엔드포인트 경로 구성
        api_version = self.project_config.get("api_version", "v1")
        endpoint = f"/api/{api_version}/{resources[0]}"
        
        return endpoint

# 테스트 코드
if __name__ == "__main__":
    # Ollama 백엔드 에이전트 생성
    agent = BackendAgentOllama(
        api_base="http://localhost:11434/api",
        model="codellama:7b-instruct"
    )
    
    # API 엔드포인트 생성 테스트
    api_desc = "사용자 프로필 정보를 가져오는 GET API 엔드포인트"
    api_result = agent.create_api_endpoint(api_desc)
    print("=== API 엔드포인트 생성 결과 ===")
    print(json.dumps(api_result, indent=2, ensure_ascii=False))
    
    # 데이터베이스 스키마 생성 테스트
    schema_desc = "온라인 쇼핑몰 제품 카탈로그 데이터베이스 스키마"
    schema_result = agent.create_database_schema(schema_desc)
    print("\n=== 데이터베이스 스키마 생성 결과 ===")
    print(json.dumps(schema_result, indent=2, ensure_ascii=False))
    
    # 인증 시스템 생성 테스트
    auth_desc = "OAuth 및 JWT를 사용한 사용자 인증 시스템"
    auth_result = agent.create_authentication_system(auth_desc)
    print("\n=== 인증 시스템 생성 결과 ===")
    print(json.dumps(auth_result, indent=2, ensure_ascii=False)) 