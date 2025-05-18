#!/bin/bash

echo "Smithery 서버 설치 시도..."

# PMAgent 서버 설치
npx -y @smithery/cli@latest install @contentscoin/pmagent \
  --client cursor \
  --key 0c8f6386-e443-4b8b-95ba-22a40d5f5e38

# 등록 후 서버 목록 확인
echo -e "\n서버 목록 확인:"
npx -y @smithery/cli@latest list servers --client cursor

# 등록된 서버 검사
echo -e "\n등록된 서버 검사:"
npx -y @smithery/cli@latest inspect @contentscoin/pmagent --client cursor

echo -e "\n완료." 