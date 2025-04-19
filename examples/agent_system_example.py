#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
에이전트 시스템 사용 예제

이 예제는 전체 에이전트 시스템의 작동 방식을 보여줍니다. 프로젝트 매니저(PM) 에이전트가
디자이너, 프론트엔드, 백엔드, AI 엔지니어 에이전트들과 협업하여 프로젝트를 진행하는
과정을 시뮬레이션합니다.

예시 프로젝트: 간단한 온라인 쇼핑몰 웹사이트 개발
- 사용자 인증 (로그인/회원가입)
- 상품 목록 및 상세 페이지
- 장바구니 기능
- 결제 기능
"""

import os
import time
from typing import Dict, Any, List, Optional
import sys

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent_factory import AgentFactory


def print_separator(title: str = None):
    """구분선 출력"""
    print("\n" + "=" * 80)
    if title:
        print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def print_task_result(result: Dict[str, Any]):
    """작업 결과 출력"""
    print(f"🔹 작업 ID: {result.get('task_id', 'N/A')}")
    print(f"🔹 상태: {result.get('status', 'N/A')}")
    
    if "content" in result:
        print("\n📝 작업 내용:")
        print("-" * 50)
        print(result["content"])
        print("-" * 50)


def simulate_agent_system():
    """에이전트 시스템 시뮬레이션"""
    print("\n" + "=" * 80)
    print("=" + " " * 30 + "🤖 에이전트 시스템 초기화" + " " * 31 + "=")
    print("=")
    print("=" * 80 + "\n")

    try:
        # AgentFactory 인스턴스 생성
        factory = AgentFactory()
        
        # 환경 변수에서 키 불러오기
        # 실제 환경에서는 이 값들이 설정되어 있어야 합니다
        api_key = os.environ.get("OPENAI_API_KEY", "sk-dummy-key")
        
        print("📌 에이전트 생성 중...")
        
        # 모든 에이전트 생성
        agents = factory.create_all_agents(
            ollama_model="llama3:latest",  # 존재하지 않으면 자동으로 다른 모델로 대체됨
            ollama_api_base="http://localhost:11434/api",
            use_mcp=True,
            api_key=api_key,
            temperature=0.7,
            connect_to_pm=True
        )
        
        print(f"📌 생성된 에이전트: {', '.join(agents.keys())}")
        
        # PM 에이전트 가져오기
        pm_agent = agents["pm"]
        
        # 에이전트 상태 확인
        print("\n📌 등록된 에이전트 상태:")
        for agent_type, agent in pm_agent.agents.items():
            status = "✅ 연결됨" if agent else "❌ 연결되지 않음"
            print(f"  - {agent_type}: {status}")
        
        # MCP 연결 상태 확인
        if pm_agent.mcp_helper:
            print("\n📌 MCP 연결 상태:")
            mcps = pm_agent.mcp_helper.get_available_mcps()
            for mcp_name, available in mcps.items():
                status = "✅ 사용 가능" if available else "❌ 사용 불가"
                print(f"  - {mcp_name}: {status}")
        
        # 예제 1: 프로젝트 계획 생성
        print_separator("📋 예제 1: 프로젝트 계획 생성")
        project_description = "간단한 온라인 쇼핑몰 웹사이트를 개발해주세요. 사용자 인증, 상품 목록, 장바구니, 결제 기능이 필요합니다."
        
        print(f"📌 프로젝트 설명: {project_description}")
        print("📌 프로젝트 계획 생성 중...")
        
        plan_result = pm_agent.generate_project_plan(project_description)
        print_task_result(plan_result)
        
        # 계획 승인 (실제 시스템에서는 사용자가 승인)
        pm_agent.approve_task(plan_result["task_id"])
        print("✅ 프로젝트 계획이 승인되었습니다.")
        
        # 예제 2: 디자이너 에이전트에 작업 위임
        print_separator("🎨 예제 2: 디자이너 에이전트에 작업 위임")
        design_task = "로그인 페이지 와이어프레임을 만들어주세요. 사용자명과 비밀번호 입력란, 로그인 버튼, 회원가입 링크가 포함되어야 합니다."
        
        print(f"📌 디자인 작업: {design_task}")
        print("📌 디자이너 에이전트에 작업 위임 중...")
        
        design_result = pm_agent.execute_task(design_task, agent_type="designer")
        print_task_result(design_result)
        
        # 디자인 작업 승인
        pm_agent.approve_task(design_result["task_id"])
        print("✅ 디자인 작업이 승인되었습니다.")
        
        # 예제 3: 프론트엔드 에이전트에 작업 위임
        print_separator("💻 예제 3: 프론트엔드 에이전트에 작업 위임")
        frontend_task = "디자인 와이어프레임을 바탕으로 React 로그인 컴포넌트를 구현해주세요. 유효성 검사 기능도 포함해주세요."
        
        print(f"📌 프론트엔드 작업: {frontend_task}")
        print("📌 프론트엔드 에이전트에 작업 위임 중...")
        
        frontend_result = pm_agent.execute_task(frontend_task, agent_type="frontend")
        print_task_result(frontend_result)
        
        # 프론트엔드 작업 승인
        pm_agent.approve_task(frontend_result["task_id"])
        print("✅ 프론트엔드 작업이 승인되었습니다.")
        
        # 예제 4: 백엔드 에이전트에 작업 위임
        print_separator("🔧 예제 4: 백엔드 에이전트에 작업 위임")
        backend_task = "로그인 API 엔드포인트를 구현해주세요. 사용자 인증 및 JWT 토큰 발급 기능이 필요합니다."
        
        print(f"📌 백엔드 작업: {backend_task}")
        print("📌 백엔드 에이전트에 작업 위임 중...")
        
        backend_result = pm_agent.execute_task(backend_task, agent_type="backend")
        print_task_result(backend_result)
        
        # 백엔드 작업 승인
        pm_agent.approve_task(backend_result["task_id"])
        print("✅ 백엔드 작업이 승인되었습니다.")
        
        # 예제 5: PM 에이전트에게 프로젝트 상태 확인
        print_separator("📊 예제 5: 프로젝트 상태 확인")
        status_query = "현재 프로젝트 상태와 다음 진행해야 할 작업은 무엇인가요?"
        
        print(f"📌 상태 확인: {status_query}")
        print("📌 PM 에이전트에게 확인 중...")
        
        status_result = pm_agent.get_project_status()
        
        print("\n📊 프로젝트 현황:")
        print(f"총 작업 수: {status_result.get('total_tasks', 0)}")
        print(f"완료된 작업: {status_result.get('completed_tasks', 0)}")
        print(f"승인 대기 중: {status_result.get('pending_approval', 0)}")
        
        print("\n📊 에이전트 상태:")
        for agent_type, status in status_result.get("agent_status", {}).items():
            print(f"  - {agent_type}: {status}")
        
        print("\n📊 권장 다음 단계:")
        for step in status_result.get("next_steps", []):
            print(f"  - {step}")
        
        print_separator("🎉 시뮬레이션 완료")
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


def simulate_agent_system_mock():
    """실제 Ollama 호출 없이 에이전트 시스템 시뮬레이션"""
    print("\n" + "=" * 80)
    print("=" + " " * 30 + "🤖 에이전트 시스템 시뮬레이션 (목업)" + " " * 23 + "=")
    print("=")
    print("=" * 80 + "\n")

    # 시뮬레이션된 에이전트 딕셔너리 생성
    agents = {
        "pm": MockPMAgent(),
        "designer": MockDesignerAgent(),
        "frontend": MockFrontendAgent(),
        "backend": MockBackendAgent(),
        "ai_engineer": MockAIEngineerAgent()
    }
    
    print("📌 에이전트 생성 완료 (목업 모드)")
    
    # PM 에이전트에 다른 에이전트들 연결
    pm_agent = agents["pm"]
    pm_agent.register_agent("designer", agents["designer"])
    pm_agent.register_agent("frontend", agents["frontend"])
    pm_agent.register_agent("backend", agents["backend"])
    pm_agent.register_agent("ai_engineer", agents["ai_engineer"])
    
    print("📌 에이전트 간 연결 완료")
    
    # 프로젝트 계획 시뮬레이션
    print_separator("프로젝트 계획 수립")
    project_summary = "간단한 온라인 쇼핑 웹사이트"
    requirements = [
        "사용자 인증 기능",
        "상품 목록 및 상세 페이지",
        "장바구니 기능",
        "결제 프로세스"
    ]
    
    plan_result = pm_agent.mock_plan_project(project_summary, requirements)
    print_task_result("PM 에이전트: 프로젝트 계획", plan_result)
    
    # 디자인 작업 시뮬레이션
    print_separator("디자인 작업 진행")
    design_task = "쇼핑몰 메인 페이지 디자인"
    design_result = pm_agent.mock_delegate_task("designer", design_task)
    print_task_result("디자이너 에이전트: 디자인 작업", design_result)
    
    # 프론트엔드 작업 시뮬레이션
    print_separator("프론트엔드 개발")
    frontend_task = "상품 목록 컴포넌트 구현"
    frontend_result = pm_agent.mock_delegate_task("frontend", frontend_task)
    print_task_result("프론트엔드 에이전트: 개발 작업", frontend_result)
    
    # 백엔드 작업 시뮬레이션
    print_separator("백엔드 개발")
    backend_task = "상품 API 엔드포인트 구현"
    backend_result = pm_agent.mock_delegate_task("backend", backend_task)
    print_task_result("백엔드 에이전트: 개발 작업", backend_result)
    
    # AI 엔지니어 작업 시뮬레이션
    print_separator("AI 기능 개발")
    ai_task = "상품 추천 알고리즘 구현"
    ai_result = pm_agent.mock_delegate_task("ai_engineer", ai_task)
    print_task_result("AI 엔지니어 에이전트: 개발 작업", ai_result)
    
    # 프로젝트 상태 체크
    print_separator("프로젝트 상태 체크")
    status_result = pm_agent.mock_check_project_status()
    print_task_result("PM 에이전트: 프로젝트 상태", status_result)
    
    print("\n🎉 시뮬레이션 완료!")

# 목업 에이전트 클래스들
class MockPMAgent:
    def __init__(self):
        self.agents = {}
        
    def register_agent(self, agent_type, agent):
        self.agents[agent_type] = agent
        
    def mock_plan_project(self, project_summary, requirements):
        return f"""
