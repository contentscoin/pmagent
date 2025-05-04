#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
프론트엔드 에이전트 테스트
"""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# 경로 설정 - 프로젝트 루트 디렉토리 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.frontend_agent_ollama import FrontendAgentOllama

# 테스트 데이터 - 버튼 디자인 예시
BUTTON_DESIGN_DATA = {
    "type": "button",
    "variant": "primary",
    "label": "Click Me",
    "size": "medium",
    "styles": {
        "padding": "8px 16px",
        "fontSize": "16px",
        "fontWeight": "medium",
        "borderRadius": "4px",
        "backgroundColor": "#3A86FF",
        "color": "#FFFFFF",
        "border": "none",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
        "hover": {
            "backgroundColor": "#2a75f0",
            "boxShadow": "0 4px 6px rgba(0,0,0,0.15)"
        }
    }
}

# 테스트에 사용할 모의 응답
MOCK_COMPONENT_RESPONSE = """
```tsx
import React from 'react';

interface ButtonProps {
  label: string;
  onClick?: () => void;
  className?: string;
}

export const Button: React.FC<ButtonProps> = ({
  label,
  onClick,
  className,
}) => {
  return (
    <button
      className={`button-primary-medium ${className || ''}`}
      onClick={onClick}
      style={{
        padding: '8px 16px',
        fontSize: '16px',
        fontWeight: 500,
        borderRadius: '4px',
        backgroundColor: '#3A86FF',
        color: '#FFFFFF',
        border: 'none',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
      }}
    >
      {label}
    </button>
  );
};

export default Button;
```
"""

@pytest.mark.asyncio
async def test_frontend_agent_init():
    """프론트엔드 에이전트 초기화 테스트"""
    agent = FrontendAgentOllama(name="테스트 에이전트", model="llama3")
    assert agent.name == "테스트 에이전트"
    assert agent.agent_type == "frontend"
    assert agent.config["framework"] == "react"
    assert agent.config["typescript"] == True

@pytest.mark.asyncio
@patch('agents.frontend_agent_ollama.OllamaClient')
async def test_generate_component(mock_ollama_client):
    """컴포넌트 생성 기능 테스트"""
    # OllamaClient 모의 객체 설정
    mock_client = MagicMock()
    mock_client.generate.return_value = MOCK_COMPONENT_RESPONSE
    mock_ollama_client.return_value = mock_client
    
    # 에이전트 생성
    agent = FrontendAgentOllama(name="테스트 에이전트", model="llama3")
    
    # 태스크 생성
    task = {
        "type": "generate_component",
        "component_name": "Button",
        "component_type": "button",
        "design_data": BUTTON_DESIGN_DATA
    }
    
    # 컴포넌트 생성 호출
    result = await agent.process_task(task)
    
    # 검증
    assert result["status"] == "generated"
    assert result["component_name"] == "Button"
    assert result["component_type"] == "button"
    assert "import React from 'react';" in result["code"]
    assert len(result["imports"]) >= 1
    
    # 프롬프트 생성 검증
    mock_client.generate.assert_called_once()
    prompt = mock_client.generate.call_args[0][0]
    assert "컴포넌트 이름: Button" in prompt
    assert "프레임워크: react" in prompt

@pytest.mark.asyncio
@patch('agents.frontend_agent_ollama.OllamaClient')
async def test_unsupported_task_type(mock_ollama_client):
    """지원하지 않는 태스크 타입 테스트"""
    # OllamaClient 모의 객체 설정
    mock_client = MagicMock()
    mock_ollama_client.return_value = mock_client
    
    # 에이전트 생성
    agent = FrontendAgentOllama(name="테스트 에이전트", model="llama3")
    
    # 지원하지 않는 태스크 생성
    task = {
        "type": "unsupported_task",
        "data": "test"
    }
    
    # 태스크 처리 호출
    result = await agent.process_task(task)
    
    # 검증
    assert result["status"] == "error"
    assert "지원하지 않는 태스크 타입" in result["message"]
    assert len(result["supported_types"]) > 0
    
if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 