#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
분산 데이터 저장 모듈

다양한 백엔드(파일 시스템, 데이터베이스, 클라우드 스토리지)를 지원하는 
분산 데이터 저장 클래스를 제공합니다.
"""

import os
import json
import time
import logging
import shutil
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class StorageBackend(ABC):
    """
    저장소 백엔드 추상 기본 클래스
    
    다양한 저장소 구현체의 공통 인터페이스를 정의합니다.
    """
    
    @abstractmethod
    def put(self, key: str, data: Any) -> bool:
        """
        데이터를 저장합니다.
        
        Args:
            key: 데이터 키
            data: 저장할 데이터
            
        Returns:
            bool: 성공 여부
        """
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        데이터를 조회합니다.
        
        Args:
            key: 데이터 키
            
        Returns:
            Optional[Any]: 데이터 (존재하지 않으면 None)
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        데이터를 삭제합니다.
        
        Args:
            key: 데이터 키
            
        Returns:
            bool: 성공 여부
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        데이터가 존재하는지 확인합니다.
        
        Args:
            key: 데이터 키
            
        Returns:
            bool: 존재 여부
        """
        pass
    
    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """
        키 목록을 조회합니다.
        
        Args:
            prefix: 키 접두사
            
        Returns:
            List[str]: 키 목록
        """
        pass

class FileSystemBackend(StorageBackend):
    """
    파일 시스템 기반 저장소 백엔드
    
    로컬 파일 시스템을 사용하여 데이터를 저장합니다.
    """
    
    def __init__(self, base_dir: str):
        """
        FileSystemBackend 초기화
        
        Args:
            base_dir: 기본 디렉토리 경로
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True, parents=True)
        
        # 파일 잠금 관리
        self.locks = {}
    
    def _get_path(self, key: str) -> Path:
        """
        키에 해당하는 파일 경로를 반환합니다.
        
        Args:
            key: 데이터 키
            
        Returns:
            Path: 파일 경로
        """
        # 키를 파일 경로로 변환
        key_path = key.replace(":", "/")
        return self.base_dir / key_path
    
    def _acquire_lock(self, key: str) -> threading.Lock:
        """
        키에 대한 잠금을 획득합니다.
        
        Args:
            key: 데이터 키
            
        Returns:
            threading.Lock: 잠금 객체
        """
        if key not in self.locks:
            self.locks[key] = threading.Lock()
        return self.locks[key]
    
    def put(self, key: str, data: Any) -> bool:
        """
        데이터를 저장합니다.
        
        Args:
            key: 데이터 키
            data: 저장할 데이터
            
        Returns:
            bool: 성공 여부
        """
        lock = self._acquire_lock(key)
        
        with lock:
            try:
                file_path = self._get_path(key)
                
                # 디렉토리 생성
                file_path.parent.mkdir(exist_ok=True, parents=True)
                
                # 데이터 저장
                with open(file_path, "w", encoding="utf-8") as f:
                    if isinstance(data, (dict, list)):
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    else:
                        f.write(str(data))
                
                return True
            except Exception as e:
                logger.error(f"데이터 저장 중 오류 발생: {str(e)}")
                return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        데이터를 조회합니다.
        
        Args:
            key: 데이터 키
            
        Returns:
            Optional[Any]: 데이터 (존재하지 않으면 None)
        """
        lock = self._acquire_lock(key)
        
        with lock:
            try:
                file_path = self._get_path(key)
                
                if not file_path.exists():
                    return None
                
                # 데이터 로드
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    
                    # JSON 형식이면 파싱
                    if content.startswith(("{", "[")):
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            pass
                    
                    return content
            except Exception as e:
                logger.error(f"데이터 조회 중 오류 발생: {str(e)}")
                return None
    
    def delete(self, key: str) -> bool:
        """
        데이터를 삭제합니다.
        
        Args:
            key: 데이터 키
            
        Returns:
            bool: 성공 여부
        """
        lock = self._acquire_lock(key)
        
        with lock:
            try:
                file_path = self._get_path(key)
                
                if not file_path.exists():
                    return False
                
                # 파일 삭제
                file_path.unlink()
                
                # 빈 디렉토리 정리
                parent_dir = file_path.parent
                while parent_dir != self.base_dir and not any(parent_dir.iterdir()):
                    parent_dir.rmdir()
                    parent_dir = parent_dir.parent
                
                return True
            except Exception as e:
                logger.error(f"데이터 삭제 중 오류 발생: {str(e)}")
                return False
    
    def exists(self, key: str) -> bool:
        """
        데이터가 존재하는지 확인합니다.
        
        Args:
            key: 데이터 키
            
        Returns:
            bool: 존재 여부
        """
        file_path = self._get_path(key)
        return file_path.exists()
    
    def list_keys(self, prefix: str = "") -> List[str]:
        """
        키 목록을 조회합니다.
        
        Args:
            prefix: 키 접두사
            
        Returns:
            List[str]: 키 목록
        """
        try:
            prefix_path = prefix.replace(":", "/")
            base_path = self.base_dir / prefix_path
            
            if not base_path.exists():
                return []
            
            if base_path.is_file():
                rel_path = str(base_path.relative_to(self.base_dir))
                return [rel_path.replace("/", ":")]
            
            result = []
            for path in base_path.glob("**/*"):
                if path.is_file():
                    rel_path = str(path.relative_to(self.base_dir))
                    result.append(rel_path.replace("/", ":"))
            
            return result
        except Exception as e:
            logger.error(f"키 목록 조회 중 오류 발생: {str(e)}")
            return []

