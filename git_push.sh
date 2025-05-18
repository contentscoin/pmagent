#!/bin/bash

# 변경 사항 추가
git add pmagent/mcp_server.py 
git add .vercelignore
git rm vercel.json

# 커밋 및 푸시
git commit -m "feat: JSON-RPC 엔드포인트 로깅 개선 및 Vercel 설정 제거"
git push origin main

echo "깃허브 푸시 완료"

# Koyeb 재배포 (Koyeb CLI가 설치되어 있다면)
if command -v koyeb &> /dev/null; then
    echo "Koyeb CLI 발견, 재배포 시도..."
    koyeb service redeploy pmagent
else 
    echo "Koyeb CLI가 설치되어 있지 않습니다. 깃허브에 푸시되었으므로 자동 배포가 진행될 것입니다."
fi

echo "프로세스 완료. Smithery에서 서버를 재등록해주세요." 