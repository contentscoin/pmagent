#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
백엔드 에이전트 테스트
"""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# 테스트 환경 설정
os.environ['PYTEST_CURRENT_TEST'] = 'test_backend_agent_ollama.py'

# 경로 설정 - 프로젝트 루트 디렉토리 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.backend_agent_ollama import BackendAgentOllama

# 테스트 데이터 - API 엔드포인트 설명 예시
API_ENDPOINT_DESCRIPTION = """
사용자 목록을 가져오는 API 엔드포인트를 만들어주세요.
- HTTP 메서드: GET
- 경로: /api/users
- 페이지네이션 지원 (page, limit 쿼리 파라미터)
- 응답에는 사용자 목록과 총 사용자 수 포함
"""

# 테스트 데이터 - 데이터베이스 스키마 설명 예시
DB_SCHEMA_DESCRIPTION = """
사용자 관리 시스템을 위한 데이터베이스 스키마를 설계해주세요.
필요한 테이블:
1. 사용자(User): id, 이름, 이메일, 비밀번호, 역할, 생성일
2. 프로필(Profile): 사용자 ID, 프로필 이미지, 소개, 전화번호, 주소
3. 역할(Role): id, 이름, 권한 목록
"""

# 테스트 데이터 - 인증 시스템 설명 예시
AUTH_SYSTEM_DESCRIPTION = """
JWT 기반 인증 시스템을 구현해주세요.
요구사항:
- 회원가입 (이메일, 비밀번호, 이름)
- 로그인
- 토큰 재발급
- 비밀번호 재설정
- 역할 기반 접근 제어 (RBAC)
"""

# 테스트에 사용할 모의 응답
MOCK_API_ENDPOINT_RESPONSE = """
{
  "endpoint": {
    "path": "/api/users",
    "method": "GET",
    "description": "사용자 목록을 조회하는 API",
    "query_parameters": [
      {
        "name": "page",
        "type": "number",
        "description": "페이지 번호 (1부터 시작)",
        "required": false,
        "default": 1
      },
      {
        "name": "limit",
        "type": "number",
        "description": "페이지당 항목 수",
        "required": false,
        "default": 10
      }
    ],
    "response": {
      "users": "User[]",
      "total": "number",
      "page": "number",
      "limit": "number",
      "totalPages": "number"
    }
  },
  "code": "const express = require('express');\nconst router = express.Router();\nconst User = require('../models/User');\n\n/**\n * @route   GET /api/users\n * @desc    사용자 목록 조회\n * @access  Private (Admin)\n */\nrouter.get('/', async (req, res) => {\n  try {\n    const page = parseInt(req.query.page, 10) || 1;\n    const limit = parseInt(req.query.limit, 10) || 10;\n    const skip = (page - 1) * limit;\n    \n    const users = await User.find()\n      .select('-password')\n      .skip(skip)\n      .limit(limit);\n    \n    const total = await User.countDocuments();\n    \n    res.json({\n      users,\n      total,\n      page,\n      limit,\n      totalPages: Math.ceil(total / limit)\n    });\n  } catch (err) {\n    console.error(err.message);\n    res.status(500).send('Server Error');\n  }\n});\n\nmodule.exports = router;"
}
"""

MOCK_DB_SCHEMA_RESPONSE = """
{
  "schema": {
    "name": "User Management System",
    "database_type": "MongoDB",
    "models": [
      {
        "name": "User",
        "fields": [
          {
            "name": "id",
            "type": "ObjectId",
            "primary": true,
            "auto": true
          },
          {
            "name": "name",
            "type": "String",
            "required": true
          },
          {
            "name": "email",
            "type": "String",
            "required": true,
            "unique": true
          },
          {
            "name": "password",
            "type": "String",
            "required": true
          },
          {
            "name": "role",
            "type": "ObjectId",
            "ref": "Role",
            "required": true
          },
          {
            "name": "createdAt",
            "type": "Date",
            "default": "Date.now"
          }
        ]
      },
      {
        "name": "Profile",
        "fields": [
          {
            "name": "user",
            "type": "ObjectId",
            "ref": "User",
            "required": true
          },
          {
            "name": "profileImage",
            "type": "String"
          },
          {
            "name": "bio",
            "type": "String"
          },
          {
            "name": "phone",
            "type": "String"
          },
          {
            "name": "address",
            "type": "String"
          }
        ]
      },
      {
        "name": "Role",
        "fields": [
          {
            "name": "id",
            "type": "ObjectId",
            "primary": true,
            "auto": true
          },
          {
            "name": "name",
            "type": "String",
            "required": true,
            "unique": true
          },
          {
            "name": "permissions",
            "type": "Array",
            "required": true
          }
        ]
      }
    ]
  },
  "code": "const mongoose = require('mongoose');\n\n// 사용자 스키마\nconst UserSchema = new mongoose.Schema({\n  name: {\n    type: String,\n    required: true\n  },\n  email: {\n    type: String,\n    required: true,\n    unique: true\n  },\n  password: {\n    type: String,\n    required: true\n  },\n  role: {\n    type: mongoose.Schema.Types.ObjectId,\n    ref: 'Role',\n    required: true\n  },\n  createdAt: {\n    type: Date,\n    default: Date.now\n  }\n});\n\n// 프로필 스키마\nconst ProfileSchema = new mongoose.Schema({\n  user: {\n    type: mongoose.Schema.Types.ObjectId,\n    ref: 'User',\n    required: true\n  },\n  profileImage: {\n    type: String\n  },\n  bio: {\n    type: String\n  },\n  phone: {\n    type: String\n  },\n  address: {\n    type: String\n  }\n});\n\n// 역할 스키마\nconst RoleSchema = new mongoose.Schema({\n  name: {\n    type: String,\n    required: true,\n    unique: true\n  },\n  permissions: {\n    type: [String],\n    required: true\n  }\n});\n\nconst User = mongoose.model('User', UserSchema);\nconst Profile = mongoose.model('Profile', ProfileSchema);\nconst Role = mongoose.model('Role', RoleSchema);\n\nmodule.exports = { User, Profile, Role };"
}
"""

MOCK_AUTH_SYSTEM_RESPONSE = """
{
  "auth_system": {
    "name": "JWT Authentication System",
    "components": [
      {
        "name": "Auth Controller",
        "endpoints": [
          {
            "path": "/api/auth/register",
            "method": "POST",
            "description": "회원가입"
          },
          {
            "path": "/api/auth/login",
            "method": "POST",
            "description": "로그인"
          },
          {
            "path": "/api/auth/refresh",
            "method": "POST",
            "description": "토큰 재발급"
          },
          {
            "path": "/api/auth/forgot-password",
            "method": "POST",
            "description": "비밀번호 찾기"
          },
          {
            "path": "/api/auth/reset-password",
            "method": "POST",
            "description": "비밀번호 재설정"
          }
        ]
      },
      {
        "name": "Middleware",
        "items": [
          {
            "name": "auth.js",
            "description": "JWT 인증 미들웨어"
          },
          {
            "name": "roles.js",
            "description": "역할 기반 접근 제어 미들웨어"
          }
        ]
      }
    ]
  },
  "code": "const express = require('express');\nconst router = express.Router();\nconst bcrypt = require('bcrypt');\nconst jwt = require('jsonwebtoken');\nconst User = require('../models/User');\nconst { check, validationResult } = require('express-validator');\nconst auth = require('../middleware/auth');\n\n// 환경 변수\nconst JWT_SECRET = process.env.JWT_SECRET || 'your_jwt_secret';\nconst JWT_EXPIRE = process.env.JWT_EXPIRE || '1h';\nconst REFRESH_TOKEN_EXPIRE = process.env.REFRESH_TOKEN_EXPIRE || '7d';\n\n/**\n * @route   POST /api/auth/register\n * @desc    사용자 등록\n * @access  Public\n */\nrouter.post('/register', [\n  check('name', '이름을 입력해주세요').not().isEmpty(),\n  check('email', '유효한 이메일을 입력해주세요').isEmail(),\n  check('password', '6자 이상의 비밀번호를 입력해주세요').isLength({ min: 6 })\n], async (req, res) => {\n  // 유효성 검사\n  const errors = validationResult(req);\n  if (!errors.isEmpty()) {\n    return res.status(400).json({ errors: errors.array() });\n  }\n\n  const { name, email, password } = req.body;\n\n  try {\n    // 이메일 중복 확인\n    let user = await User.findOne({ email });\n    if (user) {\n      return res.status(400).json({ msg: '이미 등록된 이메일입니다' });\n    }\n\n    // 기본 역할 조회\n    const defaultRole = await Role.findOne({ name: 'user' });\n    if (!defaultRole) {\n      return res.status(500).json({ msg: '기본 역할이 설정되지 않았습니다' });\n    }\n\n    // 사용자 객체 생성\n    user = new User({\n      name,\n      email,\n      password,\n      role: defaultRole._id\n    });\n\n    // 비밀번호 암호화\n    const salt = await bcrypt.genSalt(10);\n    user.password = await bcrypt.hash(password, salt);\n\n    // 사용자 저장\n    await user.save();\n\n    // JWT 토큰 생성\n    const payload = {\n      user: {\n        id: user.id,\n        role: defaultRole.name\n      }\n    };\n\n    jwt.sign(\n      payload,\n      JWT_SECRET,\n      { expiresIn: JWT_EXPIRE },\n      (err, token) => {\n        if (err) throw err;\n        res.json({ token });\n      }\n    );\n  } catch (err) {\n    console.error(err.message);\n    res.status(500).send('Server error');\n  }\n});\n\n/**\n * @route   POST /api/auth/login\n * @desc    사용자 로그인 및 토큰 발급\n * @access  Public\n */\nrouter.post('/login', [\n  check('email', '유효한 이메일을 입력해주세요').isEmail(),\n  check('password', '비밀번호를 입력해주세요').exists()\n], async (req, res) => {\n  // 생략...\n});\n\n/**\n * @route   POST /api/auth/refresh\n * @desc    액세스 토큰 재발급\n * @access  Public (리프레시 토큰 필요)\n */\nrouter.post('/refresh', async (req, res) => {\n  // 생략...\n});\n\n/**\n * @route   POST /api/auth/forgot-password\n * @desc    비밀번호 재설정 이메일 발송\n * @access  Public\n */\nrouter.post('/forgot-password', [\n  check('email', '유효한 이메일을 입력해주세요').isEmail(),\n], async (req, res) => {\n  // 생략...\n});\n\n/**\n * @route   POST /api/auth/reset-password\n * @desc    비밀번호 재설정\n * @access  Public (토큰 필요)\n */\nrouter.post('/reset-password', [\n  check('token', '토큰이 필요합니다').not().isEmpty(),\n  check('password', '6자 이상의 비밀번호를 입력해주세요').isLength({ min: 6 })\n], async (req, res) => {\n  // 생략...\n});\n\nmodule.exports = router;"
}
"""

@pytest.mark.asyncio
def test_backend_agent_init():
    """백엔드 에이전트 초기화 테스트"""
    agent = BackendAgentOllama(api_base="http://localhost:11434/api", model="llama3")
    assert agent.model == "llama3"
    assert agent.api_base == "http://localhost:11434/api"
    assert agent.project_config["framework"] == "Express.js"
    assert agent.project_config["database"] == "MongoDB"
    return agent

def run_api_endpoint_test():
    """API 엔드포인트 생성 테스트를 별도로 실행합니다."""
    # mock 객체 설정
    with patch('agents.backend_agent_ollama.requests.get') as mock_get:
        with patch('agents.backend_agent_ollama.requests.post') as mock_post:
            # requests.get 모의 객체 설정 (모델 확인용)
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get_response.json.return_value = {
                "models": [{"name": "llama3"}]
            }
            mock_get.return_value = mock_get_response
            
            # requests.post 모의 객체 설정 (Ollama API용)
            mock_post_response = MagicMock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "response": """```json
{
  "endpoint": "/api/v1/users",
  "method": "GET",
  "description": "사용자 목록 조회 API",
  "parameters": [{"name": "page", "type": "number", "description": "페이지 번호", "required": false}],
  "responses": [{"status": 200, "description": "성공", "example": {"users": [], "total": 0}}],
  "code": "// API 엔드포인트 코드"
}
```"""
            }
            mock_post.return_value = mock_post_response
            
            # 백엔드 에이전트 인스턴스 생성
            agent = BackendAgentOllama(api_base="http://localhost:11434/api", model="llama3")
            
            # API 엔드포인트 생성 테스트
            description = "사용자 목록을 페이지네이션과 함께 조회하는 API 엔드포인트를 생성하세요."
            result = agent.create_api_endpoint(description)
            
            assert "endpoint" in result
            assert "method" in result
            assert "description" in result
            assert "code" in result
            assert result["endpoint"] == "/api/v1/users"
            assert result["method"] == "GET"

def run_database_schema_test():
    """데이터베이스 스키마 생성 테스트를 별도로 실행합니다."""
    # mock 객체 설정
    with patch('agents.backend_agent_ollama.requests.get') as mock_get:
        with patch('agents.backend_agent_ollama.requests.post') as mock_post:
            # requests.get 모의 객체 설정 (모델 확인용)
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get_response.json.return_value = {
                "models": [{"name": "llama3"}]
            }
            mock_get.return_value = mock_get_response
            
            # requests.post 모의 객체 설정 (Ollama API용)
            mock_post_response = MagicMock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "response": """```json
{
  "database": "MongoDB",
  "entities": [
    {
      "name": "User",
      "description": "사용자 정보",
      "attributes": [
        {"name": "name", "type": "String", "description": "이름", "required": true},
        {"name": "email", "type": "String", "description": "이메일", "required": true, "unique": true}
      ]
    }
  ],
  "code": "// MongoDB 스키마 코드"
}
```"""
            }
            mock_post.return_value = mock_post_response
            
            # 백엔드 에이전트 인스턴스 생성
            agent = BackendAgentOllama(api_base="http://localhost:11434/api", model="llama3")
            
            # 데이터베이스 스키마 생성 테스트
            description = "사용자 정보를 저장하는 MongoDB 스키마를 생성하세요. 이름, 이메일 등 기본 정보를 포함해야 합니다."
            result = agent.create_database_schema(description)
            
            assert "database" in result
            assert "entities" in result
            assert "code" in result
            assert result["database"] == "MongoDB"
            assert len(result["entities"]) > 0
            assert result["entities"][0]["name"] == "User"

def run_authentication_system_test():
    """인증 시스템 생성 테스트를 별도로 실행합니다."""
    # mock 객체 설정
    with patch('agents.backend_agent_ollama.requests.get') as mock_get:
        with patch('agents.backend_agent_ollama.requests.post') as mock_post:
            # requests.get 모의 객체 설정 (모델 확인용)
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get_response.json.return_value = {
                "models": [{"name": "llama3"}]
            }
            mock_get.return_value = mock_get_response
            
            # requests.post 모의 객체 설정 (Ollama API용)
            mock_post_response = MagicMock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "response": """```json
{
  "auth_method": "JWT",
  "features": ["로그인", "회원가입", "토큰 갱신"],
  "code": "// 인증 시스템 코드"
}
```"""
            }
            mock_post.return_value = mock_post_response
            
            # 백엔드 에이전트 인스턴스 생성
            agent = BackendAgentOllama(api_base="http://localhost:11434/api", model="llama3")
            
            # 인증 시스템 생성 테스트
            description = "JWT를 이용한 인증 시스템을 생성하세요. 로그인, 회원가입, 토큰 갱신 기능을 포함해야 합니다."
            result = agent.create_authentication_system(description)
            
            assert "auth_method" in result
            assert "features" in result
            assert "code" in result
            assert result["auth_method"] == "JWT"
            assert "로그인" in result["features"]
            assert "회원가입" in result["features"]

def run_unsupported_task_type_test():
    """지원하지 않는 태스크 타입 테스트를 별도로 실행합니다."""
    # 백엔드 에이전트 인스턴스 생성
    agent = BackendAgentOllama(api_base="http://localhost:11434/api", model="llama3")
    
    # 지원하지 않는 태스크 타입 테스트
    task = {
        "type": "unsupported_task_type",
        "description": "지원하지 않는 태스크 타입"
    }
    
    result = agent.process_task(task)
    
    assert "status" in result
    assert result["status"] == "error"
    assert "message" in result
    assert "지원하지 않는 태스크 타입" in result["message"]

def run_optimize_performance_test():
    """성능 최적화 테스트를 별도로 실행합니다."""
    # mock 객체 설정
    with patch('agents.backend_agent_ollama.requests.get') as mock_get:
        with patch('agents.backend_agent_ollama.requests.post') as mock_post:
            # requests.get 모의 객체 설정 (모델 확인용)
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get_response.json.return_value = {
                "models": [{"name": "llama3"}]
            }
            mock_get.return_value = mock_get_response
            
            # requests.post 모의 객체 설정 (Ollama API용)
            mock_post_response = MagicMock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "response": """```json
{
  "optimization_areas": ["데이터베이스", "메모리", "알고리즘", "캐싱"],
  "total_optimizations": 1,
  "optimizations": [
    {
      "area": "데이터베이스",
      "issue": "N+1 쿼리 문제",
      "suggestion": "일괄 쿼리 사용",
      "expected_improvement": "50% 성능 향상",
      "original_code": "users.forEach(user => db.getOrders(user.id))",
      "optimized_code": "const userIds = users.map(user => user.id);\nconst orders = db.getOrdersByUserIds(userIds);"
    }
  ],
  "summary": "데이터베이스 쿼리 최적화 수행",
  "fully_optimized_code": "const express = require('express');\nconst router = express.Router();\n..."
}
```"""
            }
            mock_post.return_value = mock_post_response
            
            # 백엔드 에이전트 인스턴스 생성
            agent = BackendAgentOllama(api_base="http://localhost:11434/api", model="llama3")
            
            # 테스트 데이터
            sample_code = """
            const express = require('express');
            const router = express.Router();
            const User = require('../models/User');
            
            router.get('/users', async (req, res) => {
              const users = await User.find();
              
              // N+1 쿼리 문제
              for (const user of users) {
                const orders = await Order.find({ userId: user._id });
                user.orders = orders;
              }
              
              res.json(users);
            });
            """
            
            # 성능 최적화 테스트
            task = {
                "type": "optimize_performance",
                "code": sample_code,
                "optimization_areas": ["데이터베이스", "메모리"]
            }
            
            result = agent.process_task(task)
            
            assert result is not None
            assert "optimizations" in result
            assert "fully_optimized_code" in result
            assert len(result["optimizations"]) > 0
            assert result["total_optimizations"] > 0

def run_validate_security_test():
    """보안 검증 테스트를 별도로 실행합니다."""
    # mock 객체 설정
    with patch('agents.backend_agent_ollama.requests.get') as mock_get:
        with patch('agents.backend_agent_ollama.requests.post') as mock_post:
            # requests.get 모의 객체 설정 (모델 확인용)
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get_response.json.return_value = {
                "models": [{"name": "llama3"}]
            }
            mock_get.return_value = mock_get_response
            
            # requests.post 모의 객체 설정 (Ollama API용)
            mock_post_response = MagicMock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "response": """```json
{
  "security_level": "standard",
  "total_issues": 2,
  "issues": [
    {
      "type": "SQL 인젝션",
      "description": "사용자 입력이 SQL 쿼리에 직접 삽입됨",
      "severity": "높음",
      "location": "line 7-9",
      "fix": "매개변수화된 쿼리 사용"
    },
    {
      "type": "인증 누락",
      "description": "API 엔드포인트에 인증 검사 없음",
      "severity": "중간",
      "location": "line 5",
      "fix": "인증 미들웨어 추가"
    }
  ],
  "summary": "중요한 보안 취약점 발견됨",
  "safe_code": "const express = require('express');\nconst router = express.Router();\n..."
}
```"""
            }
            mock_post.return_value = mock_post_response
            
            # 백엔드 에이전트 인스턴스 생성
            agent = BackendAgentOllama(api_base="http://localhost:11434/api", model="llama3")
            
            # 테스트 데이터
            sample_code = """
            const express = require('express');
            const router = express.Router();
            const db = require('../db');
            
            router.get('/users/:id', (req, res) => {
              const userId = req.params.id;
              // SQL 인젝션 취약점
              const query = `SELECT * FROM users WHERE id = ${userId}`;
              db.query(query, (err, result) => {
                if (err) {
                  res.status(500).json({ error: err.message });
                } else {
                  res.json(result[0]);
                }
              });
            });
            """
            
            # 보안 검증 테스트
            task = {
                "type": "validate_security",
                "code": sample_code,
                "security_level": "standard"
            }
            
            result = agent.process_task(task)
            
            assert result is not None
            assert "issues" in result
            assert "summary" in result
            assert len(result["issues"]) > 0
            assert result["total_issues"] > 0

if __name__ == "__main__":
    # 직접 테스트 실행
    test_instance = None
    try:
        print("\n--- 백엔드 에이전트 초기화 테스트 ---")
        test_instance = test_backend_agent_init()
        print("✓ 초기화 테스트 성공")
        
        print("\n--- API 엔드포인트 생성 테스트 ---")
        run_api_endpoint_test()
        print("✓ API 엔드포인트 생성 테스트 성공")
        
        print("\n--- 데이터베이스 스키마 생성 테스트 ---")
        run_database_schema_test()
        print("✓ 데이터베이스 스키마 생성 테스트 성공")
        
        print("\n--- 인증 시스템 생성 테스트 ---")
        run_authentication_system_test()
        print("✓ 인증 시스템 생성 테스트 성공")
        
        print("\n--- 지원하지 않는 태스크 타입 테스트 ---")
        run_unsupported_task_type_test()
        print("✓ 지원하지 않는 태스크 타입 테스트 성공")
        
        print("\n--- 성능 최적화 테스트 ---")
        run_optimize_performance_test()
        print("✓ 성능 최적화 테스트 성공")
        
        print("\n--- 보안 검증 테스트 ---")
        run_validate_security_test()
        print("✓ 보안 검증 테스트 성공")
        
        print("\n모든 테스트가 성공적으로 완료되었습니다!")
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc() 