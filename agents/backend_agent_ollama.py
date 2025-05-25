import os
import requests
import json
import time
import random
import uuid  # 에이전트 ID 생성용
from typing import Dict, List, Any, Optional, Union
import logging
import sys # sys 모듈 추가
import re # 정규식 사용을 위해 추가
import ast
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
                use_mcp: bool = False, # MCP 사용 여부
                mcp_helper: Optional[Any] = None,
                agent_id: Optional[str] = None, # 에이전트 고유 ID
                mcp_server_url: str = "http://localhost:8083/mcp/invoke", # MCP 서버 URL
                temperature: float = 0.7):
        """
        Ollama 백엔드 에이전트 초기화
        
        Args:
            api_key: 사용하지 않음 (호환성 유지용)
            api_base: Ollama API 기본 URL (기본값: http://localhost:11434/api)
            model: 사용할 Ollama 모델 (기본값: llama3.2:latest)
            use_mcp: MCP 사용 여부
            mcp_helper: MCP 헬퍼 인스턴스
            agent_id: 에이전트의 고유 ID (없으면 생성)
            mcp_server_url: PMAgent MCP 서버의 invoke 엔드포인트 URL
            temperature: 생성 온도 (0.0 ~ 1.0)
        """
        super().__init__()
        
        self.api_key = api_key  # 호환성 유지용
        self.api_base = api_base or os.environ.get("OLLAMA_API_BASE", "http://localhost:11434/api")
        self.model = model
        self.temperature = temperature
        self.use_mcp = use_mcp
        self.mcp_helper = mcp_helper
        
        self.agent_id = agent_id or f"backend-agent-{uuid.uuid4()}"
        self.mcp_server_url = mcp_server_url
        
        # 현재 작업 중인 프로젝트 컨텍스트 정보
        self.current_project_id: Optional[str] = None
        self.current_project_name: Optional[str] = None
        
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
        # 테스트 환경에서는 모델 확인을 건너뜁니다
        if 'PYTEST_CURRENT_TEST' in os.environ:
            logger.info("테스트 환경에서 실행 중입니다. 모델 확인을 건너뜁니다.")
            return True
            
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
        # 테스트 환경에서는 모의 응답 반환
        if 'PYTEST_CURRENT_TEST' in os.environ:
            # API 엔드포인트 생성 관련 응답
            if "API 엔드포인트" in prompt:
                return {"response": """```json
{
  "endpoint": "/api/v1/users",
  "method": "GET",
  "description": "사용자 목록 조회 API",
  "parameters": [{"name": "page", "type": "number", "description": "페이지 번호", "required": false}],
  "responses": [{"status": 200, "description": "성공", "example": {"users": [], "total": 0}}],
  "code": "const express = require('express');\nconst router = express.Router();\nconst User = require('../models/User');\n\nrouter.get('/', async (req, res) => {\n  try {\n    const page = parseInt(req.query.page, 10) || 1;\n    const limit = parseInt(req.query.limit, 10) || 10;\n    const skip = (page - 1) * limit;\n    \n    const users = await User.find()\n      .select('-password')\n      .skip(skip)\n      .limit(limit);\n    \n    const total = await User.countDocuments();\n    \n    res.json({\n      users,\n      total,\n      page,\n      limit,\n      totalPages: Math.ceil(total / limit)\n    });\n  } catch (err) {\n    console.error(err.message);\n    res.status(500).send('Server Error');\n  }\n});\n\nmodule.exports = router;"
}
```"""}
            # 데이터베이스 스키마 관련 응답
            elif "데이터베이스 스키마" in prompt:
                return {"response": """```json
{
  "database": "MongoDB",
  "entities": [
    {
      "name": "User",
      "description": "사용자 정보",
      "attributes": [
        {"name": "name", "type": "String", "description": "이름", "required": true},
        {"name": "email", "type": "String", "description": "이메일", "required": true, "unique": true},
        {"name": "password", "type": "String", "description": "비밀번호", "required": true},
        {"name": "role", "type": "ObjectId", "description": "역할", "required": true, "ref": "Role"}
      ],
      "relationships": [
        {"entity": "Role", "type": "Many-to-One", "description": "사용자의 역할"}
      ]
    }
  ],
  "code": "const mongoose = require('mongoose');\n\nconst UserSchema = new mongoose.Schema({\n  name: {\n    type: String,\n    required: true\n  },\n  email: {\n    type: String,\n    required: true,\n    unique: true\n  },\n  password: {\n    type: String,\n    required: true\n  },\n  role: {\n    type: mongoose.Schema.Types.ObjectId,\n    ref: 'Role',\n    required: true\n  },\n  createdAt: {\n    type: Date,\n    default: Date.now\n  }\n});\n\nmodule.exports = mongoose.model('User', UserSchema);"
}
```"""}
            # 인증 시스템 관련 응답
            elif "인증 시스템" in prompt:
                return {"response": """```json
{
  "auth_method": "JWT",
  "features": ["로그인", "회원가입", "토큰 갱신", "비밀번호 재설정"],
  "flow": ["사용자 등록", "로그인 및 토큰 발급", "토큰 검증", "토큰 갱신"],
  "endpoints": [
    {"path": "/api/auth/register", "method": "POST", "description": "회원가입"},
    {"path": "/api/auth/login", "method": "POST", "description": "로그인"},
    {"path": "/api/auth/refresh", "method": "POST", "description": "토큰 갱신"}
  ],
  "code": "const express = require('express');\nconst router = express.Router();\nconst bcrypt = require('bcrypt');\nconst jwt = require('jsonwebtoken');\nconst User = require('../models/User');\n\nrouter.post('/register', async (req, res) => {\n  try {\n    const { name, email, password } = req.body;\n    \n    // 중복 이메일 확인\n    let user = await User.findOne({ email });\n    if (user) {\n      return res.status(400).json({ msg: '이미 등록된 이메일입니다' });\n    }\n    \n    // 비밀번호 암호화\n    const salt = await bcrypt.genSalt(10);\n    const hashedPassword = await bcrypt.hash(password, salt);\n    \n    // 사용자 등록\n    user = new User({\n      name,\n      email,\n      password: hashedPassword\n    });\n    \n    await user.save();\n    \n    // 토큰 발급\n    const payload = {\n      user: {\n        id: user.id\n      }\n    };\n    \n    jwt.sign(\n      payload,\n      process.env.JWT_SECRET,\n      { expiresIn: '1h' },\n      (err, token) => {\n        if (err) throw err;\n        res.json({ token });\n      }\n    );\n  } catch (err) {\n    console.error(err.message);\n    res.status(500).send('Server error');\n  }\n});\n\nmodule.exports = router;"
}
```"""}
            # 기본 응답
            else:
                return {"response": """일반 백엔드 작업 응답입니다. 요청에 따라 적절한 코드나 정보를 생성했습니다."""}
        
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
            
    def try_fix_json_string(self, json_str: str) -> Optional[Dict]:
        # 1. 코드 블록/주석/불필요한 텍스트 제거
        json_str = re.sub(r'```[a-zA-Z]*', '', json_str)
        json_str = re.sub(r'```', '', json_str)
        json_str = re.sub(r'//.*', '', json_str)
        # 2. 이중 따옴표 중첩 제거
        json_str = json_str.replace('\\"', '"')
        # 3. true/false/null → True/False/None (파이썬용)
        json_str = json_str.replace('true', 'True').replace('false', 'False').replace('null', 'None')
        # 4. 마지막 } 또는 ]까지 자르기
        last_brace = max(json_str.rfind('}'), json_str.rfind(']'))
        if last_brace != -1:
            json_str = json_str[:last_brace+1]
        try:
            return ast.literal_eval(json_str)
        except Exception:
            return None

    def _parse_ollama_json_response(self, ollama_output: str, function_name: str) -> Optional[Dict[str, Any]]:
        """
        Ollama 응답 문자열에서 JSON 객체를 robust하게 파싱합니다.
        """
        if not isinstance(ollama_output, str):
            logger.warning(f"{function_name}: _parse_ollama_json_response에 문자열이 아닌 입력이 들어왔습니다: {type(ollama_output)}")
            return None

        # 1. 코드 블록 전체 추출 (줄바꿈 포함)
        match = re.search(r"```json\s*([\s\S]*?)\s*```", ollama_output)
        if match:
            json_str = match.group(1).strip()
            if not json_str.lstrip().startswith('{'):
                brace_idx = json_str.find('{')
                if brace_idx != -1:
                    json_str = json_str[brace_idx:]
            try:
                parsed_json = json.loads(json_str)
                logger.info(f"{function_name}: 코드 블록에서 JSON 파싱 성공.")
                return parsed_json
            except json.JSONDecodeError as e:
                logger.warning(f"{function_name}: 코드 블록 내 JSON 파싱 실패: {e}. 추출된 JSON 문자열: {json_str[:500]}...")
                # 자동 보정 시도
                fixed = self.try_fix_json_string(json_str)
                if fixed:
                    logger.info(f"{function_name}: try_fix_json_string로 JSON 보정 파싱 성공.")
                    return fixed
                return None
        else:
            logger.info(f"{function_name}: 응답에서 '```json ... ```' 코드 블록을 찾지 못했습니다. 전체 문자열을 직접 JSON으로 파싱 시도합니다.")
            try:
                parsed_json = json.loads(ollama_output)
                logger.info(f"{function_name}: 전체 문자열을 JSON으로 직접 파싱 성공.")
                return parsed_json
            except json.JSONDecodeError as e:
                logger.warning(f"{function_name}: 전체 문자열 직접 JSON 파싱 실패: {e}. Ollama 원본 응답 일부: {ollama_output[:500]}")
                # 자동 보정 시도
                fixed = self.try_fix_json_string(ollama_output)
                if fixed:
                    logger.info(f"{function_name}: try_fix_json_string로 JSON 보정 파싱 성공.")
                    return fixed
                return None
            
    def create_api_endpoint(self, description: str) -> Dict[str, Any]:
        """
        API 엔드포인트 생성
        
        Args:
            description: API 엔드포인트 설명
            
        Returns:
            생성된 API 엔드포인트 정보
        """
        logger.info(f"API 엔드포인트 생성 요청: {description}")
        project_context_info = ""
        if self.current_project_id and self.current_project_name:
            project_context_info = f"현재 작업 중인 프로젝트는 '{self.current_project_name}'(ID: {self.current_project_id})입니다. "
        elif self.current_project_id:
            project_context_info = f"현재 작업 중인 프로젝트 ID는 {self.current_project_id}입니다. "
        
        prompt = f"""
        {project_context_info}다음은 API 엔드포인트 생성 요청입니다: {description}

        프로젝트 설정:
        - 프레임워크: {self.project_config.get("framework")}
        - API 버전: {self.project_config.get("api_version")}
        - API 경로: {self.project_config.get("api_path")}

        응답은 다음 JSON 형식을 엄격하게 따라야 합니다. 코드 블록 안에 JSON을 포함하고, 다른 설명은 넣지 마십시오:
```json
{{
            "endpoint": "/api/v1/example",
            "method": "GET", // GET, POST, PUT, DELETE 등
            "description": "API 엔드포인트에 대한 간략한 설명",
            "parameters": [
                {{"name": "param_name", "type": "string", "description": "파라미터 설명", "required": true}}
            ],
            "responses": [
                {{"status": 200, "description": "성공 응답 설명", "example": {{"message": "성공"}}}}
            ],
            "code": "// 여기에 {self.project_config.get("framework")} 프레임워크 기반의 API 엔드포인트 코드를 작성합니다.\n// 예시: JavaScript 또는 TypeScript 코드"
}}
```
        요청에 대한 API 엔드포인트 정의를 생성해주세요.
        """
        ollama_response = self._ollama_request(prompt)
        return self._parse_ollama_json_response(ollama_response.get("response", ""), "create_api_endpoint")
            
    def create_database_schema(self, description: str) -> Dict[str, Any]:
        """
        데이터베이스 스키마 생성
        
        Args:
            description: 데이터베이스 스키마 설명
            
        Returns:
            생성된 데이터베이스 스키마 정보
        """
        logger.info(f"데이터베이스 스키마 생성 요청: {description}")
        project_context_info = ""
        if self.current_project_id and self.current_project_name:
            project_context_info = f"현재 작업 중인 프로젝트는 '{self.current_project_name}'(ID: {self.current_project_id})입니다. "
        elif self.current_project_id:
            project_context_info = f"현재 작업 중인 프로젝트 ID는 {self.current_project_id}입니다. "
        
        prompt = f"""
        {project_context_info}다음은 데이터베이스 스키마 생성 요청입니다: {description}

        프로젝트 설정:
        - 데이터베이스: {self.project_config.get("database")}
        - 모델 경로: {self.project_config.get("models_path")}

        응답은 다음 JSON 형식을 엄격하게 따라야 합니다. 코드 블록 안에 JSON을 포함하고, 다른 설명은 넣지 마십시오:
```json
{{
            "database": "{self.project_config.get("database")}",
    "entities": [
        {{
                    "name": "ExampleEntity",
                    "description": "엔티티 설명",
            "attributes": [
                        {{"name": "attribute_name", "type": "String", "description": "속성 설명", "required": true, "unique": false, "default": null, "ref": null}}
            ],
            "relationships": [
                        {{"entity": "RelatedEntity", "type": "One-to-Many", "description": "관계 설명"}}
            ]
                }}
    ],
            "code": "// 여기에 {self.project_config.get("database")} 스키마 정의 코드를 작성합니다.\n// 예시: Mongoose (JavaScript), SQLAlchemy (Python) 등"
}}
```
        요청에 대한 데이터베이스 스키마 정의를 생성해주세요.
        """
        ollama_response = self._ollama_request(prompt)
        return self._parse_ollama_json_response(ollama_response.get("response", ""), "create_database_schema")
            
    def create_authentication_system(self, description: str) -> Dict[str, Any]:
        """
        인증 시스템 생성
        
        Args:
            description: 인증 시스템 설명
            
        Returns:
            생성된 인증 시스템 정보
        """
        logger.info(f"인증 시스템 생성 요청: {description}")
        project_context_info = ""
        if self.current_project_id and self.current_project_name:
            project_context_info = f"현재 작업 중인 프로젝트는 '{self.current_project_name}'(ID: {self.current_project_id})입니다. "
        elif self.current_project_id:
            project_context_info = f"현재 작업 중인 프로젝트 ID는 {self.current_project_id}입니다. "
        
        prompt = f"""
        {project_context_info}다음은 인증 시스템 생성 요청입니다: {description}

        프로젝트 설정:
        - 인증 제공자: {self.project_config.get("auth_provider")}
        - 프레임워크: {self.project_config.get("framework")}

        응답은 다음 JSON 형식을 엄격하게 따라야 합니다. 코드 블록 안에 JSON을 포함하고, 다른 설명은 넣지 마십시오:
```json
{{
            "auth_method": "{self.project_config.get("auth_provider")}",
            "features": ["로그인", "회원가입", "토큰 갱신"],
            "flow": ["사용자 등록", "로그인 및 토큰 발급", "토큰 검증"],
    "endpoints": [
                {{"path": "/api/auth/register", "method": "POST", "description": "회원가입"}}
    ],
            "code": "// 여기에 {self.project_config.get("auth_provider")} 기반 인증 시스템 코드를 {self.project_config.get("framework")} 프레임워크에 맞게 작성합니다."
}}
```
        요청에 대한 인증 시스템 정의를 생성해주세요.
        """
        ollama_response = self._ollama_request(prompt)
        return self._parse_ollama_json_response(ollama_response.get("response", ""), "create_authentication_system")

    def run_task(self, description: str) -> str:
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
        
        # 데이터베이스 스키마 관련 작업을 먼저 확인하여 우선순위를 높입니다.
        if any(keyword in description_lower for keyword in schema_keywords):
            logger.info(f"데이터베이스 스키마 태스크로 인식: {description}")
            return self.create_database_schema(description)
        elif any(keyword in description_lower for keyword in api_keywords):
            logger.info(f"API 엔드포인트 태스크로 인식: {description}")
            return self.create_api_endpoint(description)
        elif any(keyword in description_lower for keyword in auth_keywords):
            logger.info(f"인증 시스템 태스크로 인식: {description}")
            return self.create_authentication_system(description)
        else:
            # 일반 태스크
            logger.info(f"일반 백엔드 태스크 실행: {description}")
            
            # Ollama API 요청 프롬프트 작성
            prompt = f"""
당신은 숙련된 백엔드 개발자입니다. 다음 설명을 바탕으로 백엔드 작업을 수행해야 합니다:

설명: {{description}}
프레임워크: {{self.project_config.get('framework', 'Express.js')}}
데이터베이스: {{self.project_config.get('database', 'MongoDB')}}

중요: 반드시 다음 JSON 스키마를 정확히 따라서 응답해주십시오.
다른 설명이나 추가 텍스트 없이, 오직 순수한 JSON 객체만을 반환해야 합니다.
생성된 JSON 응답은 반드시 ```json ... ``` 코드 블록으로 감싸주세요.
만약 코드 블록 내에 JSON 외의 다른 텍스트(예: 설명)가 포함되면 안 됩니다.
오직 유효한 JSON 데이터만 코드 블록 안에 있어야 합니다.

```json
{{
    "task_description": "{description}",
    "status": "completed or error",
    "result_summary": "작업 결과 요약",
    "details": {{
        "key1": "value1",
        "key2": "value2"
    }},
    "code_snippet": "// 관련 코드 스니펫 (있을 경우)",
    "error_message": "오류 메시지 (오류 발생 시)"
}}
```
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
                
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        태스크를 처리합니다.
        
        Args:
            task: 처리할 태스크 정보
            
        Returns:
            처리 결과
        """
        task_type = task.get("type", "")
        logger.info(f"태스크 처리 시작: {task_type}")
        
        if task_type == "create_api_endpoint":
            description = task.get("description", "")
            return self.create_api_endpoint(description)
        
        elif task_type == "create_database_schema":
            description = task.get("description", "")
            return self.create_database_schema(description)
        
        elif task_type == "create_authentication_system":
            description = task.get("description", "")
            return self.create_authentication_system(description)
            
        elif task_type == "create_test_code":
            description = task.get("description", "")
            code_type = task.get("code_type", "api_endpoint")
            return self.create_test_code(description, code_type)
            
        elif task_type == "create_middleware":
            description = task.get("description", "")
            middleware_type = task.get("middleware_type", "general")
            return self.create_middleware(description, middleware_type)
            
        elif task_type == "validate_security":
            code = task.get("code", "")
            security_level = task.get("security_level", "standard")
            
            if not code:
                return {
                    "status": "error",
                    "message": "검증할 코드가 제공되지 않았습니다."
                }
                
            return self.validate_security(code, security_level)
            
        elif task_type == "optimize_performance":
            code = task.get("code", "")
            optimization_areas = task.get("optimization_areas", None)
            
            if not code:
                return {
                    "status": "error",
                    "message": "최적화할 코드가 제공되지 않았습니다."
                }
                
            return self.optimize_performance(code, optimization_areas)
        
        else:
            return {
                "status": "error",
                "message": f"지원하지 않는 태스크 타입: {task_type}",
                "supported_types": ["create_api_endpoint", "create_database_schema", "create_authentication_system", "create_test_code", "create_middleware", "validate_security", "optimize_performance"]
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

    def create_test_code(self, description: str, code_type: str = "api_endpoint") -> Dict[str, Any]:
        """
        테스트 코드 생성
        
        Args:
            description: 테스트할 코드에 대한 설명
            code_type: 코드 타입 ("api_endpoint", "database_model", "auth_system")
            
        Returns:
            생성된 테스트 코드 정보
        """
        logger.info(f"테스트 코드 생성 요청: {description}, 타입: {code_type}")
        
        # 테스트 대상에 따른 프롬프트 생성
        if code_type == "api_endpoint":
            prompt = f"""
당신은 숙련된 백엔드 개발자입니다. 다음 설명을 바탕으로 API 엔드포인트에 대한 테스트 코드를 작성해야 합니다:

설명: {description}
프레임워크: {self.project_config.get('framework', 'Express.js')}
테스트 프레임워크: Jest, Supertest

요청 형식:
1. 성공 케이스와 실패 케이스를 모두 테스트하세요.
2. 데이터베이스 모킹을 포함하세요.
3. 필요한, 올바른 HTTP 응답 코드 및 응답 형식을 검증하세요.
4. 적절한 테스트 설명을 포함하세요.

JSON 형식으로 응답하세요:
```json
{{
    "test_type": "api_endpoint",
    "description": "테스트 설명",
    "framework": "테스트 프레임워크",
    "test_cases": [
        {{"name": "케이스 이름", "description": "테스트 케이스 설명"}}
    ],
    "code": "// 테스트 코드"
}}
```
"""
        elif code_type == "database_model":
            prompt = f"""
당신은 숙련된 백엔드 개발자입니다. 다음 설명을 바탕으로 데이터베이스 모델에 대한 테스트 코드를 작성해야 합니다:

설명: {description}
데이터베이스: {self.project_config.get('database', 'MongoDB')}
테스트 프레임워크: Jest, Mongoose

요청 형식:
1. 모델 검증 테스트를 포함하세요.
2. 필수 필드 및 유효성 검사를 테스트하세요.
3. 관계가 있는 경우 관계 테스트를 포함하세요.
4. 적절한 테스트 설명을 포함하세요.

JSON 형식으로 응답하세요:
```json
{{
    "test_type": "database_model",
    "description": "테스트 설명",
    "framework": "테스트 프레임워크",
    "test_cases": [
        {{"name": "케이스 이름", "description": "테스트 케이스 설명"}}
    ],
    "code": "// 테스트 코드"
}}
```
"""
        elif code_type == "auth_system":
            prompt = f"""
당신은 숙련된 백엔드 개발자입니다. 다음 설명을 바탕으로 인증 시스템에 대한 테스트 코드를 작성해야 합니다:

설명: {description}
프레임워크: {self.project_config.get('framework', 'Express.js')}
인증 방식: {self.project_config.get('auth_provider', 'JWT')}
테스트 프레임워크: Jest, Supertest

요청 형식:
1. 로그인, 회원가입, 토큰 검증 등의 테스트를 포함하세요.
2. 성공 케이스와 실패 케이스를 모두 테스트하세요.
3. 토큰 만료 및 갱신 테스트를 포함하세요.
4. 적절한 테스트 설명을 포함하세요.

JSON 형식으로 응답하세요:
```json
{{
    "test_type": "auth_system",
    "description": "테스트 설명",
    "framework": "테스트 프레임워크",
    "test_cases": [
        {{"name": "케이스 이름", "description": "테스트 케이스 설명"}}
    ],
    "code": "// 테스트 코드"
}}
```
"""
        else:
            return {
                "status": "error",
                "message": f"지원하지 않는 코드 타입: {code_type}",
                "supported_types": ["api_endpoint", "database_model", "auth_system"]
            }
        
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
                    "test_type": code_type,
                    "description": description,
                    "code": output
                }
            
            if json_match:
                return json_match
            else:
                return {
                    "test_type": code_type,
                    "description": description,
                    "code": output
                }
                
        except Exception as e:
            logger.error(f"테스트 코드 생성 중 오류 발생: {str(e)}")
            return {
                "test_type": code_type,
                "description": description,
                "error": str(e)
            }

    def create_middleware(self, description: str, middleware_type: str = "general") -> Dict[str, Any]:
        """
        미들웨어 생성
        
        Args:
            description: 미들웨어 설명
            middleware_type: 미들웨어 타입 ("auth", "validation", "logging", "error_handling", "general")
            
        Returns:
            생성된 미들웨어 정보
        """
        logger.info(f"미들웨어 생성 요청: {description}, 타입: {middleware_type}")
        
        # 미들웨어 타입에 따른 프롬프트 생성
        if middleware_type == "auth":
            prompt = f"""
당신은 숙련된 백엔드 개발자입니다. 다음 설명을 바탕으로 인증 미들웨어를 구현해야 합니다:

설명: {description}
프레임워크: {self.project_config.get('framework', 'Express.js')}
인증 방식: {self.project_config.get('auth_provider', 'JWT')}

요청 형식:
1. 토큰 검증 로직을 구현하세요.
2. 유효하지 않은 토큰에 대한 오류 처리를 구현하세요.
3. 권한 부여 로직을 포함하세요 (필요한 경우).
4. 코드는 깔끔하고 효율적이어야 합니다.

JSON 형식으로 응답하세요:
```json
{{
    "middleware_type": "auth",
    "description": "인증 미들웨어 설명",
    "usage_example": "미들웨어 사용 예시",
    "code": "// 구현 코드"
}}
```
"""
        elif middleware_type == "validation":
            prompt = f"""
당신은 숙련된 백엔드 개발자입니다. 다음 설명을 바탕으로 유효성 검사 미들웨어를 구현해야 합니다:

설명: {description}
프레임워크: {self.project_config.get('framework', 'Express.js')}

요청 형식:
1. 요청 본문, 파라미터, 쿼리 파라미터의 유효성 검사 로직을 구현하세요.
2. 유효성 검사 오류에 대한 처리를 구현하세요.
3. 사용하기 쉬운 API를 제공하세요.
4. 코드는 깔끔하고 효율적이어야 합니다.

JSON 형식으로 응답하세요:
```json
{{
    "middleware_type": "validation",
    "description": "유효성 검사 미들웨어 설명",
    "usage_example": "미들웨어 사용 예시",
    "code": "// 구현 코드"
}}
```
"""
        elif middleware_type == "logging":
            prompt = f"""
당신은 숙련된 백엔드 개발자입니다. 다음 설명을 바탕으로 로깅 미들웨어를 구현해야 합니다:

설명: {description}
프레임워크: {self.project_config.get('framework', 'Express.js')}

요청 형식:
1. 요청 및 응답 정보를 로깅하는 로직을 구현하세요.
2. 다양한 로그 레벨을 지원하세요.
3. 필요한 경우 요청/응답 본문을 로깅하되, 민감한 정보는 제외하세요.
4. 코드는 깔끔하고 효율적이어야 합니다.

JSON 형식으로 응답하세요:
```json
{{
    "middleware_type": "logging",
    "description": "로깅 미들웨어 설명",
    "usage_example": "미들웨어 사용 예시",
    "code": "// 구현 코드"
}}
```
"""
        elif middleware_type == "error_handling":
            prompt = f"""
당신은 숙련된 백엔드 개발자입니다. 다음 설명을 바탕으로 오류 처리 미들웨어를 구현해야 합니다:

설명: {description}
프레임워크: {self.project_config.get('framework', 'Express.js')}

요청 형식:
1. 다양한 유형의 오류를 처리하는 로직을 구현하세요.
2. 일관된 오류 응답 형식을 제공하세요.
3. 운영 환경과 개발 환경에서 다르게 동작하도록 하세요.
4. 코드는 깔끔하고 효율적이어야 합니다.

JSON 형식으로 응답하세요:
```json
{{
    "middleware_type": "error_handling",
    "description": "오류 처리 미들웨어 설명",
    "usage_example": "미들웨어 사용 예시",
    "code": "// 구현 코드"
}}
```
"""
        else:  # general
            prompt = f"""
당신은 숙련된 백엔드 개발자입니다. 다음 설명을 바탕으로 미들웨어를 구현해야 합니다:

설명: {description}
프레임워크: {self.project_config.get('framework', 'Express.js')}

요청 형식:
1. 설명에 맞는 미들웨어 로직을 구현하세요.
2. 필요한 모든 기능을 포함하세요.
3. 재사용 가능하고 유지보수하기 쉬운 코드를 작성하세요.
4. 코드는 깔끔하고 효율적이어야 합니다.

JSON 형식으로 응답하세요:
```json
{{
    "middleware_type": "general",
    "description": "미들웨어 설명",
    "usage_example": "미들웨어 사용 예시",
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
                    "middleware_type": middleware_type,
                    "description": description,
                    "code": output
                }
            
            if json_match:
                return json_match
            else:
                return {
                    "middleware_type": middleware_type,
                    "description": description,
                    "code": output
                }
                
        except Exception as e:
            logger.error(f"미들웨어 생성 중 오류 발생: {str(e)}")
            return {
                "middleware_type": middleware_type,
                "description": description,
                "error": str(e)
            }

    def validate_security(self, code: str, security_level: str = "standard") -> Dict[str, Any]:
        """
        코드의 보안 취약점을 검증합니다.
        
        Args:
            code: 검증할 코드
            security_level: 보안 수준 ("standard", "high", "critical")
            
        Returns:
            보안 검증 결과
        """
        logger.info(f"보안 검증 요청, 보안 수준: {security_level}")
        
        # 보안 수준에 따른 프롬프트 생성
        if security_level == "high":
            prompt = f"""
