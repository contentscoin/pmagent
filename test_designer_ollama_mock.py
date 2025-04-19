#!/usr/bin/env python
"""
DesignerAgentOllama Mock 테스트 스크립트

이 스크립트는 Ollama API 호출을 모킹하여 실제 Ollama 서버 없이도 
DesignerAgentOllama 클래스의 기능을 테스트합니다.
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# 현재 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.designer_agent_ollama import DesignerAgentOllama

class MockResponse:
    """Mock HTTP 응답 클래스"""
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception(f"HTTP 오류: {self.status_code}")

def mock_requests_get(*args, **kwargs):
    """requests.get 모킹 함수"""
    url = args[0]
    
    if "tags" in url:
        # Ollama 모델 목록 응답 모킹
        return MockResponse({
            "models": [
                {"name": "llama3:latest"},
                {"name": "codellama:latest"},
                {"name": "mistral:latest"}
            ]
        })
    
    return MockResponse({"error": "알 수 없는 URL"}, 404)

def mock_requests_post(*args, **kwargs):
    """requests.post 모킹 함수"""
    url = args[0]
    data = kwargs.get("json", {})
    
    if "generate" in url:
        prompt = data.get("prompt", "")
        model = data.get("model", "")
        system = data.get("system", "")
        
        # 프롬프트 기반 응답 생성
        if "wireframe" in prompt.lower() or "와이어프레임" in prompt.lower():
            response = """
# 로그인 화면 와이어프레임

## 1. 핵심 UI 요소 및 배치
- 상단: 로고 및 앱 이름 (중앙 정렬)
- 중앙: 
  - 사용자 이메일/아이디 입력 필드
  - 비밀번호 입력 필드 (마스킹 처리)
  - '로그인' 버튼 (너비 100%)
- 하단:
  - '비밀번호 찾기' 링크
  - '계정이 없으신가요? 회원가입' 링크
  - 소셜 로그인 옵션 (Google, Facebook, Apple)

## 2. 사용자 상호작용
- 입력 필드: 포커스 시 키보드 표시, 자동완성 지원
- 비밀번호 필드: 표시/숨김 토글 버튼
- 로그인 버튼: 탭 시 로딩 상태 표시 후 홈 화면으로 이동
- 회원가입/비밀번호 찾기: 탭 시 해당 화면으로 이동

## 3. 반응형 고려사항
- 모바일: 현재 레이아웃 유지 (세로 스택)
- 태블릿/데스크톱: 좌우 여백 증가, 중앙 컨테이너 최대 너비 제한

## 4. 레이아웃 구조
- 전체 배경: 단색 또는 그라데이션
- 입력 영역: 카드 형태로 구분 (선택적)
- 상단 여백: 로고에 충분한 공간 확보
- 요소 간 간격: 16-24px로 일관되게 유지
"""
        elif "component" in prompt.lower() or "컴포넌트" in prompt.lower() or "button" in prompt.lower():
            response = """
# 소셜 미디어 공유 버튼 컴포넌트

## 1. 컴포넌트 목적 및 사용 사례
- 사용자가 콘텐츠를 다양한 소셜 미디어 플랫폼(페이스북, 트위터, 인스타그램)에 공유할 수 있게 함
- 블로그 포스트, 제품 페이지, 이벤트 페이지 등 다양한 콘텐츠 페이지에서 사용 가능
- 각 플랫폼별 공유 기능에 빠르게 접근 가능하도록 시각적으로 구분된 버튼 제공

## 2. 시각적 디자인 특성
### 페이스북 버튼:
- 색상: #1877F2 (페이스북 브랜드 색상)
- 아이콘: 페이스북 'f' 로고
- 모양: 둥근 사각형 또는 원형

### 트위터 버튼:
- 색상: #1DA1F2 (트위터 브랜드 색상)
- 아이콘: 트위터 새 로고
- 모양: 페이스북 버튼과 일관된 형태

### 인스타그램 버튼:
- 색상: 그라데이션 #833AB4 → #FD1D1D → #FCAF45 (인스타그램 브랜드 색상)
- 아이콘: 인스타그램 카메라 로고
- 모양: 다른 버튼과 일관된 형태

