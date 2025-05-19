#!/bin/bash

# Smithery 연결 설정 파일 수동 생성 스크립트

# 설정 값
PACKAGE_NAME="@contentscoin/pmagent"
SERVER_URL="https://successive-glenn-contentscoin-34b6608c.koyeb.app/mcp"
API_KEY="8220ee20-fe17-464b-b658-35113b05be41"

echo "========================================="
echo "Smithery 연결 설정 파일 생성 시작"
echo "패키지: $PACKAGE_NAME"
echo "서버 URL: $SERVER_URL"
echo "========================================="

# Smithery 디렉토리 생성 (없는 경우)
mkdir -p ~/.smithery
echo "Smithery 디렉토리 확인: ~/.smithery"

# 연결 설정 파일 생성
cat > ~/.smithery/connections.json << EOF
{
  "$PACKAGE_NAME": {
    "url": "$SERVER_URL",
    "apiKey": "$API_KEY"
  }
}
EOF

echo "연결 설정 파일 생성 완료: ~/.smithery/connections.json"
cat ~/.smithery/connections.json

echo ""
echo "파일 권한 설정..."
chmod 644 ~/.smithery/connections.json
ls -la ~/.smithery/connections.json

echo ""
echo "다음 명령어로 Smithery에 서버 등록을 시도하세요:"
echo "npx -y @smithery/cli@latest install $PACKAGE_NAME --url \"$SERVER_URL\" --apiKey \"$API_KEY\" --client cursor\"" 