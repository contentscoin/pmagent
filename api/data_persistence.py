#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터 지속성 유틸리티

PMAgent MCP 서버의 데이터를 로컬 파일 시스템에 저장하고 불러오는 기능을 제공합니다.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# 로깅 설정
logger = logging.getLogger(__name__)

# 데이터 디렉토리 경로
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
SESSIONS_DIR = os.path.join(DATA_DIR, 'sessions')

# 디렉토리 생성
os.makedirs(SESSIONS_DIR, exist_ok=True)

async def save_data_to_file(session_id: str, data: Dict[str, Any]) -> str:
    """
    데이터를 로컬 파일 시스템에 저장합니다.
    
    Args:
        session_id: 세션 ID
        data: 저장할 데이터
        
    Returns:
        저장된 파일 경로
    """
    try:
        # 타임스탬프 추가
        data['saved_at'] = datetime.now().isoformat()
        
        # 파일 경로 설정
        file_path = os.path.join(SESSIONS_DIR, f'{session_id}.json')
        
        # 데이터 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"세션 데이터 저장 완료: {session_id}")
        return file_path
        
    except Exception as e:
        logger.error(f"데이터 저장 오류: {str(e)}")
        raise

async def load_data_from_file(session_id: str) -> Optional[Dict[str, Any]]:
    """
    로컬 파일 시스템에서 데이터를 불러옵니다.
    
    Args:
        session_id: 세션 ID
        
    Returns:
        불러온 데이터 또는 None
    """
    try:
        file_path = os.path.join(SESSIONS_DIR, f'{session_id}.json')
        
        # 파일이 존재하지 않으면 None 반환
        if not os.path.exists(file_path):
            logger.warning(f"세션 데이터 파일 없음: {session_id}")
            return None
        
        # 데이터 불러오기
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"세션 데이터 로드 완료: {session_id}")
        return data
        
    except Exception as e:
        logger.error(f"데이터 로드 오류: {str(e)}")
        return None

async def list_all_sessions() -> Dict[str, datetime]:
    """
    저장된 모든 세션 목록을 반환합니다.
    
    Returns:
        세션 ID와 마지막 수정 시간의 딕셔너리
    """
    try:
        sessions = {}
        
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith('.json'):
                session_id = filename[:-5]  # .json 제거
                file_path = os.path.join(SESSIONS_DIR, filename)
                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                sessions[session_id] = modified_time
        
        return sessions
        
    except Exception as e:
        logger.error(f"세션 목록 조회 오류: {str(e)}")
        return {}

async def delete_session_data(session_id: str) -> bool:
    """
    세션 데이터를 삭제합니다.
    
    Args:
        session_id: 삭제할 세션 ID
        
    Returns:
        삭제 성공 여부
    """
    try:
        file_path = os.path.join(SESSIONS_DIR, f'{session_id}.json')
        
        # 파일이 존재하지 않으면 False 반환
        if not os.path.exists(file_path):
            logger.warning(f"삭제할 세션 데이터 파일 없음: {session_id}")
            return False
        
        # 파일 삭제
        os.remove(file_path)
        logger.info(f"세션 데이터 삭제 완료: {session_id}")
        return True
        
    except Exception as e:
        logger.error(f"세션 데이터 삭제 오류: {str(e)}")
        return False 