#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
에이전트 팩토리 테스트
"""

import os
import sys
import pytest

# 경로 설정 - 프로젝트 루트 디렉토리 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.agent_factory import AgentFactory
from agents.pm_agent_ollama import PMAgentOllama
from agents.designer_agent_ollama import DesignerAgentOllama
from agents.frontend_agent_ollama import FrontendAgentOllama

def test_create_pm_agent_ollama():
    """PM 에이전트 (Ollama 백엔드) 생성 테스트"""
    agent = AgentFactory.create_agent(agent_type="pm", backend="ollama")
    assert isinstance(agent, PMAgentOllama)
    assert agent.name == "PM 에이전트"
    assert agent.agent_type == "pm"

def test_create_designer_agent_ollama():
    """디자이너 에이전트 (Ollama 백엔드) 생성 테스트"""
    agent = AgentFactory.create_agent(agent_type="designer", backend="ollama")
    assert isinstance(agent, DesignerAgentOllama)
    assert agent.name == "디자이너 에이전트"
    assert agent.agent_type == "designer"

def test_create_frontend_agent_ollama():
    """프론트엔드 에이전트 (Ollama 백엔드) 생성 테스트"""
    agent = AgentFactory.create_agent(agent_type="frontend", backend="ollama")
    assert isinstance(agent, FrontendAgentOllama)
    assert agent.name == "프론트엔드 에이전트"
    assert agent.agent_type == "frontend"

def test_create_agent_with_custom_name():
    """사용자 정의 이름을 가진 에이전트 생성 테스트"""
    agent = AgentFactory.create_agent(agent_type="pm", backend="ollama", name="커스텀 PM 에이전트")
    assert agent.name == "커스텀 PM 에이전트"

def test_create_agent_with_custom_model():
    """사용자 정의 모델을 사용하는 에이전트 생성 테스트"""
    agent = AgentFactory.create_agent(agent_type="designer", backend="ollama", model="llama3:70b")
    assert isinstance(agent, DesignerAgentOllama)
    assert agent.client.model == "llama3:70b"

def test_create_agent_with_config():
    """사용자 정의 설정을 가진 에이전트 생성 테스트"""
    config = {
        "temperature": 0.7,
        "max_tokens": 2000
    }
    agent = AgentFactory.create_agent(agent_type="pm", backend="ollama", config=config)
    assert isinstance(agent, PMAgentOllama)
    
    # 설정이 병합되었는지 확인 (PMAgentOllama의 구현에 따라 달라질 수 있음)
    if hasattr(agent, "config"):
        for key, value in config.items():
            assert agent.config.get(key) == value

def test_invalid_agent_type():
    """잘못된 에이전트 유형 처리 테스트"""
    with pytest.raises(ValueError):
        AgentFactory.create_agent(agent_type="invalid_type", backend="ollama")

def test_invalid_backend():
    """잘못된 백엔드 처리 테스트"""
    with pytest.raises(ValueError):
        AgentFactory.create_agent(agent_type="pm", backend="invalid_backend")

def test_unimplemented_backend():
    """아직 구현되지 않은 백엔드 처리 테스트"""
    with pytest.raises(ValueError):
        AgentFactory.create_agent(agent_type="pm", backend="openai")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 