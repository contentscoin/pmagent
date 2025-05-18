#!/bin/bash

# 변경 사항 추가 (수정된 파일, 삭제된 파일 모두 반영)
git add README.md
git add config.json
git add direct_client_test.js
git add package.json
git add register_smithery.js
git add smithery-simple.json
git add -u  # 삭제된 파일을 스테이징에 추가

# 커밋 및 푸시
git commit -m "refactor: 중복 설정 파일 통합 및 스크립트 정리"
git push origin main

echo "깃허브 푸시 완료"

# Koyeb 재배포 (Koyeb CLI가 설치되어 있다면)
if command -v koyeb &> /dev/null; then
    echo "Koyeb CLI 발견, 재배포 시도..."
    koyeb service redeploy pmagent
else 
    echo "Koyeb CLI가 설치되어 있지 않습니다. 깃허브에 푸시되었으므로 자동 배포가 진행될 것입니다."
fi

echo "프로세스 완료. 변경사항이 Koyeb에 적용되면 npm run smithery:register 명령을 실행하여 Smithery에 서버를 등록해주세요." 