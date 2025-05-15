#!/bin/bash

# 요청 목록 확인
echo "요청 목록 가져오기..."
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"name": "list_requests", "parameters": {"random_string": "abc"}}' \
  http://localhost:8086/mcp/invoke

# 새 요청 생성 (영문)
echo "새 요청 생성 (영문)..."
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"name": "request_planning", "parameters": {"originalRequest": "Web Application Development Project Plan", "tasks": [{"title": "Requirements Analysis", "description": "Analyze project requirements and create a feature list"}, {"title": "Design Draft", "description": "Create and review UI/UX design drafts"}]}}' \
  http://localhost:8086/mcp/invoke

# 새 요청 생성 (한글)
echo "새 요청 생성 (한글)..."
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"name": "request_planning", "parameters": {"originalRequest": "한글 웹 애플리케이션 개발 프로젝트 계획", "tasks": [{"title": "한글 요구사항 분석", "description": "프로젝트 요구사항을 분석하고 기능 목록 작성 (한글)"}, {"title": "한글 디자인 시안 작성", "description": "UI/UX 디자인 시안 작성 및 검토 (한글)"}]}}' \
  http://localhost:8086/mcp/invoke

# 다시 요청 목록 확인
echo "요청 목록 다시 확인..."
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"name": "list_requests", "parameters": {"random_string": "abc"}}' \
  http://localhost:8086/mcp/invoke 