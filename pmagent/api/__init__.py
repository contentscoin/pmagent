#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent API 패키지

에이전트 협업 시스템을 위한 RESTful API 제공.
"""

from fastapi import FastAPI
from .routes import router, auth_manager, agent_coordinator, storage
from ..auth import AuthManager
from ..agent_coordinator import AgentCoordinator
from ..distributed_storage import DistributedStorage

def create_api_app(config: dict = None) -> FastAPI:
    """
    API 애플리케이션을 생성합니다.
    
    Args:
        config: 설정 (기본값: None)
        
    Returns:
        FastAPI: FastAPI 애플리케이션 인스턴스
    """
    # 기본 설정 값
    if config is None:
        config = {}
    
    # FastAPI 앱 생성
    app = FastAPI(
        title="PMAgent API",
        description="프로젝트 관리 에이전트 협업 시스템 API",
        version="0.1.0"
    )
    
    # 인증 관리자, 에이전트 코디네이터, 저장소 초기화
    data_dir = config.get("data_dir", "./data")
    
    # 인증 관리자 초기화
    global auth_manager
    auth_manager = AuthManager(data_dir=data_dir)
    
    # 에이전트 코디네이터 초기화
    global agent_coordinator
    agent_coordinator = AgentCoordinator(data_dir=data_dir)
    
    # 분산 저장소 초기화
    global storage
    storage_config = {"base_dir": data_dir}
    storage = DistributedStorage(config=storage_config)
    
    # 파일 시스템 백엔드 추가 및 설정
    from ..distributed_storage import FileSystemBackend
    import os
    
    # 저장소 디렉토리 생성
    storage_dir = os.path.join(data_dir, "storage")
    os.makedirs(storage_dir, exist_ok=True)
    
    # 파일 시스템 백엔드 추가
    file_backend = FileSystemBackend(storage_dir)
    storage.add_backend("file", file_backend)
    storage.set_current_backend("file")
    
    # 라우터 등록
    app.include_router(router, prefix="/api")
    
    return app 