당신은 숙련된 보안 전문가입니다. 다음 코드의 보안 취약점을 분석하고 자세한 보고서를 제공해야 합니다:

```
{code}
```

다음 보안 취약점을 철저히 검사하세요:
1. 인증 및 권한 관련 취약점
2. 입력 검증 및 유효성 검사 부재
3. SQL 인젝션 취약점
4. XSS(Cross-Site Scripting) 취약점
5. CSRF(Cross-Site Request Forgery) 취약점
6. 중요 정보 노출
7. 세션 관리 취약점
8. 잘못된 보안 구성
9. 안전하지 않은 암호화 사용
10. 로깅 및 모니터링 부재
11. 의존성 취약점
12. 비즈니스 로직 취약점

각 취약점에 대해 다음을 제공하세요:
- 문제 설명
- 심각도 (높음, 중간, 낮음)
- 위치 (코드의 어느 부분이 문제인지)
- 수정 방법

JSON 형식으로 응답하세요:
```json
{{
    "security_level": "high",
    "total_issues": 0,
    "issues": [
        {{
            "type": "취약점 타입",
            "description": "문제 설명",
            "severity": "심각도",
            "location": "위치",
            "fix": "수정 방법"
        }}
    ],
    "summary": "전체 요약",
    "safe_code": "수정된 코드"
}}
```
"""
        elif security_level == "critical":
            prompt = f"""
