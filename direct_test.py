#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
직접 TaskManager를 사용하는 테스트 스크립트
"""

import os
import json
from pmagent.task_manager import TaskManager

# TaskManager 인스턴스 생성
task_manager = TaskManager()

def create_request():
    """태스크 요청을 생성합니다."""
    print("===== 태스크 요청 생성 =====")
    
    try:
        # 요청 생성
        result = task_manager.request_planning(
            original_request="직접 호출 테스트 - 웹 애플리케이션 개발 프로젝트 계획",
            tasks=[
                {
                    "title": "요구사항 분석",
                    "description": "프로젝트 요구사항을 분석하고 기능 목록 작성"
                },
                {
                    "title": "디자인 시안 작성",
                    "description": "UI/UX 디자인 시안 작성 및 검토"
                }
            ]
        )
        
        print(f"결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def list_requests():
    """모든 요청을 조회합니다."""
    print("\n===== 요청 목록 조회 =====")
    
    try:
        # 요청 로드
        requests = task_manager.requests
        request_count = len(requests)
        print(f"요청 수: {request_count}")
        
        if request_count > 0:
            for request_id, request_info in requests.items():
                print(f"- 요청 ID: {request_id}")
                print(f"  원본 요청: {request_info['originalRequest']}")
                print(f"  상태: {request_info['status']}")
                print(f"  태스크 수: {len(request_info['tasks'])}")
                print()
        
        return requests
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def get_next_task(request_id):
    """다음 태스크를 가져옵니다."""
    print(f"\n===== 다음 태스크 가져오기 ({request_id}) =====")
    
    try:
        # 다음 태스크 가져오기
        task = task_manager.get_next_task(request_id)
        print(f"결과: {json.dumps(task, ensure_ascii=False, indent=2)}")
        return task
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    # 데이터 파일 확인
    data_dir = os.environ.get("DATA_DIR", "./data")
    requests_file = os.path.join(data_dir, "requests.json")
    tasks_file = os.path.join(data_dir, "tasks.json")
    
    print(f"요청 데이터 파일: {requests_file} (존재: {os.path.exists(requests_file)})")
    print(f"태스크 데이터 파일: {tasks_file} (존재: {os.path.exists(tasks_file)})")
    
    # 테스트 실행
    request_result = create_request()
    requests = list_requests()
    
    # 태스크 가져오기 테스트
    if request_result and "requestId" in request_result:
        get_next_task(request_result["requestId"]) 