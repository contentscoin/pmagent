#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent MCP 서버 데이터 지속성 테스트
"""

import os
import json
import uuid
import pytest
import shutil
from datetime import datetime
from api.data_persistence import (
    save_data_to_file,
    load_data_from_file,
    list_all_sessions,
    delete_session_data,
    SESSIONS_DIR
)

# 테스트 디렉토리 설정
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
TEST_SESSIONS_DIR = os.path.join(TEST_DATA_DIR, 'sessions')

# 테스트 데이터
@pytest.fixture
def test_session_id():
    return str(uuid.uuid4())

@pytest.fixture
def test_data():
    return {
        "projects": {
            "project1": {"id": "project1", "name": "Test Project 1"},
            "project2": {"id": "project2", "name": "Test Project 2"}
        },
        "tasks": {
            "task1": {"id": "task1", "name": "Test Task 1", "project_id": "project1"},
            "task2": {"id": "task2", "name": "Test Task 2", "project_id": "project2"}
        },
        "requests": {
            "request1": {"id": "request1", "original_request": "Test Request"}
        },
        "agents": {
            "agent1": {"id": "agent1", "type": "designer"}
        },
        "export_time": datetime.now().isoformat()
    }

# 테스트 전후 설정
@pytest.fixture(autouse=True)
async def setup_and_teardown():
    # 테스트 디렉토리 생성
    os.makedirs(TEST_SESSIONS_DIR, exist_ok=True)
    
    # 원래 디렉토리 경로 저장
    original_sessions_dir = SESSIONS_DIR
    
    # 테스트 디렉토리로 변경
    import api.data_persistence
    api.data_persistence.SESSIONS_DIR = TEST_SESSIONS_DIR
    
    yield
    
    # 원래 디렉토리 경로로 복원
    api.data_persistence.SESSIONS_DIR = original_sessions_dir
    
    # 테스트 디렉토리 삭제
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)

# 테스트 함수
@pytest.mark.asyncio
async def test_save_and_load_data(test_session_id, test_data):
    """저장 및 불러오기 기능 테스트"""
    # 데이터 저장
    file_path = await save_data_to_file(test_session_id, test_data)
    
    # 파일 존재 확인
    assert os.path.exists(file_path)
    
    # 데이터 불러오기
    loaded_data = await load_data_from_file(test_session_id)
    
    # 데이터 비교
    assert loaded_data is not None
    assert loaded_data["projects"] == test_data["projects"]
    assert loaded_data["tasks"] == test_data["tasks"]
    assert loaded_data["requests"] == test_data["requests"]
    assert loaded_data["agents"] == test_data["agents"]
    assert "saved_at" in loaded_data

@pytest.mark.asyncio
async def test_list_sessions(test_session_id, test_data):
    """세션 목록 조회 테스트"""
    # 데이터 저장
    await save_data_to_file(test_session_id, test_data)
    
    # 세션 목록 조회
    sessions = await list_all_sessions()
    
    # 세션 존재 확인
    assert test_session_id in sessions
    assert isinstance(sessions[test_session_id], datetime)

@pytest.mark.asyncio
async def test_delete_session(test_session_id, test_data):
    """세션 삭제 테스트"""
    # 데이터 저장
    await save_data_to_file(test_session_id, test_data)
    
    # 파일 존재 확인
    file_path = os.path.join(TEST_SESSIONS_DIR, f'{test_session_id}.json')
    assert os.path.exists(file_path)
    
    # 세션 삭제
    result = await delete_session_data(test_session_id)
    assert result is True
    
    # 파일 삭제 확인
    assert not os.path.exists(file_path)
    
    # 존재하지 않는 세션 삭제 시도
    result = await delete_session_data("non_existent_session")
    assert result is False

@pytest.mark.asyncio
async def test_load_non_existent_session():
    """존재하지 않는 세션 불러오기 테스트"""
    # 존재하지 않는 세션 데이터 불러오기
    data = await load_data_from_file("non_existent_session")
    assert data is None 