#!/bin/bash

echo "Smithery 서버 등록 시도..."

# PMAgent 서버 등록
npx -y @smithery/cli@latest register \
  --client cursor \
  --name "PMAgent" \
  --description "프로젝트 및 태스크 관리를 위한 MCP 서버" \
  --url "https://successive-glenn-contentscoin-34b6608c.koyeb.app" \
  --id "@contentscoin/pmagent" \
  --secret 0c8f6386-e443-4b8b-95ba-22a40d5f5e38

# 등록 후 서버 목록 확인
echo -e "\n서버 목록 확인:"
npx -y @smithery/cli@latest list servers --client cursor

# 등록된 서버 검사
echo -e "\n등록된 서버 검사:"
npx -y @smithery/cli@latest inspect @contentscoin/pmagent --client cursor

echo -e "\n완료." 