class DistributedStorage:
    """
    분산 데이터 저장소 클래스
    
    다양한 백엔드를 통합하여 분산 데이터 저장 기능을 제공합니다.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        DistributedStorage 초기화
        
        Args:
            config: 설정 (기본값: None)
        """
        self.config = config or {}
        
        # 기본 저장소 디렉토리
        base_dir = self.config.get("base_dir", "./data/storage")
        
        # 백엔드 초기화
        self.backends = {
            "file": FileSystemBackend(base_dir)
        }
        
        # 현재 사용 중인 백엔드
        self.current_backend = "file"
        
        # 이벤트 리스너
        self.listeners = {
            "put": [],
            "get": [],
            "delete": []
        }
    
    def add_backend(self, name: str, backend: StorageBackend) -> None:
        """
        새 백엔드를 추가합니다.
        
        Args:
            name: 백엔드 이름
            backend: 백엔드 인스턴스
        """
        self.backends[name] = backend
    
    def set_current_backend(self, name: str) -> bool:
        """
        현재 사용할 백엔드를 설정합니다.
        
        Args:
            name: 백엔드 이름
            
        Returns:
            bool: 성공 여부
        """
        if name in self.backends:
            self.current_backend = name
            return True
        return False
    
    def add_listener(self, event: str, callback: Callable) -> None:
        """
        이벤트 리스너를 추가합니다.
        
        Args:
            event: 이벤트 유형 (put, get, delete)
            callback: 콜백 함수
        """
        if event in self.listeners:
            self.listeners[event].append(callback)
    
    def _notify_listeners(self, event: str, key: str, data: Any = None) -> None:
        """
        이벤트 리스너에 알립니다.
        
        Args:
            event: 이벤트 유형
            key: 데이터 키
            data: 데이터 (선택)
        """
        if event in self.listeners:
            for callback in self.listeners[event]:
                try:
                    callback(event, key, data)
                except Exception as e:
                    logger.error(f"리스너 실행 중 오류 발생: {str(e)}")
    
    def put(self, key: str, data: Any, backend: Optional[str] = None) -> bool:
        """
        데이터를 저장합니다.
        
        Args:
            key: 데이터 키
            data: 저장할 데이터
            backend: 사용할 백엔드 (기본값: 현재 백엔드)
            
        Returns:
            bool: 성공 여부
        """
        backend_name = backend or self.current_backend
        
        if backend_name not in self.backends:
            logger.error(f"존재하지 않는 백엔드: {backend_name}")
            return False
        
        # 백엔드를 통해 데이터 저장
        result = self.backends[backend_name].put(key, data)
        
        # 성공 시 리스너에 알림
        if result:
            self._notify_listeners("put", key, data)
        
        return result
    
    def get(self, key: str, backend: Optional[str] = None) -> Optional[Any]:
        """
        데이터를 조회합니다.
        
        Args:
            key: 데이터 키
            backend: 사용할 백엔드 (기본값: 현재 백엔드)
            
        Returns:
            Optional[Any]: 데이터 (존재하지 않으면 None)
        """
        backend_name = backend or self.current_backend
        
        if backend_name not in self.backends:
            logger.error(f"존재하지 않는 백엔드: {backend_name}")
            return None
        
        # 백엔드를 통해 데이터 조회
        result = self.backends[backend_name].get(key)
        
        # 결과가 있으면 리스너에 알림
        if result is not None:
            self._notify_listeners("get", key, result)
        
        return result
    
    def delete(self, key: str, backend: Optional[str] = None) -> bool:
        """
        데이터를 삭제합니다.
        
        Args:
            key: 데이터 키
            backend: 사용할 백엔드 (기본값: 현재 백엔드)
            
        Returns:
            bool: 성공 여부
        """
        backend_name = backend or self.current_backend
        
        if backend_name not in self.backends:
            logger.error(f"존재하지 않는 백엔드: {backend_name}")
            return False
        
        # 백엔드를 통해 데이터 삭제
        result = self.backends[backend_name].delete(key)
        
        # 성공 시 리스너에 알림
        if result:
            self._notify_listeners("delete", key)
        
        return result
    
    def exists(self, key: str, backend: Optional[str] = None) -> bool:
        """
        데이터가 존재하는지 확인합니다.
        
        Args:
            key: 데이터 키
            backend: 사용할 백엔드 (기본값: 현재 백엔드)
            
        Returns:
            bool: 존재 여부
        """
        backend_name = backend or self.current_backend
        
        if backend_name not in self.backends:
            logger.error(f"존재하지 않는 백엔드: {backend_name}")
            return False
        
        return self.backends[backend_name].exists(key)
    
    def list_keys(self, prefix: str = "", backend: Optional[str] = None) -> List[str]:
        """
        키 목록을 조회합니다.
        
        Args:
            prefix: 키 접두사
            backend: 사용할 백엔드 (기본값: 현재 백엔드)
            
        Returns:
            List[str]: 키 목록
        """
        backend_name = backend or self.current_backend
        
        if backend_name not in self.backends:
            logger.error(f"존재하지 않는 백엔드: {backend_name}")
            return []
        
        return self.backends[backend_name].list_keys(prefix)
    
    def copy(self, src_key: str, dest_key: str, 
             src_backend: Optional[str] = None, 
             dest_backend: Optional[str] = None) -> bool:
        """
        데이터를 복사합니다.
        
        Args:
            src_key: 원본 키
            dest_key: 대상 키
            src_backend: 원본 백엔드 (기본값: 현재 백엔드)
            dest_backend: 대상 백엔드 (기본값: 원본 백엔드와 동일)
            
        Returns:
            bool: 성공 여부
        """
        src_backend_name = src_backend or self.current_backend
        dest_backend_name = dest_backend or src_backend_name
        
        # 원본 데이터 조회
        data = self.get(src_key, src_backend_name)
        if data is None:
            return False
        
        # 대상에 저장
        return self.put(dest_key, data, dest_backend_name)
    
    def move(self, src_key: str, dest_key: str,
             src_backend: Optional[str] = None,
             dest_backend: Optional[str] = None) -> bool:
        """
        데이터를 이동합니다.
        
        Args:
            src_key: 원본 키
            dest_key: 대상 키
            src_backend: 원본 백엔드 (기본값: 현재 백엔드)
            dest_backend: 대상 백엔드 (기본값: 원본 백엔드와 동일)
            
        Returns:
            bool: 성공 여부
        """
        # 같은 백엔드 내에서 이동하는 경우 최적화 가능하지만,
        # 여기서는 단순히 복사 후 삭제로 구현
        if self.copy(src_key, dest_key, src_backend, dest_backend):
            return self.delete(src_key, src_backend)
        return False
    
    def clear(self, prefix: str = "", backend: Optional[str] = None) -> bool:
        """
        접두사에 해당하는 모든 데이터를 삭제합니다.
        
        Args:
            prefix: 키 접두사
            backend: 사용할 백엔드 (기본값: 현재 백엔드)
            
        Returns:
            bool: 성공 여부
        """
        backend_name = backend or self.current_backend
        
        # 키 목록 조회
        keys = self.list_keys(prefix, backend_name)
        
        # 모든 키 삭제
        success = True
        for key in keys:
            if not self.delete(key, backend_name):
                success = False
        
        return success
    
    def backup(self, backup_dir: str, backend: Optional[str] = None) -> bool:
        """
        백업을 생성합니다.
        
        Args:
            backup_dir: 백업 디렉토리 경로
            backend: 사용할 백엔드 (기본값: 현재 백엔드)
            
        Returns:
            bool: 성공 여부
        """
        backend_name = backend or self.current_backend
        
        if backend_name not in self.backends:
            logger.error(f"존재하지 않는 백엔드: {backend_name}")
            return False
        
        # 현재는 파일 시스템 백엔드만 지원
        if backend_name != "file":
            logger.error(f"백업이 지원되지 않는 백엔드: {backend_name}")
            return False
        
        try:
            # 백업 디렉토리 생성
            backup_path = Path(backup_dir)
            backup_path.mkdir(exist_ok=True, parents=True)
            
            # 파일 시스템 백엔드의 데이터 디렉토리 복사
            file_backend = self.backends[backend_name]
            
            # 타임스탬프를 포함한 백업 디렉토리 이름 생성
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            dest_dir = backup_path / f"backup_{timestamp}"
            
            # 데이터 복사
            shutil.copytree(file_backend.base_dir, dest_dir)
            
            return True
        except Exception as e:
            logger.error(f"백업 생성 중 오류 발생: {str(e)}")
            return False
    
    def restore(self, backup_path: str, backend: Optional[str] = None) -> bool:
        """
        백업에서 복원합니다.
        
        Args:
            backup_path: 백업 경로
            backend: 사용할 백엔드 (기본값: 현재 백엔드)
            
        Returns:
            bool: 성공 여부
        """
        backend_name = backend or self.current_backend
        
        if backend_name not in self.backends:
            logger.error(f"존재하지 않는 백엔드: {backend_name}")
            return False
        
        # 현재는 파일 시스템 백엔드만 지원
        if backend_name != "file":
            logger.error(f"복원이 지원되지 않는 백엔드: {backend_name}")
            return False
        
        try:
            # 백업 경로 확인
            src_path = Path(backup_path)
            if not src_path.exists() or not src_path.is_dir():
                logger.error(f"유효하지 않은 백업 경로: {backup_path}")
                return False
            
            # 파일 시스템 백엔드의 데이터 디렉토리 비우기
            file_backend = self.backends[backend_name]
            dest_dir = file_backend.base_dir
            
            if dest_dir.exists():
                # 기존 데이터 백업
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                backup_dir = dest_dir.parent / f"backup_before_restore_{timestamp}"
                shutil.copytree(dest_dir, backup_dir)
                
                # 디렉토리 비우기
                for item in dest_dir.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
            else:
                dest_dir.mkdir(exist_ok=True, parents=True)
            
            # 백업 데이터 복사
            for item in src_path.iterdir():
                src = item
                dest = dest_dir / item.name
                
                if src.is_dir():
                    shutil.copytree(src, dest)
                else:
                    shutil.copy2(src, dest)
            
            return True
        except Exception as e:
            logger.error(f"백업 복원 중 오류 발생: {str(e)}")
            return False 