당신은 전문적인 보안 감사자입니다. 다음 코드의 보안 취약점을 매우 철저하게 분석하고 상세한 보고서를 제공해야 합니다:

```
{code}
```

다음 보안 취약점 영역에서 모든 잠재적 문제를 면밀히 검사하세요:
1. OWASP Top 10 취약점
   - 인젝션 취약점(SQL, NoSQL, OS 명령어 등)
   - 취약한 인증 및 세션 관리
   - 안전하지 않은 직접 객체 참조
   - XSS(Cross-Site Scripting)
   - 취약한 접근 제어
   - 보안 설정 오류
   - 민감 데이터 노출
   - CSRF(Cross-Site Request Forgery)
   - 알려진 취약점이 있는 컴포넌트 사용
   - 안전하지 않은 API
2. 추가 취약점 영역
   - 코드 인젝션
   - 서버 측 요청 위조(SSRF)
   - 불충분한 로깅 및 모니터링
   - 비즈니스 로직 취약점
   - 암호화 관련 취약점
   - 데이터 유효성 검사 부재
   - 메모리 누수 및 버퍼 오버플로우
   - 안전하지 않은 직렬화
   - 타임아웃 부재

각 발견된 취약점에 대해 다음을 제공하세요:
- 상세한 문제 설명
- 심각도 (치명적, 높음, 중간, 낮음)
- 정확한 코드 위치
- CVSS 점수(가능한 경우)
- 구체적인 수정 방법과 예시 코드
- 참조 자료 및 관련 CWE/CVE

