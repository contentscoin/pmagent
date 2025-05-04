#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
에이전트 팩토리

다양한 유형의 에이전트를 생성하는 팩토리 패턴 구현
"""

import os
import json
import re
import requests
import sys
from typing import Dict, Any, Optional, List, Union, Tuple

# 경로 설정 - 프로젝트 루트 디렉토리 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .frontend_agent_ollama import FrontendAgentOllama
from .backend_agent_ollama import BackendAgentOllama
from .pm_agent_ollama import PMAgentOllama
from .designer_agent_ollama import DesignerAgentOllama
from .ai_engineer_agent_ollama import AIEngineerAgentOllama
from .mcp_agent_helper import MCPAgentHelper

try:
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

class AgentFactory:
    """
    에이전트 팩토리 클래스
    
    다양한 타입의 에이전트를 생성하고 관리하는 팩토리 클래스입니다.
    환경 변수 기반 설정, 파일 기반 설정을 지원하며 에이전트 캐싱 기능을 제공합니다.
    PM 에이전트에 다른 에이전트들을 자동으로 등록하여 중앙 관리 체계를 구현합니다.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        AgentFactory 초기화
        
        Args:
            config_path (Optional[str]): 설정 파일 경로 (기본값: None)
        """
        # 에이전트 캐시
        self.cache = {}
        # 설정
        self.config = {}
        # 설정 파일 로드 (제공된 경우)
        if config_path:
            self.config = self.load_config(config_path)
        
        # 모델 가용성 캐시
        self.available_models_cache = None
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        설정 파일 로드
        
        Args:
            config_path (str): 설정 파일 경로
            
        Returns:
            Dict[str, Any]: 로드된 설정
            
        Raises:
            ValueError: 설정 파일이 존재하지 않거나 읽을 수 없는 경우
        """
        if not os.path.exists(config_path):
            raise ValueError(f"설정 파일을 찾을 수 없습니다: {config_path}")
        
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            
            # 환경 변수 대체
            config_str = json.dumps(config)
            env_pattern = re.compile(r'\${([^}]+)}')
            
            def replace_env_var(match):
                env_var = match.group(1)
                return os.environ.get(env_var, "")
            
            config_str = env_pattern.sub(replace_env_var, config_str)
            config = json.loads(config_str)
            
            return config
        except Exception as e:
            raise ValueError(f"설정 파일 로드 중 오류 발생: {str(e)}")
    
    def get_api_key(self, agent_type: str = None) -> str:
        """
        에이전트 유형에 맞는 API 키 반환
        
        Args:
            agent_type (str, optional): 에이전트 유형
            
        Returns:
            str: API 키
        """
        # 설정에서 API 키 가져오기
        if self.config and "agents" in self.config:
            agents_config = self.config["agents"]
            provider = agents_config.get("provider", "ollama")
            
            if "api_keys" in agents_config and provider in agents_config["api_keys"]:
                return agents_config["api_keys"][provider]
        
        # 기본 환경 변수에서 API 키 가져오기 (필요한 경우)
        return ""
    
    def get_available_ollama_models(self, api_base: str = "http://localhost:11434/api") -> List[str]:
        """
        Ollama에서 사용 가능한 모델 목록을 가져옵니다.
        
        Args:
            api_base (str): Ollama API 기본 URL
            
        Returns:
            List[str]: 사용 가능한 모델 목록
        """
        # 캐시된 모델 목록이 있으면 반환
        if self.available_models_cache is not None:
            return self.available_models_cache
        
        try:
            url = f"{api_base.rstrip('/')}/tags"
            response = requests.get(url, timeout=3)
            response.raise_for_status()
            models = response.json().get("models", [])
            model_names = [model.get("name") for model in models]
            
            # 모델 목록 캐시
            self.available_models_cache = model_names
            return model_names
        except Exception as e:
            print(f"⚠️ Ollama 모델 목록을 가져오는 중 오류 발생: {str(e)}")
            return []
    
    def get_alternative_model(self, requested_model: str, api_base: str = "http://localhost:11434/api") -> str:
        """
        요청된 모델이 없는 경우 대체 모델을 찾습니다.
        
        Args:
            requested_model (str): 요청된 모델명
            api_base (str): Ollama API 기본 URL
            
        Returns:
            str: 대체 모델명 (사용 가능한 대체 모델이 없으면 원래 모델명 반환)
        """
        available_models = self.get_available_ollama_models(api_base)
        
        # 요청된 모델이 사용 가능하면 그대로 반환
        if requested_model in available_models:
            return requested_model
        
        # 모델이 없으면 대체 모델 찾기
        print(f"⚠️ 모델 '{requested_model}'을(를) 찾을 수 없습니다.")
        
        # llama3 관련 모델 먼저 확인
        if "llama3" in requested_model.lower():
            llama3_models = [m for m in available_models if "llama3" in m.lower()]
            if llama3_models:
                alternative = llama3_models[0]
                print(f"💡 대체 모델로 '{alternative}'을(를) 사용합니다.")
                return alternative
        
        # 다른 llama 모델 확인
        llama_models = [m for m in available_models if "llama" in m.lower()]
        if llama_models:
            alternative = llama_models[0]
            print(f"💡 대체 모델로 '{alternative}'을(를) 사용합니다.")
            return alternative
            
        # codellama 모델 확인
        codellama_models = [m for m in available_models if "codellama" in m.lower()]
        if codellama_models:
            alternative = codellama_models[0]
            print(f"💡 대체 모델로 '{alternative}'을(를) 사용합니다.")
            return alternative
        
        # 그 외 사용 가능한 모델이 있으면 첫 번째 모델 사용
        if available_models:
            alternative = available_models[0]
            print(f"💡 대체 모델로 '{alternative}'을(를) 사용합니다.")
            return alternative
        
        # 사용 가능한 모델이 없으면 원래 모델 반환
        print("⚠️ 사용 가능한 대체 모델이 없습니다. 원래 모델명을 유지합니다.")
        return requested_model
    
    def create_agent(self, agent_type: str, **kwargs) -> Any:
        """
        에이전트 생성
        
        Args:
            agent_type (str): 에이전트 유형 (pm, designer, frontend, backend, ai_engineer)
            **kwargs: 추가 매개변수
                - api_key: API 키
                - ollama_model: Ollama 모델명 (기본값: "llama3:latest")
                - ollama_api_base: Ollama API 기본 URL (기본값: "http://localhost:11434/api")
                - use_mcp: MCP 사용 여부 (기본값: False)
                - temperature: 생성 온도 (기본값: 0.7)
                - auto_register: PM 에이전트에 다른 에이전트 자동 등록 여부 (기본값: False)
            
        Returns:
            Any: 생성된 에이전트 인스턴스
            
        Raises:
            ValueError: 유효하지 않은 에이전트 유형
        """
        # API 키 설정
        api_key = kwargs.get("api_key", self.get_api_key(agent_type))
        
        # Ollama 관련 설정
        ollama_model = kwargs.get("ollama_model", "llama3:latest")
        ollama_api_base = kwargs.get("ollama_api_base", "http://localhost:11434/api")
        
        # 모델 가용성 확인 및 대체 모델 선택
        actual_model = self.get_alternative_model(ollama_model, ollama_api_base)
        
        # 캐시에서 에이전트 확인
        cache_key = f"{agent_type}_{actual_model}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # MCP 관련 설정
        use_mcp = kwargs.get("use_mcp", False)
        mcp_helper = None
        if use_mcp and MCP_AVAILABLE:
            mcp_helper = self.create_mcp_helper(**kwargs)
        
        # 생성 온도
        temperature = kwargs.get("temperature", 0.7)
        
        # 자동 등록 여부
        auto_register = kwargs.get("auto_register", False)
        
        # 에이전트 유형에 따라 인스턴스 생성
        if agent_type == "pm":
            agent = PMAgentOllama(
                api_key=api_key,
                api_base=ollama_api_base,
                model=actual_model,
                use_mcp=use_mcp,
                mcp_helper=mcp_helper,
                temperature=temperature
            )
            
            # 자동 등록이 활성화된 경우 다른 에이전트 등록
            if auto_register:
                # ollama_model 제거하여 중복 전달 방지
                register_kwargs = kwargs.copy()
                if "ollama_model" in register_kwargs:
                    del register_kwargs["ollama_model"]
                
                self._register_agents_to_pm(
                    agent, 
                    actual_model, 
                    ollama_api_base, 
                    use_mcp, 
                    mcp_helper, 
                    temperature, 
                    **register_kwargs
                )
                
        elif agent_type == "designer":
            agent = DesignerAgentOllama(
                api_key=api_key,
                api_base=ollama_api_base,
                model=actual_model,
                use_mcp=use_mcp,
                mcp_helper=mcp_helper,
                temperature=temperature
            )
        elif agent_type == "frontend":
            agent = FrontendAgentOllama(
                api_key=api_key,
                api_base=ollama_api_base,
                model=actual_model,
                use_mcp=use_mcp,
                mcp_helper=mcp_helper,
                temperature=temperature
            )
        elif agent_type == "backend":
            agent = BackendAgentOllama(
                api_key=api_key,
                api_base=ollama_api_base,
                model=actual_model,
                use_mcp=use_mcp,
                mcp_helper=mcp_helper,
                temperature=temperature
            )
        elif agent_type == "ai_engineer":
            agent = AIEngineerAgentOllama(
                api_key=api_key,
                api_base=ollama_api_base,
                model=actual_model,
                use_mcp=use_mcp,
                mcp_helper=mcp_helper,
                temperature=temperature
            )
        else:
            raise ValueError(f"유효하지 않은 에이전트 유형: {agent_type}")
        
        # 에이전트 캐싱
        self.cache[cache_key] = agent
        
        return agent
    
    def _register_agents_to_pm(self, pm_agent: PMAgentOllama, 
                              ollama_model: str, ollama_api_base: str, 
                              use_mcp: bool, mcp_helper: Any, 
                              temperature: float, **kwargs) -> None:
        """
        PM 에이전트에 다른 에이전트들을 등록합니다.
        
        Args:
            pm_agent: PM 에이전트 인스턴스
            ollama_model: Ollama 모델명
            ollama_api_base: Ollama API 기본 URL
            use_mcp: MCP 사용 여부
            mcp_helper: MCP 헬퍼 인스턴스
            temperature: 생성 온도
            **kwargs: 추가 매개변수
        """
        # 에이전트 유형 목록 (PM 제외)
        agent_types = ["designer", "frontend", "backend", "ai_engineer"]
        
        # 각 에이전트 유형에 대해 인스턴스 생성 및 등록
        for agent_type in agent_types:
            # 에이전트 유형별 모델 오버라이드 확인
            model_key = f"{agent_type}_model"
            agent_model = kwargs.get(model_key, ollama_model)
            
            # 모델 가용성 확인 및 대체 모델 선택
            actual_model = self.get_alternative_model(agent_model, ollama_api_base)
            
            # 캐시 확인 또는 새로 생성
            cache_key = f"{agent_type}_{actual_model}"
            if cache_key in self.cache:
                agent = self.cache[cache_key]
            else:
                # 에이전트 생성
                api_key = kwargs.get("api_key", self.get_api_key(agent_type))
                
                if agent_type == "designer":
                    agent = DesignerAgentOllama(
                        api_key=api_key,
                        api_base=ollama_api_base,
                        model=actual_model,
                        use_mcp=use_mcp,
                        mcp_helper=mcp_helper,
                        temperature=temperature
                    )
                elif agent_type == "frontend":
                    agent = FrontendAgentOllama(
                        api_key=api_key,
                        api_base=ollama_api_base,
                        model=actual_model,
                        use_mcp=use_mcp,
                        mcp_helper=mcp_helper,
                        temperature=temperature
                    )
                elif agent_type == "backend":
                    agent = BackendAgentOllama(
                        api_key=api_key,
                        api_base=ollama_api_base,
                        model=actual_model,
                        use_mcp=use_mcp,
                        mcp_helper=mcp_helper,
                        temperature=temperature
                    )
                elif agent_type == "ai_engineer":
                    agent = AIEngineerAgentOllama(
                        api_key=api_key,
                        api_base=ollama_api_base,
                        model=actual_model,
                        use_mcp=use_mcp,
                        mcp_helper=mcp_helper,
                        temperature=temperature
                    )
                    
                # 에이전트 캐싱
                self.cache[cache_key] = agent
            
            # PM 에이전트에 등록
            pm_agent.register_agent(agent_type, agent)
    
    def create_mcp_helper(self, **kwargs) -> MCPAgentHelper:
        """
        MCP 헬퍼 생성
        
        Args:
            **kwargs: MCPAgentHelper 생성에 필요한 추가 매개변수
            
        Returns:
            MCPAgentHelper: 생성된 MCP 헬퍼 인스턴스
        """
        # 캐시에서 MCP 헬퍼 확인
        if "mcp_helper" in self.cache:
            return self.cache["mcp_helper"]
        
        # 설정에서 매개변수 가져오기
        unity_mcp_host = kwargs.get("unity_mcp_host", os.environ.get("UNITY_MCP_HOST"))
        github_token = kwargs.get("github_token", os.environ.get("GITHUB_TOKEN"))
        figma_token = kwargs.get("figma_token", os.environ.get("FIGMA_TOKEN"))
        db_connection_string = kwargs.get("db_connection_string", os.environ.get("DB_CONNECTION_STRING"))
        
        # MCP 헬퍼 생성
        helper = MCPAgentHelper(
            unity_mcp_host=unity_mcp_host,
            github_token=github_token,
            figma_token=figma_token,
            db_connection_string=db_connection_string
        )
        
        # MCP 헬퍼 캐싱
        self.cache["mcp_helper"] = helper
        
        return helper
    
    def clear_cache(self):
        """
        에이전트 캐시 초기화
        """
        self.cache = {}
    
    def create_all_agents(self, connect_to_pm: bool = True, **kwargs) -> Dict[str, Any]:
        """
        모든 유형의 에이전트 생성
        
        Args:
            connect_to_pm: 생성된 에이전트들을 PM 에이전트에 연결할지 여부 (기본값: True)
            **kwargs: 추가 매개변수 (ollama_model, ollama_api_base 등)
                - ollama_model: 기본 Ollama 모델 (기본값: "llama3:latest")
                - ollama_api_base: Ollama API 기본 URL
                - use_mcp: MCP 사용 여부
                - 각 에이전트별 모델 지정: designer_model, frontend_model, backend_model, ai_engineer_model
            
        Returns:
            Dict[str, Any]: 에이전트 유형을 키로, 에이전트 인스턴스를 값으로 하는 사전
        """
        agents = {}
        agent_types = ["designer", "frontend", "backend", "ai_engineer"]
        
        # Ollama API 기본 URL
        ollama_api_base = kwargs.get("ollama_api_base", "http://localhost:11434/api")
        
        # 기본 모델 및 모델 가용성 확인
        base_model = kwargs.get("ollama_model", "llama3:latest")
        actual_base_model = self.get_alternative_model(base_model, ollama_api_base)
        
        # PM 에이전트는 connect_to_pm이 True일 때는 마지막에 생성
        if not connect_to_pm:
            agent_types.insert(0, "pm")
        
        # 다른 에이전트들 먼저 생성
        for agent_type in agent_types:
            # 에이전트별 모델 오버라이드 확인
            model_key = f"{agent_type}_model"
            agent_model = kwargs.get(model_key, actual_base_model)
            
            # 에이전트 생성 (이미 get_alternative_model이 create_agent 내부에서 호출됨)
            # kwargs에서 ollama_model을 제거하고 별도로 전달
            agent_kwargs = kwargs.copy()
            if "ollama_model" in agent_kwargs:
                del agent_kwargs["ollama_model"]
            
            agents[agent_type] = self.create_agent(
                agent_type,
                ollama_model=agent_model,
                **agent_kwargs
            )
        
        # PM 에이전트가 마지막에 생성되어 다른 에이전트들을 자동 등록
        if connect_to_pm:
            # PM 에이전트별 모델 오버라이드 확인
            pm_model = kwargs.get("pm_model", actual_base_model)
            
            # kwargs에서 ollama_model을 제거하고 별도로 전달
            pm_kwargs = kwargs.copy()
            if "ollama_model" in pm_kwargs:
                del pm_kwargs["ollama_model"]
            
            agents["pm"] = self.create_agent(
                "pm",
                ollama_model=pm_model,
                auto_register=True,
                **pm_kwargs
            )
            
            # 등록 결과 확인
            if hasattr(agents["pm"], "agents"):
                all_registered = True
                for agent_type in agent_types:
                    if not agents["pm"].agents.get(agent_type):
                        all_registered = False
                        break
                
                if not all_registered:
                    # 수동으로 에이전트 등록
                    for agent_type in agent_types:
                        if agent_type in agents and agent_type in agents["pm"].agents:
                            agents["pm"].register_agent(agent_type, agents[agent_type])
        
        return agents


if __name__ == "__main__":
    # 테스트 코드
    factory = AgentFactory()
    
    try:
        # 자동 등록 기능을 사용하여 PM 에이전트 생성
        pm_agent = factory.create_agent("pm", auto_register=True)
        print(f"PM 에이전트 생성 성공: {type(pm_agent).__name__}")
        
        # 등록된 에이전트 확인
        registered_agents = {agent_type: agent is not None for agent_type, agent in pm_agent.agents.items()}
        print(f"등록된 에이전트 현황: {registered_agents}")
        
        # create_all_agents 메서드 테스트
        print("\n모든 에이전트 생성 테스트")
        all_agents = factory.create_all_agents(connect_to_pm=True)
        print(f"생성된 에이전트 수: {len(all_agents)}")
        
        # PM 에이전트에 등록된 에이전트 확인
        pm = all_agents["pm"]
        registered_count = sum(1 for agent in pm.agents.values() if agent is not None)
        print(f"PM 에이전트에 등록된 에이전트 수: {registered_count}")
        
    except Exception as e:
        print(f"에이전트 생성 중 오류 발생: {str(e)}") 