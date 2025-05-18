#!/bin/bash

echo "기존 PMAgent 서버 제거 중..."
npx -y @smithery/cli@latest uninstall @contentscoin/pmagent --client cursor

echo -e "\nPMAgent 서버 재설치 중..."
npx -y @smithery/cli@latest install @contentscoin/pmagent \
  --client cursor \
  --key 0c8f6386-e443-4b8b-95ba-22a40d5f5e38

echo -e "\n서버 목록 확인:"
npx -y @smithery/cli@latest list servers --client cursor

echo -e "\n완료." 