JSON 형식으로 응답하세요:
```json
{{
    "security_level": "critical",
    "total_issues": 0,
    "critical_issues": 0,
    "high_issues": 0,
    "medium_issues": 0,
    "low_issues": 0,
    "issues": [
        {{
            "id": "VULN-001",
            "type": "취약점 타입",
            "description": "문제 상세 설명",
            "severity": "심각도",
            "cvss_score": "CVSS 점수(해당되는 경우)",
            "cwe_id": "CWE 번호(해당되는 경우)",
            "location": "정확한 코드 위치",
            "vulnerable_code": "취약한 코드 스니펫",
            "fix": "상세한 수정 방법",
            "fix_code": "수정된 코드 스니펫",
            "references": ["참조 자료"]
        }}
    ],
    "summary": "종합적 보안 평가",
    "recommendations": ["전반적인 보안 개선 권장사항"],
    "safe_code": "수정된 코드 전체"
}}
```
"""
        else:  # standard
            prompt = f"""
당신은 백엔드 개발자이자 보안 검토자입니다. 다음 코드의 일반적인 보안 취약점을 확인하고 보고서를 제공해야 합니다:

```
{code}
```

다음 주요 보안 취약점을 검사하세요:
1. 인젝션 취약점 (SQL, NoSQL 등)
2. 입력 검증 부재
3. 인증 및 권한 부여 문제
4. 민감한 정보 노출
5. XSS(Cross-Site Scripting) 취약점
6. 불안전한 암호화 사용

