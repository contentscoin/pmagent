#!/bin/bash

echo "기존 PMAgent 서버 제거 중..."
npx -y @smithery/cli@latest uninstall @contentscoin/pmagent --client cursor

echo -e "\nPMAgent 서버 재등록 중..."
npx -y @smithery/cli@latest register \
  --client cursor \
  --name "PMAgent" \
  --description "프로젝트 및 태스크 관리를 위한 MCP 서버" \
  --url "https://successive-glenn-contentscoin-34b6608c.koyeb.app" \
  --id "@contentscoin/pmagent" \
  --secret 0c8f6386-e443-4b8b-95ba-22a40d5f5e38

echo -e "\n서버 목록 확인:"
npx -y @smithery/cli@latest list servers --client cursor

echo -e "\n완료." 