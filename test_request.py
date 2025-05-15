#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP 서버 API 테스트 Python 스크립트

requests 라이브러리를 사용하여 직접 API를 호출합니다.
"""

import requests
import json
import sys
import uuid # 테스트용 agent ID 생성에 사용 가능

# 서버 URL
# SERVER_URL = "http://localhost:8086/mcp/invoke" # 이전 설정
SERVER_URL_MCP_INVOKE = "http://localhost:8082/mcp/invoke" # 수정된 포트 및 경로
SERVER_URL_ROOT = "http://localhost:8082/" # 수정된 포트

def call_mcp_tool(tool_name: str, params: dict) -> dict:
    """지정된 MCP 도구를 호출하고 결과를 반환합니다."""
    payload = {
        "name": tool_name,
        "parameters": params
    }
    headers = {"Content-Type": "application/json"}
    
    print(f"\n===== 호출: {tool_name} =====")
    print(f"요청 페이로드: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(SERVER_URL_MCP_INVOKE, headers=headers, json=payload, timeout=10) 
        response.raise_for_status() 
        result = response.json()
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 JSON: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 오류 발생 ({tool_name}): {http_err}")
        print(f"응답 내용: {response.text}")
        return {"success": False, "error": str(http_err), "raw_response": response.text}
    except requests.exceptions.RequestException as e:
        print(f"요청 오류 발생 ({tool_name}): {e}")
        return {"success": False, "error": str(e)}
    except json.JSONDecodeError:
        print(f"JSON 디코딩 오류 ({tool_name}): 서버 응답이 유효한 JSON이 아닙니다.")
        print(f"Raw Response: {response.text}")
        return {"success": False, "error": "Invalid JSON response from server."}

def run_tests():
    """테스트 절차를 실행합니다."""
    
    test_request_id = None
    test_task_id_agent1 = None # agent1에게 할당될 태스크 ID
    test_task_id_agent2 = None # agent2에게 할당될 태스크 ID

    # 테스트용 에이전트 ID
    agent_id_1 = "test-agent-001"
    agent_id_2 = "test-agent-002"

    # 0. 모든 데이터 초기화 (테스트 환경 일관성 유지)
    print("\n--- 0. 모든 데이터 초기화 시작 ---")
    clear_params = {"confirmation": "CLEAR_ALL_MY_DATA"}
    clear_result = call_mcp_tool("clear_all_data", clear_params)
    assert clear_result.get("success") is True, "데이터 초기화 실패"
    print("--- 0. 모든 데이터 초기화 완료 ---")

    # 1. 초기 요청 목록 확인
    print("\n--- 1. 초기 요청 목록 확인 ---")
    list_params_initial = {"random_string": "initial_list"} # random_string은 이제 필수
    initial_list = call_mcp_tool("list_requests", list_params_initial)
    assert initial_list.get("success") is True, "초기 요청 목록 조회 실패"
    assert len(initial_list.get("requests", [])) == 0, "초기 요청 목록이 비어있지 않음"
    print("--- 1. 초기 요청 목록 확인 완료 ---")

    # 2. 새 요청 생성 (2개의 태스크 포함)
    print("\n--- 2. 새 요청 생성 ---")
    planning_params = {
        "originalRequest": "Agent Assignment Test Project (Python Test)",
        "tasks": [
            {"title": "Task 1 for Agent Assignment", "description": "This is the first task.", "assignee_candidate": agent_id_1},
            {"title": "Task 2 for Agent Assignment", "description": "This is the second task.", "assignee_candidate": agent_id_2},
            {"title": "Task 3 - Unassigned", "description": "This task should remain pending initially."}
        ]
    }
    planning_result = call_mcp_tool("request_planning", planning_params)
    assert planning_result.get("success") is True, "요청 생성 실패"
    test_request_id = planning_result.get("requestId")
    assert test_request_id is not None, "요청 ID가 반환되지 않음"
    print(f"생성된 요청 ID: {test_request_id}")
    print("--- 2. 새 요청 생성 완료 ---")

    # 3. 요청 목록 확인 (요청 1개, 태스크 3개 - 할당 0, 완료 0)
    print("\n--- 3. 요청 생성 후 요청 목록 확인 ---")
    list_after_planning = call_mcp_tool("list_requests", {"random_string": "after_planning"})
    assert list_after_planning.get("success") is True, "요청 목록 조회 실패"
    assert len(list_after_planning.get("requests", [])) == 1, "요청 개수 불일치"
    req_summary = list_after_planning["requests"][0]
    assert req_summary["id"] == test_request_id
    assert req_summary["totalTasks"] == 3
    assert req_summary.get("assignedTasks", 0) == 0 # mcp_agent_api.py의 list_requests가 이 필드를 반환해야 함
    assert req_summary["doneTasks"] == 0
    print("--- 3. 요청 목록 확인 완료 ---")

    # 4. Agent 1이 다음 작업 가져오기 시도
    print(f"\n--- 4. Agent {agent_id_1} 작업 할당 시도 ---")
    get_task_params_agent1 = {"requestId": test_request_id, "agentId": agent_id_1}
    task_for_agent1_result = call_mcp_tool("get_next_task", get_task_params_agent1)
    assert task_for_agent1_result.get("success") is True, f"Agent {agent_id_1} 작업 할당 실패"
    assert task_for_agent1_result.get("hasNextTask") is True, f"Agent {agent_id_1}에게 할당된 작업이 없음"
    task_data_agent1 = task_for_agent1_result.get("task")
    assert task_data_agent1 is not None, "할당된 태스크 데이터가 없음 (Agent 1)"
    test_task_id_agent1 = task_data_agent1.get("id")
    assert test_task_id_agent1 is not None, "할당된 태스크 ID가 없음 (Agent 1)"
    assert task_data_agent1.get("assignedAgentId") == agent_id_1, f"태스크가 Agent {agent_id_1}에게 할당되지 않음"
    assert task_data_agent1.get("status") == "ASSIGNED", "할당된 태스크의 상태가 ASSIGNED가 아님"
    print(f"Agent {agent_id_1}에게 태스크 {test_task_id_agent1} 할당됨: {task_data_agent1.get('title')}")
    print("--- 4. Agent 1 작업 할당 완료 ---")

    # 5. 요청 목록 확인 (태스크 3개 - 할당 1, 완료 0)
    print("\n--- 5. Agent 1 작업 할당 후 요청 목록 확인 ---")
    list_after_assign_agent1 = call_mcp_tool("list_requests", {"random_string": "after_assign_agent1"})
    assert list_after_assign_agent1.get("success") is True
    req_summary_agent1 = list_after_assign_agent1["requests"][0]
    assert req_summary_agent1["totalTasks"] == 3
    # TaskManager의 list_requests가 assignedTasks를 반환하도록 수정되었는지 확인 필요
    # 현재 mcp_agent_api.py의 _mcp_list_requests는 task_manager.list_requests()를 호출하고, 이는 assignedTasks를 포함함.
    assert req_summary_agent1.get("assignedTasks", -1) == 1, f"할당된 태스크 수 불일치: {req_summary_agent1.get('assignedTasks')}"
    assert req_summary_agent1["doneTasks"] == 0
    print("--- 5. 요청 목록 확인 완료 ---")

    # 6. Agent 2가 다음 작업 가져오기 시도 (다른 작업이 할당되어야 함)
    print(f"\n--- 6. Agent {agent_id_2} 작업 할당 시도 ---")
    get_task_params_agent2 = {"requestId": test_request_id, "agentId": agent_id_2}
    task_for_agent2_result = call_mcp_tool("get_next_task", get_task_params_agent2)
    assert task_for_agent2_result.get("success") is True, f"Agent {agent_id_2} 작업 할당 실패"
    assert task_for_agent2_result.get("hasNextTask") is True, f"Agent {agent_id_2}에게 할당된 작업이 없음"
    task_data_agent2 = task_for_agent2_result.get("task")
    assert task_data_agent2 is not None, "할당된 태스크 데이터가 없음 (Agent 2)"
    test_task_id_agent2 = task_data_agent2.get("id")
    assert test_task_id_agent2 is not None, "할당된 태스크 ID가 없음 (Agent 2)"
    assert test_task_id_agent2 != test_task_id_agent1, "Agent 1과 Agent 2에게 동일한 태스크가 할당됨"
    assert task_data_agent2.get("assignedAgentId") == agent_id_2, f"태스크가 Agent {agent_id_2}에게 할당되지 않음"
    assert task_data_agent2.get("status") == "ASSIGNED", "할당된 태스크의 상태가 ASSIGNED가 아님 (Agent 2)"
    print(f"Agent {agent_id_2}에게 태스크 {test_task_id_agent2} 할당됨: {task_data_agent2.get('title')}")
    print("--- 6. Agent 2 작업 할당 완료 ---")

    # 7. 요청 목록 확인 (태스크 3개 - 할당 2, 완료 0)
    print("\n--- 7. Agent 2 작업 할당 후 요청 목록 확인 ---")
    list_after_assign_agent2 = call_mcp_tool("list_requests", {"random_string": "after_assign_agent2"})
    assert list_after_assign_agent2.get("success") is True
    req_summary_agent2 = list_after_assign_agent2["requests"][0]
    assert req_summary_agent2["totalTasks"] == 3
    assert req_summary_agent2.get("assignedTasks", -1) == 2, f"할당된 태스크 수 불일치: {req_summary_agent2.get('assignedTasks')}"
    assert req_summary_agent2["doneTasks"] == 0
    print("--- 7. 요청 목록 확인 완료 ---")

    # 8. Agent 1이 할당받은 작업 완료 처리
    print(f"\n--- 8. Agent {agent_id_1}이 태스크 {test_task_id_agent1} 완료 시도 ---")
    mark_done_params_agent1 = {
        "requestId": test_request_id, 
        "taskId": test_task_id_agent1, 
        "agentId": agent_id_1, # mark_task_done에 agentId 파라미터 추가 필요 (mcp_server.py, mcp_agent_api.py)
        "completedDetails": f"Task {test_task_id_agent1} completed by {agent_id_1}"
    }
    # 중요: mark_task_done 도구 정의 및 래퍼 함수에 agentId를 추가해야 이 테스트가 통과함
    # 현재 mcp_server.py의 mark_task_done 래퍼는 agentId를 받지 않음.
    # mcp_agent_api.py의 _mcp_mark_task_done도 agentId를 받도록 수정 필요. (TaskManager는 이미 받음)
    # 이 부분을 수정하지 않으면 이 테스트는 실패할 것임.
    # 우선, mcp_server.py와 mcp_agent_api.py를 수정했다고 가정하고 진행.
    # TODO: 실제 실행 전 mcp_server.py와 mcp_agent_api.py의 mark_task_done에 agentId 파라미터 추가 필요
    
    # `mark_task_done` 도구 정의에 `agentId`를 추가하고 해당 MCP 함수들이 `agentId`를 사용하도록 수정 필요
    # 이 스크립트에서는 해당 수정이 선행되었다고 가정.
    done_result_agent1 = call_mcp_tool("mark_task_done", mark_done_params_agent1)
    assert done_result_agent1.get("success") is True, f"Agent {agent_id_1} 작업 완료 실패: {done_result_agent1.get('error')}"
    assert done_result_agent1.get("task", {}).get("status") == "DONE", "완료된 태스크의 상태가 DONE이 아님"
    print(f"Agent {agent_id_1}에 의해 태스크 {test_task_id_agent1} 완료됨")
    print("--- 8. Agent 1 작업 완료 처리 완료 ---")

    # 9. 요청 목록 확인 (태스크 3개 - 할당 1, 완료 1)
    print("\n--- 9. Agent 1 작업 완료 후 요청 목록 확인 ---")
    list_after_done_agent1 = call_mcp_tool("list_requests", {"random_string": "after_done_agent1"})
    assert list_after_done_agent1.get("success") is True
    req_summary_done1 = list_after_done_agent1["requests"][0]
    assert req_summary_done1["totalTasks"] == 3
    assert req_summary_done1.get("assignedTasks", -1) == 1, f"할당된 태스크 수 불일치 (1 완료 후): {req_summary_done1.get('assignedTasks')}"
    assert req_summary_done1["doneTasks"] == 1
    print("--- 9. 요청 목록 확인 완료 ---")

    # 10. Agent 2가 Agent 1의 완료된 작업을 다시 완료 시도 (실패해야 함 - 다른 에이전트의 작업 시도)
    print(f"\n--- 10. Agent {agent_id_2}이 이미 완료된 태스크 {test_task_id_agent1} 완료 시도 ---")
    mark_done_params_agent2_on_done_task = {
        "requestId": test_request_id, 
        "taskId": test_task_id_agent1, # Agent 1이 완료한 태스크
        "agentId": agent_id_2,
        "completedDetails": "Attempting to re-complete other agent\'s done task."
    }
    done_again_result = call_mcp_tool("mark_task_done", mark_done_params_agent2_on_done_task)
    # 다른 에이전트가 완료 시도하므로 success: False가 기대됨
    assert done_again_result.get("success") is False, "다른 에이전트가 이미 완료된 태스크 완료 시도시 success가 False여야 함"
    # 메시지는 할당된 에이전트가 아니라는 내용이어야 함
    expected_message_fragment = f"assigned to agent {agent_id_1}, not {agent_id_2}".lower()
    actual_message = (done_again_result.get("message", "") or done_again_result.get("error", "")).lower()
    assert expected_message_fragment in actual_message, \
        f"다른 에이전트가 완료된 태스크 재완료 시도 시 메시지 불일치: 기대 프래그먼트='{expected_message_fragment}', 실제 메시지='{actual_message}'"
    print("--- 10. 다른 에이전트가 완료된 태스크 재완료 시도 완료 (예상된 실패) ---")

    # 11. Agent 1이 Agent 2에게 할당된 작업을 완료 시도 (실패해야 함)
    print(f"\n--- 11. Agent {agent_id_1}이 Agent {agent_id_2}의 태스크 {test_task_id_agent2} 완료 시도 ---")
    mark_done_params_agent1_on_agent2_task = {
        "requestId": test_request_id, 
        "taskId": test_task_id_agent2, # Agent 2에게 할당된 태스크
        "agentId": agent_id_1, 
        "completedDetails": "Attempting to complete other agent's task."
    }
    wrong_agent_done_result = call_mcp_tool("mark_task_done", mark_done_params_agent1_on_agent2_task)
    assert wrong_agent_done_result.get("success") is False, "다른 에이전트의 작업 완료 시도가 성공함"
    assert "not assigned to agent" not in wrong_agent_done_result.get("error", "").lower() # 이 메시지는 할당되지 않았을 때
    assert f"assigned to agent {agent_id_2}, not {agent_id_1}" in wrong_agent_done_result.get("message", "").lower() or \
           f"is assigned to agent {agent_id_2}, not {agent_id_1}" in wrong_agent_done_result.get("error", "").lower(), \
           f"잘못된 에이전트가 작업 완료 시도 시 메시지 불일치: {wrong_agent_done_result.get('error') or wrong_agent_done_result.get('message')}"
    print("--- 11. 다른 에이전트 작업 완료 시도 완료 (예상된 실패) ---")

    # 12. 남은 작업 (Task 3) 할당 시도 (Agent 1 또는 2)
    print(f"\n--- 12. 남은 작업(Task 3) 할당 시도 (Agent {agent_id_1}) ---")
    task_for_agent1_again_result = call_mcp_tool("get_next_task", get_task_params_agent1)
    assert task_for_agent1_again_result.get("success") is True
    if task_for_agent1_again_result.get("hasNextTask") is True:
        task_data_agent1_again = task_for_agent1_again_result.get("task")
        assert task_data_agent1_again is not None
        assert task_data_agent1_again.get("id") not in [test_task_id_agent1, test_task_id_agent2]
        assert task_data_agent1_again.get("assignedAgentId") == agent_id_1
        print(f"Agent {agent_id_1}에게 추가 태스크 {task_data_agent1_again.get('id')} 할당됨: {task_data_agent1_again.get('title')}")
        # 이 작업도 완료 처리 (간단히)
        call_mcp_tool("mark_task_done", {"requestId": test_request_id, "taskId": task_data_agent1_again.get("id"), "agentId": agent_id_1, "completedDetails": "Task 3 done"})
    else:
        print(f"Agent {agent_id_1}에게 더 이상 할당할 작업 없음.")
    print("--- 12. 남은 작업 할당 시도 완료 ---")
    
    # 13. 모든 작업이 할당/완료된 후 다음 작업 가져오기 시도 (hasNextTask: False 예상)
    print(f"\n--- 13. 모든 작업 소진 후 Agent {agent_id_2}가 작업 할당 시도 ---")
    # Agent2의 원래 작업(test_task_id_agent2)도 완료시켜야 모든 작업이 소진됨
    call_mcp_tool("mark_task_done", {"requestId": test_request_id, "taskId": test_task_id_agent2, "agentId": agent_id_2, "completedDetails": "Task 2 done by agent 2"})
    
    final_get_task_result = call_mcp_tool("get_next_task", get_task_params_agent2)
    assert final_get_task_result.get("success") is True
    assert final_get_task_result.get("hasNextTask") is False, "모든 작업 소진 후에도 작업이 있다고 나옴"
    assert "No assignable task found" in final_get_task_result.get("message", ""), "모든 작업 소진 후 메시지 불일치"
    print("--- 13. 모든 작업 소진 후 작업 할당 시도 완료 (예상된 결과) ---")

    print("\n===== 모든 테스트 통과! =====")

if __name__ == "__main__":
    try:
        # 서버 URL 변경에 따라 루트 경로 대신 /mcp/tools 로 확인
        # response = requests.get(SERVER_URL_ROOT, timeout=3)
        health_check_url = SERVER_URL_ROOT + "mcp/tools" 
        response = requests.get(health_check_url, timeout=3)
        response.raise_for_status()
        print(f"서버 ({health_check_url}) 연결 확인됨. 테스트를 시작합니다...")
        run_tests()
    except requests.exceptions.ConnectionError:
        print(f"오류: 서버({SERVER_URL_ROOT})에 연결할 수 없습니다. PMAgent 서버 (mcp_agent_api.py)가 {SERVER_URL_ROOT}에서 실행 중인지 확인하세요.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"오류: 서버({SERVER_URL_ROOT}) 연결 시간 초과.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"오류: 서버({SERVER_URL_ROOT})가 실행 중이지만 오류 응답: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        sys.exit(1) 