프로젝트 계획 수립 완료:
- 프로젝트: {project_summary}
- 주요 기능: {', '.join(requirements)}
- 일정: 4주
- 담당자 배정 완료
"""
    
    def mock_delegate_task(self, agent_type, task):
        if agent_type in self.agents:
            if agent_type == "designer":
                return self.agents[agent_type].mock_design_task(task)
            elif agent_type == "frontend":
                return self.agents[agent_type].mock_develop_frontend(task)
            elif agent_type == "backend":
                return self.agents[agent_type].mock_develop_backend(task)
            elif agent_type == "ai_engineer":
                return self.agents[agent_type].mock_develop_ai_feature(task)
        return f"에이전트 {agent_type}에 작업 위임 실패"
    
    def mock_check_project_status(self):
        return """
프로젝트 상태:
- 디자인: 90% 완료
- 프론트엔드: 70% 완료
- 백엔드: 80% 완료
- AI 기능: 60% 완료
- 전체 진행률: 75%
"""

class MockDesignerAgent:
    def mock_design_task(self, task):
        return f"""
디자인 작업 '{task}' 완료:
- 메인 컬러: #3A86FF, #FF006E
- 타이포그래피: 'Roboto' (헤더), 'Open Sans' (본문)
- 반응형 디자인: 모바일, 태블릿, 데스크톱 지원
- 구성요소: 내비게이션 바, 상품 카드, 장바구니 아이콘
"""

class MockFrontendAgent:
    def mock_develop_frontend(self, task):
        return f"""
