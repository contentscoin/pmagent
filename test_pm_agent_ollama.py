import os
import sys
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from agents.agent_factory import AgentFactory
from agents.pm_agent_ollama import PMAgentOllama

def test_create_pm_agent_ollama():
    """
    AgentFactory를 통해 PMAgentOllama 생성 테스트
    """
    factory = AgentFactory()
    
    # PM Agent Ollama 생성
    pm_agent = factory.create_agent(
        "pm_ollama", 
        ollama_model="llama3:latest",
        use_ollama=True,
        use_mcp=True
    )
    
    logger.info(f"PM Agent 생성됨: {type(pm_agent).__name__}")
    assert isinstance(pm_agent, PMAgentOllama)
    
    # PM Agent Ollama 직접 생성
    direct_pm_agent = PMAgentOllama(
        api_key="dummy",
        api_base="http://localhost:11434/api",
        model="llama3:latest",
        use_mcp=True
    )
    
    logger.info(f"PM Agent 직접 생성됨: {type(direct_pm_agent).__name__}")
    assert isinstance(direct_pm_agent, PMAgentOllama)
    
    return pm_agent

def test_pm_agent_functionality(pm_agent):
    """
    PMAgentOllama 기능 테스트
    """
    # 프로젝트 계획 생성 테스트
    task_description = "간단한 사용자 관리 시스템 설계"
    
    logger.info(f"프로젝트 계획 생성 테스트: {task_description}")
    
    try:
        # 모델 사용 가능 여부 확인
        is_available = pm_agent.check_model()
        logger.info(f"모델 사용 가능: {is_available}")
        
        if is_available:
            # 프로젝트 계획 생성
            project_plan = pm_agent.generate_project_plan(task_description)
            logger.info(f"생성된 프로젝트 계획: {project_plan}")
            
            # 태스크 분석
            task_analysis = pm_agent.analyze_task(task_description)
            logger.info(f"태스크 분석 결과: {task_analysis}")
    except Exception as e:
        logger.error(f"에러 발생: {str(e)}")

if __name__ == "__main__":
    try:
        # PMAgentOllama 생성 테스트
        pm_agent = test_create_pm_agent_ollama()
        
        # Ollama 서버 실행 중인 경우에만 기능 테스트 실행
        if pm_agent.check_model():
            test_pm_agent_functionality(pm_agent)
        else:
            logger.warning("Ollama 서버가 실행 중이지 않거나 접근할 수 없어 기능 테스트를 건너뜁니다.")
    except Exception as e:
        logger.error(f"테스트 실행 중 에러 발생: {str(e)}")
        sys.exit(1)
    
    logger.info("모든 테스트 완료!")
    sys.exit(0) 