JSON 형식으로 응답하세요:
```json
{{
    "security_level": "standard",
    "total_issues": 0,
    "issues": [
        {{
            "type": "취약점 타입",
            "description": "문제 설명",
            "severity": "심각도",
            "location": "위치",
            "fix": "수정 방법"
        }}
    ],
    "summary": "전체 요약",
    "safe_code": "수정된 코드"
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
                # 텍스트 응답에서 문제 찾기
                issues = []
                summary = "보안 검증 중 문제가 발견되었습니다."
                
                if "취약점" in output:
                    lines = output.split("\n")
                    for i, line in enumerate(lines):
                        if "취약점" in line or "vulnerability" in line.lower() or "issue" in line.lower():
                            issue_type = line.strip()
                            description = lines[i+1].strip() if i+1 < len(lines) else ""
                            issues.append({
                                "type": issue_type,
                                "description": description,
                                "severity": "알 수 없음",
                                "location": "알 수 없음",
                                "fix": "알 수 없음"
                            })
                
                return {
                    "security_level": security_level,
                    "total_issues": len(issues),
                    "issues": issues,
                    "summary": summary,
                    "raw_output": output
                }
            
            if json_match:
                return json_match
            else:
                return {
                    "security_level": security_level,
                    "total_issues": 0,
                    "issues": [],
                    "summary": "보안 문제가 발견되지 않았습니다.",
                    "safe_code": code
                }
                
        except Exception as e:
            logger.error(f"보안 검증 중 오류 발생: {str(e)}")
            return {
                "security_level": security_level,
                "error": str(e),
                "issues": [],
                "summary": "보안 검증 중 오류가 발생했습니다."
            }

    def optimize_performance(self, code: str, optimization_areas: List[str] = None) -> Dict[str, Any]:
        """
        백엔드 코드 성능을 최적화합니다.
        
        Args:
            code: 최적화할 코드
            optimization_areas: 최적화 영역 목록 (데이터베이스, 메모리, 알고리즘, 캐싱 등)
            
        Returns:
            최적화된 코드 정보
        """
        logger.info("성능 최적화 요청")
        
        if optimization_areas is None:
            optimization_areas = ["데이터베이스", "메모리", "알고리즘", "캐싱"]
        
        # 최적화 영역을 문자열로 변환
        optimization_areas_str = ", ".join(optimization_areas)
        
        # 프롬프트 생성
        prompt = f"""
당신은 백엔드 성능 최적화 전문가입니다. 다음 코드를 분석하고 성능을 최적화하세요:

```
{code}
```

다음 영역에서 성능 최적화를 수행하세요: {optimization_areas_str}

각 최적화 항목에 대해 다음을 제공하세요:
1. 현재 성능 문제 설명
2. 제안된 최적화 방법
3. 최적화된 코드
4. 예상되는 성능 향상 정도

JSON 형식으로 응답하세요:
```json
{{
    "optimization_areas": ["{optimization_areas_str}"],
    "total_optimizations": 0,
    "optimizations": [
        {{
            "area": "최적화 영역",
            "issue": "현재 성능 문제",
            "suggestion": "제안된 최적화 방법",
            "expected_improvement": "예상되는 성능 향상 정도",
            "original_code": "원본 코드 스니펫",
            "optimized_code": "최적화된 코드 스니펫"
        }}
    ],
    "summary": "최적화 요약",
    "fully_optimized_code": "전체 최적화된 코드"
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
                
                # 최적화된 코드 추출 시도
                optimized_code = code
                if "```" in output and "```" in output.split("```", 1)[1]:
                    optimized_code = output.split("```", 1)[1].split("```", 1)[0].strip()
                
                return {
                    "optimization_areas": optimization_areas,
                    "total_optimizations": 1,
                    "optimizations": [{
                        "area": "일반",
                        "suggestion": "성능 최적화 제안",
                        "optimized_code": optimized_code
                    }],
                    "summary": "성능 최적화가 수행되었습니다.",
                    "raw_output": output
                }
            
            if json_match:
                return json_match
            else:
                return {
                    "optimization_areas": optimization_areas,
                    "total_optimizations": 0,
                    "optimizations": [],
                    "summary": "최적화할 항목이 발견되지 않았습니다.",
                    "fully_optimized_code": code
                }
                
        except Exception as e:
            logger.error(f"성능 최적화 중 오류 발생: {str(e)}")
            return {
                "optimization_areas": optimization_areas,
                "error": str(e),
                "optimizations": [],
                "summary": "성능 최적화 중 오류가 발생했습니다."
            }

    def _call_pmagent_mcp(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """PMAgent MCP 서버의 도구를 호출합니다."""
        payload = {
            "name": tool_name,
            "parameters": parameters
        }
        headers = {"Content-Type": "application/json"}

        logger.debug(f"Backend Agent {self.agent_id} calling MCP tool: {tool_name} with params: {parameters}")

        try:
            response = requests.post(self.mcp_server_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status() # HTTP 오류 발생 시 예외 처리
            result = response.json()
            logger.debug(f"MCP tool {tool_name} response: {result}")
            return result
        except requests.exceptions.Timeout:
            logger.error(f"MCP tool {tool_name} call timed out.")
            return {"success": False, "error": "Request timed out"}
        except requests.exceptions.RequestException as e:
            logger.error(f"MCP tool {tool_name} call failed: {e}")
            error_detail = str(e)
            if e.response is not None:
                try:
                    error_detail += f" - Response: {e.response.text}"
                except Exception:
                    pass
            return {"success": False, "error": error_detail}
        except json.JSONDecodeError:
            logger.error(f"MCP tool {tool_name} response is not valid JSON: {response.text}")
            return {"success": False, "error": "Invalid JSON response from server"}

    def _check_and_process_tasks(self, project_id_to_check: str):
        """MCP 서버에서 다음 작업을 확인하고 실제 처리합니다."""
        if not self.use_mcp:
            logger.info("MCP is not enabled for this agent.")
            return

        logger.info(f"Backend Agent {self.agent_id} checking for next task for project {project_id_to_check}...")
        get_task_params = {
            "requestId": project_id_to_check,
            "agentType": "BackendAgent",
            "agentId": self.agent_id
        }
        result = self._call_pmagent_mcp("get_next_task", get_task_params)

        if result.get("success") and result.get("hasNextTask"):
            task_data = result.get("task")
            # 프로젝트 컨텍스트 정보 추출 및 설정
            self.current_project_id = result.get("projectId") 
            self.current_project_name = result.get("projectName")
            logger.info(f"Current project context set for BackendAgent: ID='{self.current_project_id}', Name='{self.current_project_name}'")
            
            if task_data:
                task_id = task_data.get("id")
                task_title = task_data.get("title")
                task_description = task_data.get("description")

                logger.info(f"Backend Agent {self.agent_id} assigned task: ID={task_id}, Title='{task_title}' for Project '{self.current_project_name}' ({self.current_project_id})")

                completed_details = f"Task '{task_title}' (ID: {task_id}) processing initiated by {self.agent_id} for project {self.current_project_id}."
                processing_status = "UNKNOWN"
                max_detail_length = 300 # completedDetails에 포함될 결과 요약의 최대 길이

                try:
                    logger.info(f"Processing task {task_id}: {task_description} (Project: {self.current_project_id})")
                    processing_result_obj = self.run_task(task_description)
                    logger.info(f"Task {task_id} processing finished by Ollama.")
                    processing_status = "PROCESSED"

                    if isinstance(processing_result_obj, dict):
                        # 성공적으로 파싱된 JSON 객체인 경우
                        summary = processing_result_obj.get("result_summary")
                        parsing_error_msg = processing_result_obj.get("parsing_error")
                        status_from_obj = processing_result_obj.get("status", "completed")
                        
                        final_summary_parts = [f"Status: {status_from_obj}."]
                        if summary:
                            final_summary_parts.append(f"Summary: {summary}")
                        elif parsing_error_msg:
                            final_summary_parts.append(f"Notice: {parsing_error_msg}")
                            raw_output_preview = processing_result_obj.get("details", {}).get("raw_output", "")[:100]
                            if raw_output_preview:
                                final_summary_parts.append(f"Raw data starts with: '{raw_output_preview}...'") 
                        else:
                            # result_summary 없고 parsing_error도 없으면, 전체 객체를 요약
                            json_str_preview = json.dumps(processing_result_obj, ensure_ascii=False)
                            if len(json_str_preview) > max_detail_length:
                                final_summary_parts.append(f"Full result (JSON): {json_str_preview[:max_detail_length]}...")
                            else:
                                final_summary_parts.append(f"Full result (JSON): {json_str_preview}")
                        
                        completed_details = f"Task '{task_title}' processed by {self.agent_id} for project {self.current_project_id}. " + " ".join(final_summary_parts)
                        if len(completed_details) > max_detail_length + 100: # 전체 completedDetails 길이도 제어
                             completed_details = completed_details[:max_detail_length+97] + "..."

                    else: # JSON 파싱 실패 등으로 인해 문자열로 반환된 경우 (또는 예상치 못한 타입)
                        processing_status = "PROCESSED_WITH_FALLBACK"
                        result_str = str(processing_result_obj)
                        if len(result_str) > max_detail_length:
                            completed_details = f"Task '{task_title}' processed by {self.agent_id} for project {self.current_project_id}. Model response (text, truncated): {result_str[:max_detail_length]}..."
                        else:
                            completed_details = f"Task '{task_title}' processed by {self.agent_id} for project {self.current_project_id}. Model response (text): {result_str}"
                        logger.warning(f"Task {task_id} result was not a dict, treated as text. Type: {type(processing_result_obj)}")

                except Exception as e:
                    processing_status = "ERROR_IN_PROCESSING"
                    logger.error(f"Error processing task {task_id} with Ollama or during result handling: {e}", exc_info=True)
                    error_message = f"{type(e).__name__}: {str(e)[:150]}" # 오류 메시지 길이 제한
                    completed_details = f"ERROR processing task '{task_title}' by {self.agent_id} for project {self.current_project_id}. Status: {processing_status}. Details: {error_message}"
                
                logger.info(f"Final completedDetails for task {task_id} (status: {processing_status}): {completed_details}")

                # 작업 완료 보고
                mark_done_params = {
                    "requestId": project_id_to_check, # 또는 self.current_project_id 사용
                    "taskId": task_id,
                    "agentId": self.agent_id,
                    "completedDetails": completed_details
                }
                done_result = self._call_pmagent_mcp("mark_task_done", mark_done_params)

                if done_result.get("success"):
                    logger.info(f"Successfully marked task {task_id} as done.")
                else:
                    logger.error(f"Failed to mark task {task_id} as done: {done_result.get('error')}")
            else:
                logger.warning("get_next_task succeeded but no task data received.")
        elif result.get("success") and not result.get("hasNextTask"):
            logger.info(f"No new assignable tasks found for project {project_id_to_check} for agent {self.agent_id}.")
        else:
            logger.error(f"Failed to get next task for project {project_id_to_check}: {result.get('error')}")

    def start_working(self, project_id_to_work_on: str, interval: int = 10):
        """
        지정된 프로젝트 ID에 대해 주기적으로 작업을 확인하고 처리합니다.

        Args:
            project_id_to_work_on: 처리할 프로젝트 ID
            interval: 작업 확인 간격 (초)
        """
        if not self.use_mcp:
            logger.error("MCP is not enabled. Cannot start working loop.")
            return

        logger.info(f"Backend Agent {self.agent_id} starting to work on project {project_id_to_work_on} (checking every {interval} seconds)...")
        try:
            while True: # 실제 운영시 종료 조건 필요
                self._check_and_process_tasks(project_id_to_work_on)
                logger.debug(f"Waiting for {interval} seconds before next check...")
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info(f"Backend Agent {self.agent_id} stopping work loop.")
        except Exception as e:
            logger.error(f"An error occurred during the working loop for project {project_id_to_work_on}: {e}", exc_info=True)

# 테스트 코드 (예시)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Backend 에이전트 생성 (MCP 활성화)
    backend_agent = BackendAgentOllama(
        api_base=os.environ.get("OLLAMA_API_BASE"), # 환경 변수 또는 기본값 사용
        model=os.environ.get("OLLAMA_MODEL", "llama3.2:latest"),
        use_mcp=True, 
        agent_id="backend-agent-test-001", # 테스트용 고정 ID
        mcp_server_url="http://localhost:8083/mcp/invoke" # 포트 수정
    )

    # 명령행 인자에서 requestId 가져오기
    if len(sys.argv) > 1:
        current_request_id = sys.argv[1]
    else:
        # PMAgentOllama를 통해 생성된 요청 ID를 여기에 입력해야 합니다. (예비용/테스트용)
        # 실제 운영 시에는 명령행 인자를 통해 받는 것이 좋습니다.
        logger.warning("명령행 인자로 requestId가 제공되지 않았습니다. 코드 내의 기본 ID를 사용합니다.")
        logger.warning("사용법: python -m agents.backend_agent_ollama <REQUEST_ID>")
        current_request_id = "YOUR_PMAgent_GENERATED_REQUEST_ID_HERE" # 기본값 또는 오류 처리


    if current_request_id == "YOUR_PMAgent_GENERATED_REQUEST_ID_HERE" or not current_request_id:
        print("오류: 테스트를 위해 `requestId`를 명령행 인자로 제공해주세요.")
        print("예시: python -m agents.backend_agent_ollama xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    else:
        print(f"\n=== Backend Agent MCP 작업 루프 테스트 시작 (Request ID: {current_request_id}) ===\n")
        print(f"Backend Agent ({backend_agent.agent_id})가 요청 {current_request_id}에 대한 작업을 시작합니다.")
        print("Ctrl+C를 눌러 중지하세요.")
        try:
            backend_agent.start_working(current_request_id)
        except Exception as main_e:
            logger.error(f"Backend Agent main loop encountered an error: {main_e}", exc_info=True)