#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Ollama 클라이언트 모듈

Ollama API와 통신하기 위한 클라이언트 구현
"""

import json
import logging
import aiohttp
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class OllamaClient:
    """Ollama API 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Ollama 클라이언트 초기화
        
        Args:
            base_url: Ollama API 기본 URL (기본값: http://localhost:11434)
        """
        self.base_url = base_url
        self.api_generate = f"{base_url}/api/generate"
        self.api_chat = f"{base_url}/api/chat"
        self.api_embeddings = f"{base_url}/api/embeddings"
        self.api_models = f"{base_url}/api/models"
        
        logger.info(f"Ollama 클라이언트 초기화 완료 (API: {base_url})")
    
    async def generate(self, model: str, prompt: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        텍스트 생성 API 호출
        
        Args:
            model: 모델 이름 (예: llama2, mistral)
            prompt: 생성을 위한 프롬프트
            options: 생성 옵션 (temperature, top_p 등)
            
        Returns:
            Dict[str, Any]: API 응답
        """
        req_data = {
            "model": model,
            "prompt": prompt
        }
        
        if options:
            req_data.update(options)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_generate, json=req_data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API 오류 (generate): {response.status} - {error_text}")
                        return {"error": f"API 오류: {response.status}", "message": error_text}
        except Exception as e:
            logger.error(f"Ollama 클라이언트 오류 (generate): {str(e)}")
            return {"error": "클라이언트 오류", "message": str(e)}
    
    async def chat(self, model: str, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        채팅 API 호출
        
        Args:
            model: 모델 이름 (예: llama2, mistral)
            messages: 채팅 메시지 목록 (예: [{"role": "user", "content": "안녕"}])
            options: 생성 옵션 (temperature, top_p 등)
            
        Returns:
            Dict[str, Any]: API 응답
        """
        req_data = {
            "model": model,
            "messages": messages
        }
        
        if options:
            req_data.update(options)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_chat, json=req_data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API 오류 (chat): {response.status} - {error_text}")
                        return {"error": f"API 오류: {response.status}", "message": error_text}
        except Exception as e:
            logger.error(f"Ollama 클라이언트 오류 (chat): {str(e)}")
            return {"error": "클라이언트 오류", "message": str(e)}
    
    async def get_embeddings(self, model: str, text: str) -> Dict[str, Any]:
        """
        임베딩 API 호출
        
        Args:
            model: 임베딩 모델 이름
            text: 임베딩할 텍스트
            
        Returns:
            Dict[str, Any]: API 응답 (embedding 벡터 포함)
        """
        req_data = {
            "model": model,
            "prompt": text
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_embeddings, json=req_data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API 오류 (embeddings): {response.status} - {error_text}")
                        return {"error": f"API 오류: {response.status}", "message": error_text}
        except Exception as e:
            logger.error(f"Ollama 클라이언트 오류 (embeddings): {str(e)}")
            return {"error": "클라이언트 오류", "message": str(e)}
    
    async def list_models(self) -> Dict[str, Any]:
        """
        사용 가능한 모델 목록 조회
        
        Returns:
            Dict[str, Any]: API 응답 (모델 목록 포함)
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_models) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API 오류 (models): {response.status} - {error_text}")
                        return {"error": f"API 오류: {response.status}", "message": error_text}
        except Exception as e:
            logger.error(f"Ollama 클라이언트 오류 (models): {str(e)}")
            return {"error": "클라이언트 오류", "message": str(e)} 