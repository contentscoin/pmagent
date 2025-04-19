#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
플샵(PPLShop) 에이전트 시스템 데모 실행 스크립트

이 스크립트는 에이전트 시스템을 데모 모드로 실행하고 결과를 파일로 출력합니다.
PowerShell 렌더링 문제를 우회하기 위해 결과를 파일로 저장합니다.
"""

import os
import sys
import time
from typing import Dict, Any, List, Optional

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.agent_factory import AgentFactory


def write_separator(file, title: str = None):
    """구분선 출력"""
    file.write("\n" + "=" * 80 + "\n")
    if title:
        file.write(f" {title} ".center(80, "=") + "\n")
    file.write("=" * 80 + "\n\n")


def run_demo():
    """데모 시스템 실행"""
    # 결과 파일 열기
    with open("demo_results.txt", "w", encoding="utf-8") as f:
        write_separator(f, "🤖 플샵(PPLShop) 에이전트 시스템 데모")
        
        try:
            # AgentFactory 인스턴스 생성
            f.write("📌 에이전트 팩토리 초기화 중...\n")
            factory = AgentFactory()
            
            # 환경 변수에서 키 불러오기
            api_key = os.environ.get("OPENAI_API_KEY", "sk-dummy-key")
            
            f.write("📌 에이전트 생성 중...\n")
            
            # 수정: 에이전트 팩토리로부터 직접 에이전트 생성
            # PM 에이전트 생성
            pm_agent = factory.create_agent(
                "pm", 
                api_key=api_key,
                ollama_model="llama3:latest",
                ollama_api_base="http://localhost:11434/api",
                use_mcp=True,
                temperature=0.7
            )
            
            # 각 에이전트 생성 및 PM에 등록
            designer_agent = factory.create_agent(
                "designer",
                api_key=api_key,
                ollama_model="llama3:latest",
                ollama_api_base="http://localhost:11434/api",
                use_mcp=True,
                temperature=0.7
            )
            pm_agent.register_agent("designer", designer_agent)
            
            frontend_agent = factory.create_agent(
                "frontend",
                api_key=api_key,
                ollama_model="llama3:latest",
                ollama_api_base="http://localhost:11434/api",
                use_mcp=True,
                temperature=0.7
            )
            pm_agent.register_agent("frontend", frontend_agent)
            
            backend_agent = factory.create_agent(
                "backend",
                api_key=api_key,
                ollama_model="llama3:latest",
                ollama_api_base="http://localhost:11434/api",
                use_mcp=True,
                temperature=0.7
            )
            pm_agent.register_agent("backend", backend_agent)
            
            ai_engineer_agent = factory.create_agent(
                "ai_engineer",
                api_key=api_key,
                ollama_model="llama3:latest",
                ollama_api_base="http://localhost:11434/api",
                use_mcp=True,
                temperature=0.7
            )
            pm_agent.register_agent("ai_engineer", ai_engineer_agent)
            
            # 모든 에이전트를 사전에 저장
            agents = {
                "pm": pm_agent,
                "designer": designer_agent,
                "frontend": frontend_agent,
                "backend": backend_agent,
                "ai_engineer": ai_engineer_agent
            }
            
            f.write(f"📌 생성된 에이전트: {', '.join(agents.keys())}\n")
            
            # 에이전트 상태 확인
            f.write("\n📌 등록된 에이전트 상태:\n")
            for agent_type, agent in pm_agent.agents.items():
                status = "✅ 연결됨" if agent else "❌ 연결되지 않음"
                f.write(f"  - {agent_type}: {status}\n")
            
            # MCP 연결 상태 확인
            if pm_agent.mcp_helper:
                f.write("\n📌 MCP 연결 상태:\n")
                mcps = pm_agent.mcp_helper.get_available_mcps()
                for mcp_name, available in mcps.items():
                    status = "✅ 사용 가능" if available else "❌ 사용 불가"
                    f.write(f"  - {mcp_name}: {status}\n")
            
            # 에이전트 시스템 프롬프트 (모형화된 예시)
            write_separator(f, "PM 에이전트 시스템 프롬프트 (예시)")
            f.write("""
