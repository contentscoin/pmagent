#!/usr/bin/env python
"""
AgentFactory 테스트 스크립트
"""

from agents import AgentFactory

def main():
    print("AgentFactory 테스트 시작")
    
    # 팩토리 생성
    factory = AgentFactory()
    print("AgentFactory 생성 완료")
    
    # 사용 가능한 모델
    ollama_model = "llama3.2:latest"  # 사용 가능한 모델로 변경
    
    # 자동 등록 기능을 테스트하는 새로운 섹션
    print("\n=== 자동 등록(auto_register) 기능 테스트 ===")
    try:
        pm_agent = factory.create_agent("pm", ollama_model=ollama_model, auto_register=True)
        print(f"PM 에이전트 생성 및 다른 에이전트 자동 등록 성공: {type(pm_agent).__name__}")
        
        # 자동 등록된 에이전트 확인
        registered_agents = {agent_type: agent is not None for agent_type, agent in pm_agent.agents.items()}
        print(f"등록된 에이전트 현황: {registered_agents}")
    except Exception as e:
        print(f"자동 등록 테스트 실패: {str(e)}")
    
    # 모델 가용성 체크 테스트
    print("\n=== 모델 가용성 체크 테스트 ===")
    try:
        # 모든 에이전트 생성
        all_agents = factory.create_all_agents(ollama_model=ollama_model)
        
        # 각 에이전트의 모델 가용성 체크
        for agent_type, agent in all_agents.items():
            print(f"\n[{agent_type} 에이전트 모델 체크]")
            if hasattr(agent, "_check_model_availability"):
                is_available = agent._check_model_availability()
                print(f"모델 '{agent.model}' 가용성: {'✅ 사용 가능' if is_available else '❌ 사용 불가'}")
            else:
                print(f"모델 가용성 체크 메서드가 {agent_type} 에이전트에 없습니다.")
    except Exception as e:
        print(f"모델 가용성 체크 테스트 실패: {str(e)}")
    
    # 개별 에이전트 생성 테스트 (기존 코드)
    print("\n=== 개별 에이전트 생성 테스트 ===")
    
    # PM 에이전트 생성
    try:
        pm_agent = factory.create_agent("pm", ollama_model=ollama_model)
        print(f"PM 에이전트 생성 성공: {type(pm_agent).__name__}")
    except Exception as e:
        print(f"PM 에이전트 생성 실패: {str(e)}")
    
    # Designer 에이전트 생성
    try:
        designer_agent = factory.create_agent("designer", ollama_model=ollama_model)
        print(f"Designer 에이전트 생성 성공: {type(designer_agent).__name__}")
    except Exception as e:
        print(f"Designer 에이전트 생성 실패: {str(e)}")
    
    # Frontend 에이전트 생성
    try:
        frontend_agent = factory.create_agent("frontend", ollama_model=ollama_model)
        print(f"Frontend 에이전트 생성 성공: {type(frontend_agent).__name__}")
    except Exception as e:
        print(f"Frontend 에이전트 생성 실패: {str(e)}")
    
    # Backend 에이전트 생성
    try:
        backend_agent = factory.create_agent("backend", ollama_model=ollama_model)
        print(f"Backend 에이전트 생성 성공: {type(backend_agent).__name__}")
    except Exception as e:
        print(f"Backend 에이전트 생성 실패: {str(e)}")
    
    # AI Engineer 에이전트 생성
    try:
        ai_engineer_agent = factory.create_agent("ai_engineer", ollama_model=ollama_model)
        print(f"AI Engineer 에이전트 생성 성공: {type(ai_engineer_agent).__name__}")
    except Exception as e:
        print(f"AI Engineer 에이전트 생성 실패: {str(e)}")
    
    # 캐시 테스트
    print("\n=== 에이전트 캐시 테스트 ===")
    try:
        # 동일한 파라미터로 에이전트 생성
        cached_pm_agent = factory.create_agent("pm", ollama_model=ollama_model)
        # 객체 ID 비교
        is_cached = id(pm_agent) == id(cached_pm_agent)
        print(f"캐시된 에이전트 사용: {'✅ 성공' if is_cached else '❌ 실패'}")
        
        # 캐시 초기화
        factory.clear_cache()
        new_pm_agent = factory.create_agent("pm", ollama_model=ollama_model)
        is_new = id(pm_agent) != id(new_pm_agent)
        print(f"캐시 초기화 후 새 에이전트 생성: {'✅ 성공' if is_new else '❌ 실패'}")
    except Exception as e:
        print(f"캐시 테스트 실패: {str(e)}")
    
    print("\nAgentFactory 테스트 완료")

if __name__ == "__main__":
    main() 