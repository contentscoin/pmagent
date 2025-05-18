#!/bin/bash

# smithery_install.sh - PMAgent 스미더리 설치 스크립트
# 터미널에서 직접 실행할 수 있는 간단한 스크립트입니다.

set -e # 오류 발생 시 스크립트 종료

# 설정 정보
PACKAGE_NAME="@contentscoin/pmagent"
SERVER_URL="https://successive-glenn-contentscoin-34b6608c.koyeb.app/mcp"
API_KEY="8220ee20-fe17-464b-b658-35113b05be41"

echo "========================================"
echo "PMAgent Smithery 설치 시작"
echo "패키지: $PACKAGE_NAME"
echo "서버 URL: $SERVER_URL"
echo "========================================"

# 연결 설정 파일 생성
SMITHERY_DIR="$HOME/.smithery"
CONNECTION_FILE="$SMITHERY_DIR/connections.json"

# 디렉토리 없으면 생성
mkdir -p "$SMITHERY_DIR"

# connections.json 파일 생성
echo "{
  \"$PACKAGE_NAME\": {
    \"url\": \"$SERVER_URL\",
    \"apiKey\": \"$API_KEY\"
  }
}" > "$CONNECTION_FILE"

echo "연결 설정 파일 생성됨: $CONNECTION_FILE"

# 스미더리 설치
echo "스미더리 서버 등록 중..."

# 첫 번째 설치 시도 - apiKey 파라미터 사용
echo "첫 번째 설치 시도 - apiKey 파라미터 사용..."
if npx -y @smithery/cli@latest install "$PACKAGE_NAME" --url "$SERVER_URL" --apiKey "$API_KEY" --client cursor; then
    echo "✅ 설치 성공!"
    exit 0
fi

# 두 번째 설치 시도 - api-key 파라미터 사용
echo "두 번째 설치 시도 - api-key 파라미터 사용..."
if npx -y @smithery/cli@latest install "$PACKAGE_NAME" --url "$SERVER_URL" --api-key "$API_KEY" --client cursor; then
    echo "✅ 설치 성공!"
    exit 0
fi

# 세 번째 설치 시도 - key 파라미터 사용
echo "세 번째 설치 시도 - key 파라미터 사용..."
if npx -y @smithery/cli@latest install "$PACKAGE_NAME" --url "$SERVER_URL" --key "$API_KEY" --client cursor; then
    echo "✅ 설치 성공!"
    exit 0
fi

# 네 번째 설치 시도 - URL만 사용
echo "네 번째 설치 시도 - URL만 사용..."
if npx -y @smithery/cli@latest install "$PACKAGE_NAME" --url "$SERVER_URL" --client cursor; then
    echo "✅ 설치 성공!"
    exit 0
fi

echo "❌ 모든 설치 시도가 실패했습니다."
echo "수동으로 설치하려면 다음 명령어를 복사하여 실행하세요:"
echo "npx -y @smithery/cli@latest install $PACKAGE_NAME --url \"$SERVER_URL\" --apiKey \"$API_KEY\" --client cursor"

exit 1

echo "등록된 서버 목록 확인:"
npx -y @smithery/cli@latest list servers --client cursor

echo "모든 과정이 완료되었습니다. Cursor를 재시작하여 설정을 적용하세요." 