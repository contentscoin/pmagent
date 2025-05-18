#!/bin/bash

# smithery_install.sh - PMAgent 스미더리 설치 스크립트
# 터미널에서 직접 실행할 수 있는 간단한 스크립트입니다.

# 설정 정보
PACKAGE_NAME="@contentscoin/pmagent"
SERVER_URL="https://successive-glenn-contentscoin-34b6608c.koyeb.app/mcp"
API_KEY="0c8f6386-e443-4b8b-95ba-22a40d5f5e38"

echo "Smithery 등록 시작..."
echo "패키지: $PACKAGE_NAME"
echo "URL: $SERVER_URL"
echo "API 키: ${API_KEY:0:8}..."

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

echo "연결 설정 파일 생성: $CONNECTION_FILE"

# 스미더리 설치
echo "스미더리 서버 등록 중..."

# 여러 옵션으로 시도
echo "방법 1: URL과 apiKey 명시"
npx -y @smithery/cli@latest install $PACKAGE_NAME --url "$SERVER_URL" --apiKey "$API_KEY" --client cursor || {
  echo "방법 1 실패, 방법 2 시도: URL과 api-key 명시"
  npx -y @smithery/cli@latest install $PACKAGE_NAME --url "$SERVER_URL" --api-key "$API_KEY" --client cursor || {
    echo "방법 2 실패, 방법 3 시도: 기본 명령"
    npx -y @smithery/cli@latest install $PACKAGE_NAME --client cursor || {
      echo "모든 방법 실패. 수동으로 다음 명령을 시도해보세요:"
      echo "npx -y @smithery/cli@latest install $PACKAGE_NAME --url \"$SERVER_URL\" --apiKey \"$API_KEY\" --client cursor"
      exit 1
    }
  }
}

echo "등록된 서버 목록 확인:"
npx -y @smithery/cli@latest list servers --client cursor

echo "모든 과정이 완료되었습니다. Cursor를 재시작하여 설정을 적용하세요." 