프론트엔드 개발 '{task}' 완료:
- React 컴포넌트 생성
- 상태 관리: Redux 사용
- API 연동: Axios 사용
- 반응형 레이아웃 구현
- 단위 테스트 작성
"""

class MockBackendAgent:
    def mock_develop_backend(self, task):
        return f"""
백엔드 개발 '{task}' 완료:
- RESTful API 엔드포인트 구현
- 데이터베이스 모델 정의 (MongoDB)
- 인증 미들웨어 구현
- API 문서화 (Swagger)
- 단위 테스트 작성
"""

class MockAIEngineerAgent:
    def mock_develop_ai_feature(self, task):
        return f"""
AI 기능 개발 '{task}' 완료:
- 협업 필터링 알고리즘 구현
- 사용자 행동 분석 모듈 개발
- A/B 테스트 설정
- 모델 성능 평가: 정확도 85%
- API 통합 완료
"""

if __name__ == "__main__":
    # 실제 Ollama 서버가 실행 중이면 실제 에이전트 시뮬레이션 실행
    # 그렇지 않으면 목업 시뮬레이션 실행
    try:
        import requests
        # Ollama 서버 연결 테스트
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            simulate_agent_system()
        else:
            print("Ollama 서버에 연결할 수 없습니다. 목업 시뮬레이션을 실행합니다.")
            simulate_agent_system_mock()
    except Exception as e:
        print(f"Ollama 서버에 연결할 수 없습니다: {e}")
        print("목업 시뮬레이션을 실행합니다.")
        simulate_agent_system_mock() 