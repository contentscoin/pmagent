# PMAgent 기여 가이드라인

PMAgent 프로젝트에 기여해 주셔서 감사합니다! 이 문서는 프로젝트에 기여하는 방법에 대한 가이드라인을 제공합니다.

## 기여 방법

PMAgent에 기여하는 방법은 여러 가지가 있습니다:

1. 코드 기여
2. 문서 개선
3. 버그 리포트 및 기능 요청
4. 코드 리뷰 및 피드백

## 개발 환경 설정

1. 저장소를 복제하세요:
   ```bash
   git clone https://github.com/contentscoin/pmagent.git
   cd pmagent
   ```

2. 가상 환경을 생성하고 활성화합니다:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. 필요한 패키지를 설치합니다:
   ```bash
   pip install -e ".[dev]"
   ```

## 코드 기여 프로세스

1. 이슈를 확인하거나 새 이슈를 생성합니다.
2. 저장소를 포크하고 새 브랜치를 생성합니다:
   ```bash
   git checkout -b feature/your-feature
   ```
3. 코드를 변경합니다.
4. 테스트를 실행하여 변경 사항이 기존 기능을 손상시키지 않는지 확인합니다:
   ```bash
   pytest
   ```
5. 코드 스타일을 확인합니다:
   ```bash
   flake8
   ```
6. 변경 내용을 커밋하고 푸시합니다:
   ```bash
   git commit -m "feat: 기능 설명"
   git push origin feature/your-feature
   ```
7. Pull Request를 생성합니다.

## 코딩 스타일

- [PEP 8](https://www.python.org/dev/peps/pep-0008/) 스타일 가이드를 따릅니다.
- 클래스, 메서드, 함수에 대해 문서 문자열(docstrings)을 작성합니다.
- 복잡한 코드에는 주석을 추가합니다.
- 변수와 함수 이름은 직관적이고 의미 있게 작성합니다.

## 커밋 메시지 가이드라인

커밋 메시지는 다음과 같은 형식을 따릅니다:

```
<유형>: <설명>

[선택적 본문]

[선택적 꼬리말]
```

유형은 다음 중 하나여야 합니다:
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 형식 변경(코드 작동에 영향을 주지 않는 변경)
- `refactor`: 리팩토링
- `test`: 테스트 추가 또는 수정
- `chore`: 빌드 프로세스 또는 도구 변경

예:
```
feat: 프로젝트 필터링 기능 추가

프로젝트를 상태, 생성일, 담당자별로 필터링할 수 있는 기능을 추가했습니다.

Closes #123
```

## 테스트

모든 새 기능에는 테스트가 포함되어야 합니다. 테스트는 `tests/` 디렉토리에 있습니다.

## 문서화

코드를 변경할 때 관련 문서도 업데이트해 주세요. 특히:
- API 변경 시 문서 문자열(docstrings) 업데이트
- 새 기능 추가 시 README.md 또는 docs/ 디렉토리의 문서 업데이트
- 주요 변경 사항은 CHANGELOG.md에 기록

## 질문이 있으신가요?

질문이나 도움이 필요하시면 저장소의 이슈를 통해 문의해 주세요.

감사합니다! 