## 3. 상태 및 변형
- 기본 상태: 불투명도 100%, 그림자 효과 약간
- 호버 상태: 밝기 증가 (10%), 그림자 강화
- 활성화(클릭) 상태: 약간 축소 효과, 그림자 감소
- 크기 변형: 작음(아이콘만), 중간(아이콘+텍스트), 큼(강조용)
- 레이아웃 변형: 수평 배치, 수직 배치, 그리드 배치

## 4. 스타일링 접근 방식
```jsx
// SocialShareButton.jsx
import React from 'react';
import './SocialShareButton.css';

const SocialShareButton = ({ platform, size = 'medium', onClick }) => {
  const getIcon = () => {
    switch (platform) {
      case 'facebook':
        return <i className="fab fa-facebook-f"></i>;
      case 'twitter':
        return <i className="fab fa-twitter"></i>;
      case 'instagram':
        return <i className="fab fa-instagram"></i>;
      default:
        return null;
    }
  };

  return (
    <button 
      className={`social-share-button ${platform} ${size}`}
      onClick={onClick}
      aria-label={`Share on ${platform}`}
    >
      {getIcon()}
      {size !== 'small' && <span>{platform}</span>}
    </button>
  );
};

export default SocialShareButton;
```

```css
/* SocialShareButton.css */
.social-share-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  margin: 0 8px;
  color: white;
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: pointer;
}

.social-share-button:hover {
  filter: brightness(1.1);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.social-share-button:active {
  transform: scale(0.98);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.social-share-button.facebook {
  background-color: #1877F2;
}

.social-share-button.twitter {
  background-color: #1DA1F2;
}

.social-share-button.instagram {
  background: linear-gradient(45deg, #833AB4, #FD1D1D, #FCAF45);
}

/* 크기 변형 */
.social-share-button.small {
  padding: 8px;
  border-radius: 50%;
}

.social-share-button.small i {
  margin: 0;
}

.social-share-button.medium {
  padding: 8px 16px;
}

.social-share-button.large {
  padding: 12px 24px;
  font-size: 1.1em;
}

.social-share-button i {
  margin-right: 8px;
}

.social-share-button.small i {
  margin-right: 0;
}
```
"""
        elif "system" in prompt.lower() or "시스템" in prompt.lower() or "theme" in prompt.lower():
            response = """
# 다크 모드 디자인 시스템

## colors.js
```javascript
// colors.js - 다크 모드 테마 색상 시스템
export const colors = {
  // 기본 색상
  primary: {
    main: '#6200EE',
    light: '#9E47FF',
    dark: '#4B01B3',
    contrastText: '#FFFFFF'
  },
  secondary: {
    main: '#03DAC6',
    light: '#70EFDE',
    dark: '#018786',
    contrastText: '#000000'
  },
  
  // 배경 색상 (다크 모드)
  background: {
    default: '#121212',
    paper: '#1E1E1E',
    elevation1: '#2D2D2D',
    elevation2: '#333333',
    elevation3: '#383838'
  },
  
  // 텍스트 색상
  text: {
    primary: '#FFFFFF',
    secondary: '#BBBBBB',
    disabled: '#777777',
    hint: '#999999'
  },
  
  // 상태 색상
  state: {
    success: '#4CAF50',
    warning: '#FF9800',
    error: '#F44336',
    info: '#2196F3'
  },
  
  // 그래디언트
  gradients: {
    primary: 'linear-gradient(45deg, #6200EE 30%, #9E47FF 90%)',
    secondary: 'linear-gradient(45deg, #03DAC6 30%, #70EFDE 90%)'
  },
  
  // 경계 및 분리선
  divider: 'rgba(255, 255, 255, 0.12)'
};

export default colors;
```

