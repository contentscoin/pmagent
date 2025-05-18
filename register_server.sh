#!/bin/bash

# 쉘 스크립트로 직접 Smithery에 서버 등록 (Cursor 클라이언트 없음)

# 설정값
PACKAGE_NAME="@contentscoin/pmagent"
SERVER_URL="https://successive-glenn-contentscoin-34b6608c.koyeb.app/mcp"
API_KEY="8220ee20-fe17-464b-b658-35113b05be41"

echo "========================================="
echo "Smithery 서버 등록 시작 (Cursor 통합 없음)"
echo "패키지: $PACKAGE_NAME"
echo "서버 URL: $SERVER_URL"
echo "========================================="

# Smithery 디렉토리 없으면 생성
mkdir -p ~/.smithery

# 연결 설정 파일 생성
cat > ~/.smithery/connections.json << EOF
{
  "$PACKAGE_NAME": {
    "url": "$SERVER_URL",
    "apiKey": "$API_KEY"
  }
}
EOF

echo "연결 설정 파일 생성: ~/.smithery/connections.json"

# 서버 등록 시도
echo "서버 등록 시도중..."

# 첫 번째 시도 - apiKey 사용
echo "방법 1: apiKey 사용"
if npx -y @smithery/cli@latest install $PACKAGE_NAME --url "$SERVER_URL" --apiKey "$API_KEY" --client cursor; then
  echo "✅ 서버 등록 성공!"
  npx -y @smithery/cli@latest list servers
  exit 0
fi

# 두 번째 시도 - api-key 사용
echo "방법 2: api-key 사용"
if npx -y @smithery/cli@latest install $PACKAGE_NAME --url "$SERVER_URL" --api-key "$API_KEY" --client cursor; then
  echo "✅ 서버 등록 성공!"
  npx -y @smithery/cli@latest list servers
  exit 0
fi

# 세 번째 시도 - key 사용
echo "방법 3: key 사용"
if npx -y @smithery/cli@latest install $PACKAGE_NAME --url "$SERVER_URL" --key "$API_KEY" --client cursor; then
  echo "✅ 서버 등록 성공!"
  npx -y @smithery/cli@latest list servers
  exit 0
fi

# 네 번째 시도 - URL만 사용
echo "방법 4: URL만 사용"
if npx -y @smithery/cli@latest install $PACKAGE_NAME --url "$SERVER_URL" --client cursor; then
  echo "✅ 서버 등록 성공!"
  npx -y @smithery/cli@latest list servers
  exit 0
fi

echo "❌ 모든 등록 시도가 실패했습니다."
echo ""
echo "수동 설치 방법:"
echo "새 터미널 창을 열고 다음 명령을 직접 실행하세요:"
echo "npx -y @smithery/cli@latest install $PACKAGE_NAME --url \"$SERVER_URL\" --apiKey \"$API_KEY\" --client cursor"

exit 1 