당신은 플샵(PPLShop) 프로젝트의 PM(Project Manager) 에이전트입니다.
당신의 역할은 프로젝트 계획을 수립하고, 다른 에이전트들(디자이너, 프론트엔드, 백엔드, AI 엔지니어)에게
작업을 할당하고, 프로젝트 진행 상황을 모니터링하는 것입니다.

주요 책임:
1. 프로젝트 요구사항 분석 및 계획 수립
2. 작업 분배 및 우선순위 설정
3. 에이전트 간 조율 및 협업 촉진
4. 프로젝트 진행 상황 추적
5. 위험 관리 및 문제 해결

당신은 Cursor Rules를 철저히 준수해야 하며, 프로젝트 구조, 파일명 규칙, 디자인 시스템 등을 고려해야 합니다.
""")
            
            write_separator(f, "디자이너 에이전트 시스템 프롬프트 (예시)")
            f.write("""
당신은 플샵(PPLShop) 프로젝트의 디자이너 에이전트입니다.
당신의 역할은 UI/UX 디자인, 와이어프레임 제작, 디자인 시스템 구축을 담당하는 것입니다.

주요 책임:
1. 사용자 인터페이스(UI) 디자인
2. 사용자 경험(UX) 최적화
3. 와이어프레임 및 프로토타입 제작
4. 디자인 시스템 구축 및 관리
5. 디자인 가이드라인 제공

당신은 Cursor Rules를 준수해야 하며, 특히 디자인 시스템(colors.js, typography.js, spacing.js)을
일관되게 적용해야 합니다.
""")
            
            write_separator(f, "프론트엔드 에이전트 시스템 프롬프트 (예시)")
            f.write("""
당신은 플샵(PPLShop) 프로젝트의 프론트엔드 에이전트입니다.
당신의 역할은 React/React Native 컴포넌트를 개발하고, 사용자 인터페이스를 구현하는 것입니다.

주요 책임:
1. React/React Native 컴포넌트 개발
2. 반응형 레이아웃 구현
3. API 연동
4. 상태 관리
5. 프론트엔드 테스트

당신은 Cursor Rules를 준수해야 하며, 특히 디자인 시스템을 활용하고 파일명 규칙(예: MainScreen.js,
UserCardComponent.js)을 따라야 합니다.
""")
            
            write_separator(f, "백엔드 에이전트 시스템 프롬프트 (예시)")
            f.write("""
당신은 플샵(PPLShop) 프로젝트의 백엔드 에이전트입니다.
당신의 역할은 API 엔드포인트를 개발하고, 데이터베이스를 관리하며, 서버 로직을 구현하는 것입니다.

주요 책임:
1. RESTful API 개발
2. 데이터베이스 설계 및 구현
3. 인증 및 권한 관리
4. 비즈니스 로직 구현
5. 백엔드 테스트

