#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
인증 및 권한 관리 모듈

사용자 및 에이전트 인증, 토큰 발급 및 검증, 권한 확인 기능을 제공합니다.
"""

import os
import json
import time
import uuid
import hashlib
import secrets
import logging
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class AuthManager:
    """
    인증 및 권한 관리 클래스
    
    - 사용자 및 에이전트 인증
    - 토큰 발급 및 검증
    - 권한 확인 및 관리
    """
    
    def __init__(self, data_dir: Optional[str] = None, token_expiry: int = 86400):
        """
        AuthManager 초기화
        
        Args:
            data_dir: 데이터 저장 디렉토리 (기본값: 환경 변수 DATA_DIR 또는 "./data")
            token_expiry: 토큰 만료 시간(초) (기본값: 24시간)
        """
        # 데이터 디렉토리 설정
        self.data_dir = data_dir or os.environ.get("DATA_DIR", "./data")
        # auth 디렉토리 생성
        self.auth_dir = os.path.join(self.data_dir, "auth")
        Path(self.auth_dir).mkdir(exist_ok=True, parents=True)
        
        # 파일 경로
        self.users_file = os.path.join(self.auth_dir, "users.json")
        self.agents_file = os.path.join(self.auth_dir, "agents.json")
        self.tokens_file = os.path.join(self.auth_dir, "tokens.json")
        
        # 암호화 키 설정
        self.secret_key = os.environ.get("AUTH_SECRET_KEY")
        if not self.secret_key:
            key_file = os.path.join(self.auth_dir, "secret_key")
            if os.path.exists(key_file):
                with open(key_file, "r") as f:
                    self.secret_key = f.read().strip()
            else:
                # 새 키 생성
                self.secret_key = secrets.token_hex(32)
                with open(key_file, "w") as f:
                    f.write(self.secret_key)
        
        # 토큰 만료 시간
        self.token_expiry = token_expiry
        
        # 사용자, 에이전트, 토큰 데이터
        self.users = {}
        self.agents = {}
        self.tokens = {}
        
        # 데이터 로드
        self._load_data()
        
        # 기본 관리자 계정 생성 (없는 경우)
        self._ensure_admin_user()
    
    def _load_data(self) -> None:
        """데이터 파일에서 데이터를 로드합니다."""
        # 사용자 데이터 로드
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, "r", encoding="utf-8") as f:
                    self.users = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"잘못된 JSON 포맷: {self.users_file}")
                self.users = {}
        
        # 에이전트 데이터 로드
        if os.path.exists(self.agents_file):
            try:
                with open(self.agents_file, "r", encoding="utf-8") as f:
                    self.agents = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"잘못된 JSON 포맷: {self.agents_file}")
                self.agents = {}
        
        # 토큰 데이터 로드
        if os.path.exists(self.tokens_file):
            try:
                with open(self.tokens_file, "r", encoding="utf-8") as f:
                    self.tokens = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"잘못된 JSON 포맷: {self.tokens_file}")
                self.tokens = {}
    
    def _save_data(self) -> None:
        """현재 데이터를 파일에 저장합니다."""
        # 사용자 데이터 저장
        with open(self.users_file, "w", encoding="utf-8") as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
        
        # 에이전트 데이터 저장
        with open(self.agents_file, "w", encoding="utf-8") as f:
            json.dump(self.agents, f, ensure_ascii=False, indent=2)
        
        # 토큰 데이터 저장
        with open(self.tokens_file, "w", encoding="utf-8") as f:
            json.dump(self.tokens, f, ensure_ascii=False, indent=2)
    
    def _ensure_admin_user(self) -> None:
        """기본 관리자 계정이 존재하는지 확인하고 없으면 생성합니다."""
        # 관리자 계정이 있는지 확인
        admin_exists = False
        for user_id, user_data in self.users.items():
            if user_data.get("role") == "admin":
                admin_exists = True
                break
        
        # 관리자 계정이 없으면 생성
        if not admin_exists:
            default_admin_password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin123")
            self.create_user(
                username="admin",
                password=default_admin_password,
                email="admin@example.com",
                role="admin"
            )
            logger.info("기본 관리자 계정이 생성되었습니다.")
    
    def _hash_password(self, password: str) -> str:
        """
        비밀번호를 해시화합니다.
        
        Args:
            password: 원본 비밀번호
            
        Returns:
            str: 해시화된 비밀번호
        """
        # 솔트 생성
        salt = secrets.token_hex(8)
        # 해시 생성
        h = hashlib.sha256()
        h.update(f"{password}{salt}".encode("utf-8"))
        return f"{salt}${h.hexdigest()}"
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """
        비밀번호가 해시와 일치하는지 확인합니다.
        
        Args:
            password: 확인할 비밀번호
            hashed: 저장된 해시값
            
        Returns:
            bool: 일치 여부
        """
        salt, hash_value = hashed.split("$", 1)
        h = hashlib.sha256()
        h.update(f"{password}{salt}".encode("utf-8"))
        return h.hexdigest() == hash_value
    
    def _generate_token(self, user_id: str, token_type: str = "access") -> str:
        """
        JWT 토큰을 생성합니다.
        
        Args:
            user_id: 사용자 ID
            token_type: 토큰 유형 (access, refresh)
            
        Returns:
            str: JWT 토큰
        """
        now = datetime.utcnow()
        
        # 토큰 만료 시간 설정
        if token_type == "refresh":
            expires = now + timedelta(days=30)  # 리프레시 토큰은 30일 유효
        else:
            expires = now + timedelta(seconds=self.token_expiry)  # 액세스 토큰은 설정된 시간만큼 유효
        
        # 토큰 페이로드
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": expires,
            "type": token_type
        }
        
        # 사용자 역할 추가
        if user_id in self.users:
            payload["role"] = self.users[user_id].get("role", "user")
        
        # 토큰 생성
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        # 토큰 저장
        token_id = str(uuid.uuid4())
        self.tokens[token_id] = {
            "id": token_id,
            "user_id": user_id,
            "type": token_type,
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "is_revoked": False
        }
        self._save_data()
        
        return token
    
    def _verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        JWT 토큰을 검증합니다.
        
        Args:
            token: JWT 토큰
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: (유효 여부, 토큰 정보)
        """
        try:
            # 토큰 디코딩
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # 토큰 유효성 검사
            user_id = payload.get("sub")
            token_type = payload.get("type", "access")
            
            # 사용자 존재 확인
            if user_id not in self.users:
                return False, None
            
            # 토큰 취소 여부 확인
            for token_id, token_info in self.tokens.items():
                if (token_info.get("user_id") == user_id and 
                    token_info.get("type") == token_type and 
                    token_info.get("is_revoked", False)):
                    # 해당 사용자의 같은 유형의 토큰이 취소된 경우
                    return False, None
            
            return True, payload
        except jwt.PyJWTError:
            return False, None
    
    def create_user(self, username: str, password: str, email: str, role: str = "user") -> str:
        """
        새 사용자를 생성합니다.
        
        Args:
            username: 사용자명
            password: 비밀번호
            email: 이메일
            role: 역할 (admin, user)
            
        Returns:
            str: 사용자 ID
            
        Raises:
            ValueError: 사용자명이나 이메일이 이미 사용 중인 경우
        """
        # 사용자명 중복 확인
        for _, user_data in self.users.items():
            if user_data.get("username") == username:
                raise ValueError(f"사용자명 '{username}'은(는) 이미 사용 중입니다.")
            if user_data.get("email") == email:
                raise ValueError(f"이메일 '{email}'은(는) 이미 사용 중입니다.")
        
        # 사용자 ID 생성
        user_id = str(uuid.uuid4())
        
        # 비밀번호 해시화
        hashed_password = self._hash_password(password)
        
        # 사용자 정보 생성
        now = datetime.now().isoformat()
        self.users[user_id] = {
            "id": user_id,
            "username": username,
            "email": email,
            "password": hashed_password,
            "role": role,
            "created_at": now,
            "updated_at": now,
            "last_login": None
        }
        
        self._save_data()
        logger.info(f"사용자 '{username}' 생성됨 (ID: {user_id}, 역할: {role})")
        
        return user_id
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """
        사용자 인증을 수행합니다.
        
        Args:
            username: 사용자명
            password: 비밀번호
            
        Returns:
            Optional[str]: 인증 성공 시 사용자 ID, 실패 시 None
        """
        # 사용자명으로 사용자 찾기
        user_id = None
        for uid, user_data in self.users.items():
            if user_data.get("username") == username:
                user_id = uid
                break
        
        if not user_id:
            return None
        
        # 비밀번호 확인
        user_data = self.users[user_id]
        if not self._verify_password(password, user_data["password"]):
            return None
        
        # 마지막 로그인 시간 업데이트
        user_data["last_login"] = datetime.now().isoformat()
        user_data["updated_at"] = datetime.now().isoformat()
        self._save_data()
        
        return user_id
    
    def generate_auth_tokens(self, user_id: str) -> Dict[str, str]:
        """
        사용자에 대한 인증 토큰을 생성합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            Dict[str, str]: 액세스 토큰과 리프레시 토큰
        """
        if user_id not in self.users:
            raise ValueError(f"존재하지 않는 사용자 ID: {user_id}")
        
        access_token = self._generate_token(user_id, "access")
        refresh_token = self._generate_token(user_id, "refresh")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.token_expiry
        }
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        리프레시 토큰을 사용하여 새 액세스 토큰을 발급합니다.
        
        Args:
            refresh_token: 리프레시 토큰
            
        Returns:
            Optional[Dict[str, str]]: 새 액세스 토큰 정보
        """
        # 리프레시 토큰 검증
        is_valid, payload = self._verify_token(refresh_token)
        if not is_valid or payload.get("type") != "refresh":
            return None
        
        # 새 액세스 토큰 발급
        user_id = payload.get("sub")
        access_token = self._generate_token(user_id, "access")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.token_expiry
        }
    
    def revoke_token(self, token: str) -> bool:
        """
        토큰을 취소(무효화)합니다.
        
        Args:
            token: JWT 토큰
            
        Returns:
            bool: 취소 성공 여부
        """
        # 토큰 검증
        is_valid, payload = self._verify_token(token)
        if not is_valid:
            return False
        
        # 토큰 정보 가져오기
        user_id = payload.get("sub")
        token_type = payload.get("type", "access")
        
        # 토큰 찾기 및 취소 처리
        for token_id, token_info in self.tokens.items():
            if token_info.get("user_id") == user_id and token_info.get("type") == token_type:
                token_info["is_revoked"] = True
                self._save_data()
                return True
        
        return False
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        토큰을 검증하고 정보를 반환합니다.
        
        Args:
            token: JWT 토큰
            
        Returns:
            Dict[str, Any]: 토큰 검증 결과
                - is_valid: 토큰 유효 여부
                - user_id: 사용자 ID (유효한 경우)
                - role: 사용자 역할 (유효한 경우)
                - error: 오류 메시지 (유효하지 않은 경우)
        """
        # 토큰 검증
        is_valid, payload = self._verify_token(token)
        
        if not is_valid:
            return {
                "is_valid": False,
                "error": "유효하지 않은 토큰"
            }
        
        # 사용자 정보 가져오기
        user_id = payload.get("sub")
        role = payload.get("role", "user")
        
        return {
            "is_valid": True,
            "user_id": user_id,
            "role": role
        }
    
    def update_user(self, user_id: str, data: Dict[str, Any]) -> bool:
        """
        사용자 정보를 업데이트합니다.
        
        Args:
            user_id: 사용자 ID
            data: 업데이트할 데이터
                - username: 사용자명
                - email: 이메일
                - password: 비밀번호
                - role: 역할
            
        Returns:
            bool: 업데이트 성공 여부
        """
        if user_id not in self.users:
            return False
        
        user_data = self.users[user_id]
        updated = False
        
        # 사용자명 업데이트
        if "username" in data and data["username"] != user_data["username"]:
            # 중복 확인
            for uid, u_data in self.users.items():
                if uid != user_id and u_data.get("username") == data["username"]:
                    raise ValueError(f"사용자명 '{data['username']}'은(는) 이미 사용 중입니다.")
            
            user_data["username"] = data["username"]
            updated = True
        
        # 이메일 업데이트
        if "email" in data and data["email"] != user_data["email"]:
            # 중복 확인
            for uid, u_data in self.users.items():
                if uid != user_id and u_data.get("email") == data["email"]:
                    raise ValueError(f"이메일 '{data['email']}'은(는) 이미 사용 중입니다.")
            
            user_data["email"] = data["email"]
            updated = True
        
        # 비밀번호 업데이트
        if "password" in data:
            user_data["password"] = self._hash_password(data["password"])
            updated = True
        
        # 역할 업데이트
        if "role" in data and data["role"] in ["admin", "user"]:
            user_data["role"] = data["role"]
            updated = True
        
        if updated:
            user_data["updated_at"] = datetime.now().isoformat()
            self._save_data()
        
        return updated
    
    def delete_user(self, user_id: str) -> bool:
        """
        사용자를 삭제합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        if user_id not in self.users:
            return False
        
        # 마지막 관리자 계정은 삭제 불가
        user_data = self.users[user_id]
        if user_data.get("role") == "admin":
            admin_count = 0
            for _, u_data in self.users.items():
                if u_data.get("role") == "admin":
                    admin_count += 1
            
            if admin_count <= 1:
                raise ValueError("마지막 관리자 계정은 삭제할 수 없습니다.")
        
        # 사용자 삭제
        del self.users[user_id]
        
        # 해당 사용자의 토큰도 모두 삭제
        for token_id in list(self.tokens.keys()):
            if self.tokens[token_id].get("user_id") == user_id:
                del self.tokens[token_id]
        
        self._save_data()
        return True
    
    def create_agent_token(self, agent_id: str, agent_type: str, permissions: List[str] = None) -> str:
        """
        에이전트 인증 토큰을 생성합니다.
        
        Args:
            agent_id: 에이전트 ID
            agent_type: 에이전트 유형 (pm, designer, frontend, backend, ai_engineer)
            permissions: 권한 목록
            
        Returns:
            str: 에이전트 토큰
        """
        # 에이전트 정보 생성
        now = datetime.utcnow()
        expires = now + timedelta(days=365)  # 에이전트 토큰은 1년 유효
        
        # 토큰 페이로드
        payload = {
            "sub": agent_id,
            "type": "agent",
            "agent_type": agent_type,
            "permissions": permissions or [],
            "iat": now,
            "exp": expires
        }
        
        # 토큰 생성
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        # 에이전트 정보 저장
        if agent_id not in self.agents:
            self.agents[agent_id] = {
                "id": agent_id,
                "type": agent_type,
                "created_at": now.isoformat(),
                "permissions": permissions or [],
                "last_active": None
            }
            self._save_data()
        
        return token
    
    def validate_agent_token(self, token: str) -> Dict[str, Any]:
        """
        에이전트 토큰을 검증합니다.
        
        Args:
            token: 에이전트 토큰
            
        Returns:
            Dict[str, Any]: 토큰 검증 결과
                - is_valid: 토큰 유효 여부
                - agent_id: 에이전트 ID (유효한 경우)
                - agent_type: 에이전트 유형 (유효한 경우)
                - permissions: 권한 목록 (유효한 경우)
                - error: 오류 메시지 (유효하지 않은 경우)
        """
        try:
            # 토큰 디코딩
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # 토큰 유형 확인
            if payload.get("type") != "agent":
                return {
                    "is_valid": False,
                    "error": "에이전트 토큰이 아닙니다."
                }
            
            # 에이전트 ID와 유형 가져오기
            agent_id = payload.get("sub")
            agent_type = payload.get("agent_type")
            permissions = payload.get("permissions", [])
            
            # 에이전트 존재 확인
            if agent_id in self.agents:
                # 마지막 활성 시간 업데이트
                self.agents[agent_id]["last_active"] = datetime.now().isoformat()
                self._save_data()
            
            return {
                "is_valid": True,
                "agent_id": agent_id,
                "agent_type": agent_type,
                "permissions": permissions
            }
        except jwt.PyJWTError as e:
            return {
                "is_valid": False,
                "error": f"토큰 검증 실패: {str(e)}"
            }
    
    def revoke_agent_token(self, agent_id: str) -> bool:
        """
        에이전트 토큰을 취소(무효화)합니다.
        
        Args:
            agent_id: 에이전트 ID
            
        Returns:
            bool: 취소 성공 여부
        """
        if agent_id not in self.agents:
            return False
        
        # 에이전트 삭제
        del self.agents[agent_id]
        self._save_data()
        
        return True
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        사용자 정보를 조회합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            Optional[Dict[str, Any]]: 사용자 정보
        """
        if user_id not in self.users:
            return None
        
        user_data = self.users[user_id].copy()
        # 비밀번호 해시는 반환하지 않음
        if "password" in user_data:
            del user_data["password"]
        
        return user_data
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        에이전트 정보를 조회합니다.
        
        Args:
            agent_id: 에이전트 ID
            
        Returns:
            Optional[Dict[str, Any]]: 에이전트 정보
        """
        if agent_id not in self.agents:
            return None
        
        return self.agents[agent_id].copy()
    
    def list_users(self) -> List[Dict[str, Any]]:
        """
        모든 사용자 목록을 조회합니다.
        
        Returns:
            List[Dict[str, Any]]: 사용자 정보 목록
        """
        users_list = []
        for user_id, user_data in self.users.items():
            user_info = user_data.copy()
            # 비밀번호 해시는 반환하지 않음
            if "password" in user_info:
                del user_info["password"]
            users_list.append(user_info)
        
        return users_list
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        모든 에이전트 목록을 조회합니다.
        
        Returns:
            List[Dict[str, Any]]: 에이전트 정보 목록
        """
        return [agent_data.copy() for agent_data in self.agents.values()]
    
    def check_permission(self, token: str, required_permissions: List[str] = None) -> Dict[str, Any]:
        """
        토큰의 권한을 확인합니다.
        
        Args:
            token: JWT 토큰
            required_permissions: 필요한 권한 목록
            
        Returns:
            Dict[str, Any]: 권한 확인 결과
                - has_permission: 권한 보유 여부
                - is_valid: 토큰 유효 여부
                - user_id/agent_id: 사용자/에이전트 ID
                - role/agent_type: 사용자 역할/에이전트 유형
                - error: 오류 메시지 (권한이 없는 경우)
        """
        # 토큰 검증
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # 토큰 유형 확인
            token_type = payload.get("type")
            
            if token_type == "agent":
                # 에이전트 토큰 처리
                agent_id = payload.get("sub")
                agent_type = payload.get("agent_type")
                permissions = payload.get("permissions", [])
                
                # 권한 확인
                has_permission = True
                if required_permissions:
                    has_permission = all(perm in permissions for perm in required_permissions)
                
                return {
                    "has_permission": has_permission,
                    "is_valid": True,
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                    "token_type": "agent",
                    "error": None if has_permission else "필요한 권한이 없습니다."
                }
            else:
                # 사용자 토큰 처리
                user_id = payload.get("sub")
                role = payload.get("role", "user")
                
                # 관리자는 모든 권한 보유
                if role == "admin":
                    return {
                        "has_permission": True,
                        "is_valid": True,
                        "user_id": user_id,
                        "role": role,
                        "token_type": "user",
                        "error": None
                    }
                
                # 일반 사용자는 기본 권한만 보유
                has_permission = True
                if required_permissions:
                    # 사용자의 권한 확인 방식에 따라 구현 필요
                    has_permission = False
                
                return {
                    "has_permission": has_permission,
                    "is_valid": True,
                    "user_id": user_id,
                    "role": role,
                    "token_type": "user",
                    "error": None if has_permission else "필요한 권한이 없습니다."
                }
        except jwt.PyJWTError as e:
            return {
                "has_permission": False,
                "is_valid": False,
                "error": f"토큰 검증 실패: {str(e)}"
            } 