## typography.js
```javascript
// typography.js - 다크 모드 테마 타이포그래피 시스템
export const typography = {
  fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  
  // 폰트 가중치
  fontWeights: {
    light: 300,
    regular: 400,
    medium: 500,
    semiBold: 600,
    bold: 700
  },
  
  // 제목 스타일
  h1: {
    fontSize: '2.5rem',    // 40px
    lineHeight: 1.2,
    fontWeight: 700,
    letterSpacing: '-0.01562em',
    marginBottom: '0.5em'
  },
  h2: {
    fontSize: '2rem',      // 32px
    lineHeight: 1.3,
    fontWeight: 700,
    letterSpacing: '-0.00833em',
    marginBottom: '0.5em'
  },
  h3: {
    fontSize: '1.75rem',   // 28px
    lineHeight: 1.4,
    fontWeight: 600,
    letterSpacing: '0em',
    marginBottom: '0.5em'
  },
  h4: {
    fontSize: '1.5rem',    // 24px
    lineHeight: 1.4,
    fontWeight: 600,
    letterSpacing: '0.00735em',
    marginBottom: '0.5em'
  },
  h5: {
    fontSize: '1.25rem',   // 20px
    lineHeight: 1.5,
    fontWeight: 600,
    letterSpacing: '0em',
    marginBottom: '0.5em'
  },
  h6: {
    fontSize: '1rem',      // 16px
    lineHeight: 1.6,
    fontWeight: 600,
    letterSpacing: '0.0075em',
    marginBottom: '0.5em'
  },
  
  // 본문 스타일
  body1: {
    fontSize: '1rem',      // 16px
    lineHeight: 1.6,
    fontWeight: 400,
    letterSpacing: '0.00938em'
  },
  body2: {
    fontSize: '0.875rem',  // 14px
    lineHeight: 1.6,
    fontWeight: 400,
    letterSpacing: '0.01071em'
  },
  
  // 기타 스타일
  button: {
    fontSize: '0.875rem',  // 14px
    lineHeight: 1.75,
    fontWeight: 500,
    letterSpacing: '0.02857em',
    textTransform: 'uppercase'
  },
  caption: {
    fontSize: '0.75rem',   // 12px
    lineHeight: 1.66,
    fontWeight: 400,
    letterSpacing: '0.03333em'
  },
  overline: {
    fontSize: '0.75rem',   // 12px
    lineHeight: 2.66,
    fontWeight: 400,
    letterSpacing: '0.08333em',
    textTransform: 'uppercase'
  }
};

export default typography;
```

## spacing.js
```javascript
// spacing.js - 다크 모드 테마 간격 시스템
export const spacing = {
  // 기본 단위 (4px)
  unit: 4,
  
  // 명명된 간격 값
  xxs: 2,      // 8px
  xs: 4,       // 16px
  sm: 6,       // 24px
  md: 8,       // 32px
  lg: 12,      // 48px
  xl: 16,      // 64px
  xxl: 24,     // 96px
  
  // 함수형 간격 계산
  getValue: (multiplier) => `${multiplier * 4}px`,
  
  // 레이아웃 상수
  layout: {
    pageMargin: '24px',
    sectionGap: '48px',
    containerMaxWidth: '1200px',
    cardPadding: '24px',
    dialogPadding: '32px',
    formFieldGap: '16px'
  },
  
  // 컴포넌트별 간격
  components: {
    button: {
      paddingY: '8px',
      paddingX: '16px',
      spaceBetween: '8px'
    },
    input: {
      paddingY: '10px',
      paddingX: '14px'
    },
    card: {
      padding: '16px',
      borderRadius: '8px'
    },
    modal: {
      padding: '24px'
    }
  }
};

export default spacing;
```