당신은 Cursor Rules를 준수해야 하며, 특히 services 폴더 구조와 명확한 함수/파일명을 사용해야 합니다.
""")
            
            # 간단한 프로젝트 계획 생성 예시 (목업 데이터)
            write_separator(f, "간단한 프로젝트 계획 예시 (목업)")
            project_plan = {
                "project_name": "플샵(PPLShop) - 온라인 쇼핑몰",
                "description": "사용자 인증, 상품 목록, 장바구니, 결제 기능을 갖춘 온라인 쇼핑몰",
                "timeline": "4주",
                "phases": [
                    {"name": "기획 및 디자인", "duration": "1주", "status": "완료"},
                    {"name": "프론트엔드 개발", "duration": "2주", "status": "진행 중"},
                    {"name": "백엔드 개발", "duration": "2주", "status": "진행 중"},
                    {"name": "테스트 및 배포", "duration": "1주", "status": "예정"}
                ],
                "agents": {
                    "pm": "프로젝트 전체 조율 및 관리",
                    "designer": "UI/UX 디자인 및 와이어프레임 생성",
                    "frontend": "React 컴포넌트 개발 및 API 연동",
                    "backend": "RESTful API 구현 및 데이터베이스 관리",
                    "ai_engineer": "상품 추천 시스템 개발"
                }
            }
            
            # 프로젝트 계획 출력
            f.write("📋 프로젝트명: " + project_plan["project_name"] + "\n")
            f.write("📋 설명: " + project_plan["description"] + "\n")
            f.write("📋 예상 기간: " + project_plan["timeline"] + "\n\n")
            
            f.write("📋 단계:\n")
            for phase in project_plan["phases"]:
                status_emoji = "✅" if phase["status"] == "완료" else "🔄" if phase["status"] == "진행 중" else "⏳"
                f.write(f"  - {status_emoji} {phase['name']} ({phase['duration']}): {phase['status']}\n")
            
            f.write("\n📋 에이전트 역할:\n")
            for agent_type, role in project_plan["agents"].items():
                f.write(f"  - {agent_type}: {role}\n")
            
            # 폴더 구조 및 파일명 규칙 예시 (Cursor Rule 기반)
            write_separator(f, "플샵(PPLShop) 폴더 구조 및 파일명 규칙 예시")
            f.write("""
📁 프로젝트 구조

pplshop/
├── 📁 app/
│   ├── 📁 screens/         # 화면 (HomeScreen.js, LoginScreen.js 등)
│   ├── 📁 components/      # 재사용 위젯 (UserCard.js, CommonButton.js)
│   ├── 📁 services/        # API, 상태 관리 모듈
│   ├── 📁 config/          # 환경설정 (env 등)
│   ├── 📄 App.js           # 앱 진입점
│   └── 📄 index.js         # 런처(선택)
├── 📁 assets/
│   ├── 📁 images/
│   ├── 📁 svg/
│   └── 📁 fonts/
├── 📁 agents/              # 에이전트 관련 코드
│   ├── 📄 pm_agent_ollama.py         # PM 에이전트
│   ├── 📄 designer_agent_ollama.py   # 디자이너 에이전트
│   ├── 📄 frontend_agent_ollama.py   # 프론트엔드 에이전트
│   ├── 📄 backend_agent_ollama.py    # 백엔드 에이전트
│   ├── 📄 ai_engineer_agent_ollama.py # AI 엔지니어 에이전트
│   ├── 📄 agent_factory.py           # 에이전트 팩토리
│   └── 📄 mcp_agent_helper.py        # MCP 연결 헬퍼
└── 📄 package.json
""")

            # Cursor Rule에 따른 디자인 시스템 예시
            write_separator(f, "Cursor Rule 기반 디자인 시스템 예시")
            f.write("""
// colors.js - 컬러 팔레트
export const Colors = {
  primary: '#3A86FF',
  secondary: '#8338EC',
  background: '#F8F9FA',
  textPrimary: '#212529',
  success: '#28a745',
  warning: '#ffc107',
  danger: '#dc3545',
};

// typography.js - 타이포그래피 시스템
export const Typography = {
  heading1: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.textPrimary,
  },
  body1: {
    fontSize: 16,
    color: Colors.textPrimary,
  },
  button: {
    fontSize: 14,
    fontWeight: '600',
  },
};

// spacing.js - 간격 시스템
export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
};
""")
            
            # 마무리
            write_separator(f, "🎉 플샵(PPLShop) 에이전트 시스템 데모 완료")
            f.write("데모가 성공적으로 완료되었습니다.\n")
            f.write("실제 시스템 구현 시에는 Ollama API를 통한 실제 에이전트 호출이 이루어집니다.\n")
            f.write("MCP 연결을 통해 외부 도구(Unity, GitHub, Figma 등)와 통합이 가능합니다.\n")
            
        except Exception as e:
            f.write(f"❌ 오류 발생: {str(e)}\n")
            import traceback
            f.write(traceback.format_exc())
    
    print("데모 실행 완료! 결과는 'demo_results.txt' 파일에서 확인할 수 있습니다.")


if __name__ == "__main__":
    run_demo() 