#!/bin/bash

# 패키지를 개발자 모드로 설치
echo "PMAgent 패키지를 설치하는 중..."
pip install -e .

# 의존성이 없는 경우 설치
if [ $? -ne 0 ]; then
    echo "필수 의존성 설치 중..."
    pip install uvicorn fastapi pydantic aiohttp requests
    pip install -e .
fi

# 서버 실행
echo "PMAgent MCP 서버 실행 중..."
python -m pmagent.server 