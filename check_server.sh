#!/bin/bash

echo "서버 상태 확인 중..."
curl -s https://successive-glenn-contentscoin-34b6608c.koyeb.app/health

echo -e "\n\n도구 목록 확인 중..."
curl -s https://successive-glenn-contentscoin-34b6608c.koyeb.app/tools

echo -e "\n\n서버 정보 확인 중..."
curl -s https://successive-glenn-contentscoin-34b6608c.koyeb.app/smithery-simple.json 