이상의 파일들은 모던하고 일관된 다크 모드 디자인 시스템을 구성합니다. 이 시스템은 머티리얼 디자인의 원칙을 따르면서도 다크 모드에 최적화되어 있습니다. 색상은 눈의 피로를 줄이는 톤으로 구성되었으며, 타이포그래피와 간격은 가독성과 일관성을 보장합니다.
"""
        else:
            response = "디자인 작업 결과: 요청하신 디자인 작업이 완료되었습니다. 사용자 경험 향상을 위해 색상 대비, 접근성, 일관성을 모두 고려했습니다."
        
        return MockResponse({
            "model": model,
            "response": response,
            "done": True
        })
    
    return MockResponse({"error": "알 수 없는 URL"}, 404)

class TestDesignerAgentOllama(unittest.TestCase):
    """DesignerAgentOllama 테스트 클래스"""
    
    @patch('requests.get', side_effect=mock_requests_get)
    @patch('requests.post', side_effect=mock_requests_post)
    def setUp(self, mock_post, mock_get):
        """테스트 설정"""
        self.designer = DesignerAgentOllama(
            model="llama3:latest",
            api_base="http://localhost:11434/api"
        )
    
    @patch('requests.get', side_effect=mock_requests_get)
    @patch('requests.post', side_effect=mock_requests_post)
    def test_initialization(self, mock_post, mock_get):
        """초기화 테스트"""
        self.assertEqual(self.designer.name, "designer_agent_ollama")
        self.assertEqual(self.designer.model, "llama3:latest")
        self.assertIn("colors", self.designer.design_system)
        self.assertIn("typography", self.designer.design_system)
        self.assertIn("spacing", self.designer.design_system)
    
    @patch('requests.post', side_effect=mock_requests_post)
    def test_wireframe_generation(self, mock_post):
        """와이어프레임 생성 테스트"""
        task = {
            "description": "모바일 앱의 로그인 화면을 위한 와이어프레임을 만들어주세요.",
            "screen_name": "LoginScreen"
        }
        result = self.designer._generate_wireframe(task)
        self.assertIn("와이어프레임 설명", result)
        self.assertIn("LoginScreen", result)
        
        # run_task 테스트
        result = self.designer.run_task("로그인 화면을 위한 와이어프레임을 만들어주세요.")
        self.assertIn("와이어프레임", result)
    
    @patch('requests.post', side_effect=mock_requests_post)
    def test_component_design(self, mock_post):
        """컴포넌트 디자인 테스트"""
        task = {
            "description": "소셜 미디어 공유를 위한 버튼 컴포넌트를 디자인해주세요.",
            "component_type": "button",
            "component_name": "SocialShareButton"
        }
        result = self.designer._generate_component_design(task)
        self.assertIn("컴포넌트 디자인", result)
        self.assertIn("SocialShareButton", result)
    
    @patch('requests.post', side_effect=mock_requests_post)
    def test_design_system_generation(self, mock_post):
        """디자인 시스템 생성 테스트"""
        task = {
            "description": "다크 모드 테마의 모던한 디자인 시스템을 생성해주세요.",
            "output_dir": "app/config"
        }
        result = self.designer._generate_design_system(task)
        self.assertIn("디자인 시스템 생성 완료", result)
        self.assertIn("app/config", result)
    
    @patch('requests.post', side_effect=mock_requests_post)
    def test_helper_methods(self, mock_post):
        """헬퍼 메서드 테스트"""
        # generate_design 테스트
        component_requirements = {
            "primary": True,
            "size": "medium",
            "withIcon": True
        }
        design_data = self.designer.generate_design("button", component_requirements)
        self.assertEqual(design_data["type"], "button")
        self.assertIn("styles", design_data)
        
        # review_design 테스트
        review_result = self.designer.review_design(design_data)
        self.assertIn("original_design", review_result)
        self.assertIn("feedback", review_result)
        
        # create_design_system_files 테스트
        files = self.designer.create_design_system_files("app/theme")
        self.assertEqual(len(files), 3)
        self.assertIn("app/theme/colors.js", files)
        self.assertIn("app/theme/typography.js", files)
        self.assertIn("app/theme/spacing.js", files)

def print_test_results():
    """테스트 결과를 출력"""
    print("\n===== DesignerAgentOllama Mock 테스트 결과 =====")
    
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestDesignerAgentOllama)
    test_result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    print(f"\n테스트 요약:")
    print(f"- 실행된 테스트: {test_result.testsRun}")
    print(f"- 성공: {test_result.testsRun - len(test_result.errors) - len(test_result.failures)}")
    print(f"- 실패: {len(test_result.failures)}")
    print(f"- 오류: {len(test_result.errors)}")
    
    if test_result.wasSuccessful():
        print("\n✅ 모든 테스트 통과! DesignerAgentOllama가 정상적으로 작동합니다.")
    else:
        print("\n❌ 일부 테스트가 실패했습니다. 자세한 내용은 위 로그를 확인하세요.")

if __name__ == "__main__":
    print("DesignerAgentOllama Mock 테스트 시작...")
    print("(Ollama 서버 없이 모의 API 응답으로 테스트합니다)")
    print_test_results() 