# 플샵(PPLShop) 에이전트 시스템

플샵(PPLShop)은 올라마(Ollama) 기반의 AI 에이전트 시스템으로, 프로젝트 관리자(PM), 디자이너, 프론트엔드 개발자, 백엔드 개발자, AI 엔지니어 역할의 에이전트들이 협업하여 프로젝트를 진행하는 시스템입니다.

## 주요 기능

1. **에이전트 시스템**: 다양한 역할의 에이전트들이 협업하여 프로젝트를 진행
2. **MCP 연동**: 외부 도구(Unity, GitHub, Figma 등)와 연결하여 다양한 작업 수행
3. **Cursor Rule 준수**: 프로젝트 구조, 파일명 규칙, 디자인 시스템 등을 준수

## 시스템 구성

### 에이전트

- **PM 에이전트**: 프로젝트 계획 수립, 작업 분배, 프로젝트 관리
- **디자이너 에이전트**: UI/UX 디자인, 와이어프레임 제작, 디자인 시스템 구축
- **프론트엔드 에이전트**: React/React Native 컴포넌트 개발, 사용자 인터페이스 구현
- **백엔드 에이전트**: API 개발, 데이터베이스 관리, 서버 로직 구현
- **AI 엔지니어 에이전트**: AI 기능 개발, 데이터 분석, 머신러닝 모델 구현

### MCP(Model Context Protocol)

외부 도구와의 연동을 담당하는 프로토콜입니다.

- **Unity MCP**: Unity 엔진과 연동
- **GitHub MCP**: GitHub 저장소 관리
- **Figma MCP**: Figma 디자인 도구와 연동
- **DB MCP**: 데이터베이스 연결 및 쿼리 실행

## 프로젝트 구조

```
pplshop/
├── app/                     # 애플리케이션 코드
│   ├── screens/             # 화면 (HomeScreen.js, LoginScreen.js 등)
│   ├── components/          # 재사용 위젯 (UserCard.js, CommonButton.js)
│   ├── services/            # API, 상태 관리 모듈
│   └── config/              # 환경설정
├── assets/                  # 리소스 파일
│   ├── images/
│   ├── svg/
│   └── fonts/
├── agents/                  # 에이전트 관련 코드
│   ├── pm_agent_ollama.py             # PM 에이전트
│   ├── designer_agent_ollama.py       # 디자이너 에이전트
│   ├── frontend_agent_ollama.py       # 프론트엔드 에이전트
│   ├── backend_agent_ollama.py        # 백엔드 에이전트
│   ├── ai_engineer_agent_ollama.py    # AI 엔지니어 에이전트
│   ├── agent_factory.py               # 에이전트 팩토리
│   └── mcp_agent_helper.py            # MCP 연결 헬퍼
├── examples/                # 예제 코드
│   └── agent_system_example.py        # 에이전트 시스템 예제
├── run_demo.py              # 데모 실행 스크립트
├── test_simple_system.py    # 간단한 테스트 스크립트
├── mcp_connections_test.py  # MCP 연결 테스트
└── README.md                # 프로젝트 설명
```

## 시작하기

### 필수 요구사항

- Python 3.8 이상
- Ollama 서버 (기본 URL: http://localhost:11434/api)

### 설치

```bash
# 저장소 클론
git clone https://github.com/yourusername/pplshop.git
cd pplshop

# 필요한 패키지 설치
pip install -r requirements.txt
```

### 데모 실행

```bash
# 데모 실행
python run_demo.py

# 간단한 테스트 실행
python test_simple_system.py

# MCP 연결 테스트
python mcp_connections_test.py
```

## 디자인 시스템

Cursor Rule에 따라 다음과 같은 디자인 시스템을 사용합니다:

### 색상 시스템 (colors.js)

```javascript
export const Colors = {
  primary: '#3A86FF',
  secondary: '#8338EC',
  background: '#F8F9FA',
  textPrimary: '#212529',
  success: '#28a745',
  warning: '#ffc107',
  danger: '#dc3545',
};
```

### 타이포그래피 시스템 (typography.js)

```javascript
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
```

## 참고 사항

- 실제 사용을 위해서는 적절한 API 키와 환경 변수 설정이 필요합니다.
- MCP 연결을 위해서는 해당 도구(Unity, GitHub, Figma 등)의 API 키 또는 토큰이 필요합니다.
- Ollama 서버가 실행 중이어야 합니다.

## 라이센스

이 프로젝트는 MIT 라이센스를 따릅니다. 