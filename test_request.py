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
import logging

# 로깅 기본 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 서버 URL
# SERVER_URL = "http://localhost:8086/mcp/invoke" # 이전 설정
SERVER_URL_MCP_INVOKE = "http://localhost:4000/invoke" # 수정된 포트 및 /mcp prefix 제거
SERVER_URL_ROOT = "http://localhost:4000/" # 수정된 포트

# TaskManager에서 사용하는 상태 상수 (테스트에서 직접 비교용)
TASK_STATUS_PENDING = "PENDING"
TASK_STATUS_ASSIGNED = "ASSIGNED"
TASK_STATUS_DONE = "DONE"
TASK_STATUS_APPROVED = "APPROVED"

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
        # raise_for_status()를 호출하면 4xx, 5xx 응답 시 바로 예외 발생
        response.raise_for_status() 
        result = response.json() # 성공적인 응답 (2xx)만 여기에 도달
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 JSON: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result # 예: {"result": {"actual_tool_response"}}
    except requests.exceptions.HTTPError as http_err:
        # print(f"HTTP 오류 발생 ({tool_name}): {http_err}") # logger로 대체
        # print(f"응답 내용: {response.text}") # logger로 대체
        logger.error(f"HTTP 오류 발생 ({tool_name}): {http_err}", exc_info=True)
        logger.error(f"응답 내용: {response.text}")
        # HTTP 오류 시, 서버가 보낸 JSON 오류 메시지를 포함할 수 있도록 raw_response 저장
        return {"success": False, "error_type": "HTTPError", "status_code": response.status_code, "error": str(http_err), "raw_response": response.text}
    except requests.exceptions.RequestException as e:
        # print(f"요청 오류 발생 ({tool_name}): {e}") # logger로 대체
        logger.error(f"요청 오류 발생 ({tool_name}): {e}", exc_info=True)
        return {"success": False, "error_type": "RequestException", "error": str(e)}
    except json.JSONDecodeError:
        # print(f"JSON 디코딩 오류 ({tool_name}): 서버 응답이 유효한 JSON이 아닙니다.") # logger로 대체
        # print(f"Raw Response: {response.text}") # logger로 대체
        logger.error(f"JSON 디코딩 오류 ({tool_name}): 서버 응답이 유효한 JSON이 아닙니다. Raw Response: {response.text}", exc_info=True)
        return {"success": False, "error_type": "JSONDecodeError", "error": "Invalid JSON response from server.", "raw_response": response.text}

def get_error_detail_from_raw_response(raw_response_text: str) -> str:
    """HTTP 오류 응답 텍스트에서 'detail' 메시지를 추출합니다."""
    try:
        return json.loads(raw_response_text).get("detail", raw_response_text)
    except json.JSONDecodeError:
        return raw_response_text

def run_tests():
    """테스트 절차를 실행합니다."""
    
    test_request_id = None
    test_task_id_agent1 = None
    test_task_id_agent2 = None
    unassigned_task_id = None # 할당되지 않은 작업을 테스트하기 위한 ID

    agent_id_1 = "test-agent-001"
    agent_id_2 = "test-agent-002"

    # 0. 모든 데이터 초기화
    # print("\n--- 0. 모든 데이터 초기화 시작 ---") # logger로 대체
    logger.info("\n--- 0. 모든 데이터 초기화 시작 ---")
    clear_params = {"confirmation": "CLEAR_ALL_MY_DATA"}
    clear_response = call_mcp_tool("clear_all_data", clear_params)
    assert "result" in clear_response and clear_response["result"].get("success") is True, f"데이터 초기화 실패: {clear_response}"
    # print("--- 0. 모든 데이터 초기화 완료 ---") # logger로 대체
    logger.info("--- 0. 모든 데이터 초기화 완료 ---")

    # 1. 초기 요청 목록 확인
    # print("\n--- 1. 초기 요청 목록 확인 ---") # logger로 대체
    logger.info("\n--- 1. 초기 요청 목록 확인 ---")
    # list_requests는 이제 파라미터를 받지 않음 (mcp_server.py의 list_requests 핸들러 수정됨)
    initial_list_response = call_mcp_tool("list_requests", {}) 
    assert "result" in initial_list_response, f"초기 요청 목록 조회 실패 (result 키 없음): {initial_list_response}"
    initial_list_data = initial_list_response["result"]
    assert "requests" in initial_list_data, f"초기 요청 목록 조회 실패 (requests 키 없음): {initial_list_data}"
    assert len(initial_list_data.get("requests", [])) == 0, f"초기 요청 목록이 비어있지 않음: {initial_list_data.get('requests')}"
    # print("--- 1. 초기 요청 목록 확인 완료 ---") # logger로 대체
    logger.info("--- 1. 초기 요청 목록 확인 완료 ---")

    # 2. 새 요청 생성 (3개의 태스크 포함)
    # print("\n--- 2. 새 요청 생성 ---") # logger로 대체
    logger.info("\n--- 2. 새 요청 생성 ---")
    planning_params = {
        "originalRequest": "Agent Assignment Test Project (Python Test)",
        "tasks": [
            {"title": "Task 1 for Agent Assignment", "description": "This is the first task."},
            {"title": "Task 2 for Agent Assignment", "description": "This is the second task."},
            {"title": "Task 3 - Unassigned Test", "description": "This task is for unassigned completion test."}
        ]
    }
    planning_response = call_mcp_tool("request_planning", planning_params)
    assert "result" in planning_response, f"요청 생성 실패 (result 키 없음): {planning_response}"
    planning_data = planning_response["result"]
    test_request_id = planning_data.get("requestId")
    assert test_request_id is not None, f"요청 ID가 반환되지 않음: {planning_data}"
    assert planning_data.get("taskCount") == 3, f"생성된 태스크 수 불일치: {planning_data}"
    # print(f"생성된 요청 ID: {test_request_id}") # logger로 대체
    logger.info(f"생성된 요청 ID: {test_request_id}")
    # print("--- 2. 새 요청 생성 완료 ---") # logger로 대체
    logger.info("--- 2. 새 요청 생성 완료 ---")

    # 2.1 생성된 태스크 ID 중 하나를 unassigned_task_id로 가져오기 (Task 3)
    # list_requests를 통해 태스크 ID들을 가져와야 함. request_planning은 task_ids를 반환하지 않음.
    # 또는 open_task_details 등을 사용할 수 있으나, 여기서는 list_requests 후 필터링
    list_after_planning_response = call_mcp_tool("list_requests", {})
    req_summary_for_task_ids = list_after_planning_response["result"]["requests"][0]
    
    # 상세 태스크 정보를 얻기 위해 _get_tasks_progress (내부용) 대신 open_task_details를 여러번 호출하거나,
    # TaskManager에 요청 ID로 태스크 목록 상세를 가져오는 MCP 도구를 추가해야 함.
    # 여기서는 TaskManager의 _get_tasks_progress가 반환하는 것과 유사한 정보를 구성하기 위해
    # open_task_details를 가정하거나, 테스트의 편의를 위해 TaskManager 내부 함수를 모방.
    # 지금은 test_request_id로 생성된 tasks의 ID를 알아낼 방법이 마땅치 않음.
    # request_planning이 task_ids를 반환하도록 수정하거나, list_requests가 task_ids를 포함하도록 해야함.
    # TaskManager.request_planning은 {"requestId": ..., "taskCount": ...} 만 반환.
    # 임시로, 생성된 3개의 태스크 중 3번째 태스크의 ID를 알아내기 위해선,
    # TaskManager 내부의 self.tasks를 직접 조회해야 하나 테스트 스크립트에서는 불가능.
    # 가장 최근에 생성된 3개의 태스크 ID를 가정하는 것은 불안정함.
    # 이 테스트는 unassigned_task_id를 명확히 특정할 수 있을 때까지 보류 또는 다른 방식으로 ID 확보 필요.
    # 여기서는 get_next_task를 통해 할당되지 않을 마지막 태스크를 식별해본다.

    # 3. 요청 목록 확인 (요청 1개, 태스크 3개 - 할당 0, 완료 0)
    # print("\n--- 3. 요청 생성 후 요청 목록 확인 ---") # logger로 대체
    logger.info("\n--- 3. 요청 생성 후 요청 목록 확인 ---")
    list_response_after_planning = call_mcp_tool("list_requests", {})
    assert "result" in list_response_after_planning
    list_data_after_planning = list_response_after_planning["result"]
    assert len(list_data_after_planning.get("requests", [])) == 1, "요청 개수 불일치"
    req_summary = list_data_after_planning["requests"][0]
    assert req_summary["id"] == test_request_id
    assert req_summary["totalTasks"] == 3
    assert req_summary.get("assignedTasks", 0) == 0, f"초기 할당된 태스크 수 불일치: {req_summary}"
    assert req_summary["doneTasks"] == 0
    # print("--- 3. 요청 목록 확인 완료 ---") # logger로 대체
    logger.info("--- 3. 요청 목록 확인 완료 ---")

    # 4. Agent 1이 다음 작업 가져오기
    # print(f"\n--- 4. Agent {agent_id_1} 작업 할당 시도 ---") # logger로 대체
    logger.info(f"\n--- 4. Agent {agent_id_1} 작업 할당 시도 ---")
    get_task_params_agent1 = {"requestId": test_request_id, "agentId": agent_id_1}
    task_for_agent1_response = call_mcp_tool("get_next_task", get_task_params_agent1)
    assert "result" in task_for_agent1_response
    task_for_agent1_data = task_for_agent1_response["result"]
    assert task_for_agent1_data.get("success") is True, f"Agent {agent_id_1} 작업 할당 실패: {task_for_agent1_data.get('error')}"
    assert task_for_agent1_data.get("hasNextTask") is True, f"Agent {agent_id_1}에게 할당된 작업이 없음"
    task_data_agent1 = task_for_agent1_data.get("task")
    assert task_data_agent1 is not None, "할당된 태스크 데이터가 없음 (Agent 1)"
    test_task_id_agent1 = task_data_agent1.get("id")
    assert test_task_id_agent1 is not None, "할당된 태스크 ID가 없음 (Agent 1)"
    assert task_data_agent1.get("assignedAgentId") == agent_id_1, f"태스크가 Agent {agent_id_1}에게 할당되지 않음"
    assert task_data_agent1.get("status") == TASK_STATUS_ASSIGNED, f"할당된 태스크의 상태 불일치: {task_data_agent1.get('status')}"
    # print(f"Agent {agent_id_1}에게 태스크 {test_task_id_agent1} 할당됨: {task_data_agent1.get('title')}") # logger로 대체
    logger.info(f"Agent {agent_id_1}에게 태스크 {test_task_id_agent1} 할당됨: {task_data_agent1.get('title')}")
    # print("--- 4. Agent 1 작업 할당 완료 ---") # logger로 대체
    logger.info("--- 4. Agent 1 작업 할당 완료 ---")

    # 5. 요청 목록 확인 (태스크 3개 - 할당 1, 완료 0)
    # print("\n--- 5. Agent 1 작업 할당 후 요청 목록 확인 ---") # logger로 대체
    logger.info("\n--- 5. Agent 1 작업 할당 후 요청 목록 확인 ---")
    list_response_after_assign1 = call_mcp_tool("list_requests", {})
    assert "result" in list_response_after_assign1
    req_summary_assigned1 = list_response_after_assign1["result"]["requests"][0]
    assert req_summary_assigned1["totalTasks"] == 3
    assert req_summary_assigned1.get("assignedTasks", -1) == 1, f"할당된 태스크 수 불일치: {req_summary_assigned1.get('assignedTasks')}"
    assert req_summary_assigned1["doneTasks"] == 0
    # print("--- 5. 요청 목록 확인 완료 ---") # logger로 대체
    logger.info("--- 5. 요청 목록 확인 완료 ---")

    # 6. Agent 2가 다음 작업 가져오기
    # print(f"\n--- 6. Agent {agent_id_2} 작업 할당 시도 ---") # logger로 대체
    logger.info(f"\n--- 6. Agent {agent_id_2} 작업 할당 시도 ---")
    get_task_params_agent2 = {"requestId": test_request_id, "agentId": agent_id_2}
    task_for_agent2_response = call_mcp_tool("get_next_task", get_task_params_agent2)
    assert "result" in task_for_agent2_response
    task_for_agent2_data = task_for_agent2_response["result"]
    assert task_for_agent2_data.get("success") is True, f"Agent {agent_id_2} 작업 할당 실패: {task_for_agent2_data.get('error')}"
    assert task_for_agent2_data.get("hasNextTask") is True, f"Agent {agent_id_2}에게 할당된 작업이 없음"
    task_data_agent2 = task_for_agent2_data.get("task")
    assert task_data_agent2 is not None
    test_task_id_agent2 = task_data_agent2.get("id")
    assert test_task_id_agent2 is not None
    assert test_task_id_agent2 != test_task_id_agent1, "Agent 1과 Agent 2에게 동일 태스크 할당됨"
    assert task_data_agent2.get("assignedAgentId") == agent_id_2
    assert task_data_agent2.get("status") == TASK_STATUS_ASSIGNED
    # print(f"Agent {agent_id_2}에게 태스크 {test_task_id_agent2} 할당됨: {task_data_agent2.get('title')}") # logger로 대체
    logger.info(f"Agent {agent_id_2}에게 태스크 {test_task_id_agent2} 할당됨: {task_data_agent2.get('title')}")
    # print("--- 6. Agent 2 작업 할당 완료 ---") # logger로 대체
    logger.info("--- 6. Agent 2 작업 할당 완료 ---")
    
    # 6.1. 세 번째 태스크(할당 안 된) ID 확보 시도
    # 현재 agent1, agent2에게 하나씩 할당됨. 남은 하나가 unassigned_task_id 후보.
    # get_next_task를 한 번 더 호출하면 (예: agent_id_1로) 세 번째 태스크가 할당될 것임.
    # 그 ID를 unassigned_task_id로 사용하기 위해 미리 가져오고, 테스트 후 초기화.
    # 이 방법은 테스트 흐름에 영향을 줄 수 있으므로 주의.
    # 여기서는 Task 3 (Unassigned Test) 의 ID를 특정하기 위해 임시로 get_next_task 사용
    
    temp_get_task_params = {"requestId": test_request_id, "agentId": "temp-agent-for-id"}
    temp_task_response = call_mcp_tool("get_next_task", temp_get_task_params)
    if temp_task_response.get("result", {}).get("hasNextTask"):
        unassigned_task_id = temp_task_response["result"]["task"]["id"]
        # print(f"테스트용 미할당 태스크 ID 확보: {unassigned_task_id} ({temp_task_response['result']['task']['title']})") # logger로 대체
        logger.info(f"테스트용 미할당 태스크 ID 확보: {unassigned_task_id} ({temp_task_response['result']['task']['title']})")
        # 이 태스크를 다시 PENDING으로 되돌리는 MCP 도구가 없으므로, 이 테스트 후에는 데이터 클린업 필요.
        # 또는, 이 태스크를 완료하지 않고 다른 테스트를 진행.
        # 여기서는 ID만 확보하고, 실제 할당 상태는 유지. (temp-agent-for-id에게 할당된 상태)
        # 이로 인해 assignedTasks 카운트가 1 증가한 상태로 다음 테스트가 진행됨.
        # 이를 원치 않으면, 이 ID 확보 로직을 다른 곳으로 옮기거나, clear 후 재실행.
        # 지금은 이 상태를 감안하고 진행. (assignedTasks는 3이 될 것)
    else:
        # print("미할당 태스크 ID 확보 실패. Task 3에 대한 테스트 스킵될 수 있음.") # logger로 대체
        logger.warning("미할당 태스크 ID 확보 실패. Task 3에 대한 테스트 스킵될 수 있음.")


    # 7. 요청 목록 확인 (태스크 3개 - 할당 2 또는 3 (위 ID확보 로직에 따라), 완료 0)
    # print("\n--- 7. Agent 2 작업 할당 후 요청 목록 확인 ---") # logger로 대체
    logger.info("\n--- 7. Agent 2 작업 할당 후 요청 목록 확인 ---")
    list_response_after_assign2 = call_mcp_tool("list_requests", {})
    assert "result" in list_response_after_assign2
    req_summary_assigned2 = list_response_after_assign2["result"]["requests"][0]
    assert req_summary_assigned2["totalTasks"] == 3
    # unassigned_task_id 확보 로직으로 인해 assignedTasks가 3일 수 있음
    current_assigned_tasks = req_summary_assigned2.get("assignedTasks", -1)
    assert current_assigned_tasks in [2, 3], f"할당된 태스크 수 불일치 (2 또는 3이어야 함): {current_assigned_tasks}"
    assert req_summary_assigned2["doneTasks"] == 0
    # print(f"--- 7. 요청 목록 확인 완료 (현재 할당된 태스크: {current_assigned_tasks}) ---") # logger로 대체
    logger.info(f"--- 7. 요청 목록 확인 완료 (현재 할당된 태스크: {current_assigned_tasks}) ---")

    # 8. Agent 1이 할당받은 작업 완료 처리
    # print(f"\n--- 8. Agent {agent_id_1}이 태스크 {test_task_id_agent1} 완료 시도 ---") # logger로 대체
    logger.info(f"\n--- 8. Agent {agent_id_1}이 태스크 {test_task_id_agent1} 완료 시도 ---")
    mark_done_params_agent1 = {
        "requestId": test_request_id, 
        "taskId": test_task_id_agent1, 
        "agentId": agent_id_1,
        "completedDetails": f"Task {test_task_id_agent1} completed by {agent_id_1}"
    }
    done_response_agent1 = call_mcp_tool("mark_task_done", mark_done_params_agent1)
    assert "result" in done_response_agent1, f"Agent {agent_id_1} 작업 완료 실패 (result 키 없음): {done_response_agent1}"
    done_data_agent1 = done_response_agent1["result"]
    assert done_data_agent1.get("status") == TASK_STATUS_DONE, f"완료된 태스크 상태 불일치: {done_data_agent1}"
    # print(f"Agent {agent_id_1}에 의해 태스크 {test_task_id_agent1} 완료됨") # logger로 대체
    logger.info(f"Agent {agent_id_1}에 의해 태스크 {test_task_id_agent1} 완료됨")
    # print("--- 8. Agent 1 작업 완료 처리 완료 ---") # logger로 대체
    logger.info("--- 8. Agent 1 작업 완료 처리 완료 ---")

    # 9. 요청 목록 확인 (Agent 1 완료 후)
    # print("\n--- 9. Agent 1 작업 완료 후 요청 목록 확인 ---") # logger로 대체
    logger.info("\n--- 9. Agent 1 작업 완료 후 요청 목록 확인 ---")
    list_response_after_done1 = call_mcp_tool("list_requests", {})
    assert "result" in list_response_after_done1
    req_summary_done1 = list_response_after_done1["result"]["requests"][0]
    assert req_summary_done1["totalTasks"] == 3
    # assignedTasks는 1 줄고, doneTasks는 1 늘어남
    # (만약 이전 단계에서 unassigned_task_id 확보로 3개 할당되었었다면, 이제 2개 할당)
    expected_assigned_after_done1 = current_assigned_tasks - 1
    assert req_summary_done1.get("assignedTasks", -1) == expected_assigned_after_done1, \
        f"할당된 태스크 수 불일치 (1 완료 후): 기대값={expected_assigned_after_done1}, 실제값={req_summary_done1.get('assignedTasks')}"
    assert req_summary_done1["doneTasks"] == 1
    # print("--- 9. 요청 목록 확인 완료 ---") # logger로 대체
    logger.info("--- 9. 요청 목록 확인 완료 ---")

    # --- 추가된 테스트 케이스들 ---
    # 9.1 mark_task_done 호출 시 agentId 파라미터 누락 (실패 예상)
    # print("\n--- 9.1. mark_task_done 호출 시 agentId 파라미터 누락 테스트 ---") # logger로 대체
    logger.info("\n--- 9.1. mark_task_done 호출 시 agentId 파라미터 누락 테스트 ---")
    mark_done_missing_agentid_params = {
        "requestId": test_request_id,
        "taskId": test_task_id_agent2, # 아직 완료되지 않은 Agent 2의 태스크 사용
        # "agentId": agent_id_2, # 누락
        "completedDetails": "Attempting completion without agentId"
    }
    missing_agentid_response = call_mcp_tool("mark_task_done", mark_done_missing_agentid_params)
    assert missing_agentid_response.get("success") is False, "agentId 누락 시 성공으로 처리됨"
    assert missing_agentid_response.get("error_type") == "HTTPError", "agentId 누락 시 HTTPError가 아님"
    error_detail = get_error_detail_from_raw_response(missing_agentid_response.get("raw_response", ""))
    assert "'agentId' is a required parameter" in error_detail, f"agentId 누락 시 에러 메시지 불일치: {error_detail}"
    # print(f"--- 9.1. agentId 파라미터 누락 테스트 완료 (예상된 실패: {error_detail}) ---") # logger로 대체
    logger.info(f"--- 9.1. agentId 파라미터 누락 테스트 완료 (예상된 실패: {error_detail}) ---")

    # 9.2 mark_task_done 호출 시 agentId가 빈 문자열 (실패 예상)
    # print("\n--- 9.2. mark_task_done 호출 시 빈 agentId 테스트 ---") # logger로 대체
    logger.info("\n--- 9.2. mark_task_done 호출 시 빈 agentId 테스트 ---")
    mark_done_empty_agentid_params = {
        "requestId": test_request_id,
        "taskId": test_task_id_agent2,
        "agentId": "", # 빈 문자열
        "completedDetails": "Attempting completion with empty agentId"
    }
    empty_agentid_response = call_mcp_tool("mark_task_done", mark_done_empty_agentid_params)
    assert empty_agentid_response.get("success") is False, "빈 agentId 시 성공으로 처리됨"
    assert empty_agentid_response.get("error_type") == "HTTPError", "빈 agentId 시 HTTPError가 아님"
    error_detail_empty = get_error_detail_from_raw_response(empty_agentid_response.get("raw_response", ""))
    assert "agent_id는 작업을 완료하기 위해 필수입니다." in error_detail_empty, f"빈 agentId 시 에러 메시지 불일치: {error_detail_empty}"
    # print(f"--- 9.2. 빈 agentId 테스트 완료 (예상된 실패: {error_detail_empty}) ---") # logger로 대체
    logger.info(f"--- 9.2. 빈 agentId 테스트 완료 (예상된 실패: {error_detail_empty}) ---")
    
    # 9.3 할당되지 않은 PENDING 태스크를 mark_task_done으로 바로 완료 시도 (실패 예상)
    # 이 테스트를 위해서는 unassigned_task_id가 필요함.
    # 만약 6.1 단계에서 unassigned_task_id가 확보되었다면 (temp-agent-for-id 에게 할당된 상태)
    # 이 태스크는 ASSIGNED 상태이므로 이 테스트에 적합하지 않음.
    # 데이터를 초기화하고 PENDING 상태의 태스크 ID를 확보해야 함.
    # 여기서는 테스트 흐름상 unassigned_task_id가 PENDING 상태라고 가정하고 진행. (실제로는 위에서 할당됨)
    # 가장 좋은 방법은 request_planning 시 ID를 반환받거나, 특정 조건으로 PENDING task ID를 가져오는 것.
    # 지금은 'Task 3 - Unassigned Test'라는 이름의 태스크 ID를 찾아야 함.
    # 임시 방편: list_requests 후 전체 태스크 목록을 보고, 아직 PENDING인 것 중 하나를 선택.
    
    found_pending_for_test = False
    if unassigned_task_id: # 6.1에서 ID를 확보했지만, 이미 할당된 상태일 것임.
                           # 테스트를 위해선 PENDING 상태의 ID를 찾아야 함.
                           # 이 ID (unassigned_task_id)는 현재 temp-agent-for-id에게 할당되어있음.
                           # 따라서 이 ID로 테스트하면 "다른 에이전트에게 할당" 오류가 나야 정상.
        # print(f"\n--- 9.3. 다른 에이전트({temp_get_task_params['agentId']})에게 할당된 태스크({unassigned_task_id})를 다른 에이전트({agent_id_1})가 완료 시도 ---") # logger로 대체
        logger.info(f"\n--- 9.3. 다른 에이전트({temp_get_task_params['agentId']})에게 할당된 태스크({unassigned_task_id})를 다른 에이전트({agent_id_1})가 완료 시도 ---")
        mark_done_on_other_assigned_task_params = {
            "requestId": test_request_id,
            "taskId": unassigned_task_id, 
            "agentId": agent_id_1, # temp-agent-for-id가 아닌 다른 에이전트
            "completedDetails": "Attempting to complete a task assigned to someone else"
        }
        pending_status_done_response = call_mcp_tool("mark_task_done", mark_done_on_other_assigned_task_params)
        assert pending_status_done_response.get("success") is False, "다른 에이전트에게 할당된 태스크 완료 시도가 성공함"
        error_detail_pending = get_error_detail_from_raw_response(pending_status_done_response.get("raw_response", ""))
        expected_error_fragment_pending = "다른 에이전트에게 할당되었습니다."
        assert expected_error_fragment_pending in error_detail_pending, \
            f"다른 에이전트 할당 태스크 완료 시도 시 에러 메시지 불일치: 기대='{expected_error_fragment_pending}', 실제='{error_detail_pending}'"
        # print(f"--- 9.3. 다른 에이전트 할당 태스크 완료 시도 테스트 완료 (예상된 실패: {error_detail_pending}) ---") # logger로 대체
        logger.info(f"--- 9.3. 다른 에이전트 할당 태스크 완료 시도 테스트 완료 (예상된 실패: {error_detail_pending}) ---")
        found_pending_for_test = True # 일단 이 테스트라도 진행
    
    if not found_pending_for_test:
         # print("\n--- 9.3. PENDING 상태 태스크 직접 완료 시도 테스트 (적절한 PENDING 태스크 ID 확보 불가로 스킵) ---") # logger로 대체
         logger.warning("\n--- 9.3. PENDING 상태 태스크 직접 완료 시도 테스트 (적절한 PENDING 태스크 ID 확보 불가로 스킵) ---")
    # --- 추가 테스트 케이스 종료 ---

    # 10. Agent 2가 Agent 1의 완료된 작업을 다시 완료 시도 (실패해야 함)
    # print(f"\n--- 10. Agent {agent_id_2}이 이미 완료된 태스크 {test_task_id_agent1} 완료 시도 ---") # logger로 대체
    logger.info(f"\n--- 10. Agent {agent_id_2}이 이미 완료된 태스크 {test_task_id_agent1} 완료 시도 ---")
    mark_done_params_agent2_on_done_task = {
        "requestId": test_request_id, 
        "taskId": test_task_id_agent1, # Agent 1이 완료한 태스크
        "agentId": agent_id_2,
        "completedDetails": "Attempting to re-complete other agent's done task."
    }
    done_again_response = call_mcp_tool("mark_task_done", mark_done_params_agent2_on_done_task)
    # TaskManager의 mark_task_done은 {"message": "태스크 ... 이미 완료되었습니다.", "status": "DONE"} 을 반환 (HTTP 200)
    assert "result" in done_again_response, f"이미 완료된 태스크 재완료 시도 시 result 키 없음: {done_again_response}"
    done_again_data = done_again_response["result"]
    assert done_again_data.get("status") == TASK_STATUS_DONE, f"이미 완료된 태스크 재완료 시도 시 상태 불일치: {done_again_data}"
    assert "이미 완료되었습니다." in done_again_data.get("message", ""), f"이미 완료된 태스크 재완료 시도 시 메시지 불일치: {done_again_data}"
    # print("--- 10. 이미 완료된 태스크 재완료 시도 완료 (예상된 결과) ---") # logger로 대체
    logger.info("--- 10. 이미 완료된 태스크 재완료 시도 완료 (예상된 결과) ---")


    # 11. Agent 1이 Agent 2에게 할당된 작업을 완료 시도 (실패해야 함)
    # print(f"\n--- 11. Agent {agent_id_1}이 Agent {agent_id_2}의 태스크 {test_task_id_agent2} 완료 시도 ---") # logger로 대체
    logger.info(f"\n--- 11. Agent {agent_id_1}이 Agent {agent_id_2}의 태스크 {test_task_id_agent2} 완료 시도 ---")
    mark_done_params_agent1_on_agent2_task = {
        "requestId": test_request_id, 
        "taskId": test_task_id_agent2, # Agent 2에게 할당된 태스크
        "agentId": agent_id_1, 
        "completedDetails": "Attempting to complete other agent's task."
    }
    wrong_agent_done_response = call_mcp_tool("mark_task_done", mark_done_params_agent1_on_agent2_task)
    assert wrong_agent_done_response.get("success") is False, "다른 에이전트의 작업 완료 시도가 성공으로 처리됨 (success 필드)"
    assert wrong_agent_done_response.get("error_type") == "HTTPError", "다른 에이전트 작업 완료 시도 시 HTTPError가 아님"
    error_detail_wrong_agent = get_error_detail_from_raw_response(wrong_agent_done_response.get("raw_response", ""))
    expected_error_fragment_wrong_agent = "다른 에이전트에게 할당되었습니다."
    # TaskManager는 "태스크 {task_id}는 다른 에이전트에게 할당되었습니다." 를 반환함.
    assert expected_error_fragment_wrong_agent in error_detail_wrong_agent, \
        f"잘못된 에이전트가 작업 완료 시도 시 에러 메시지 불일치: 기대 포함='{expected_error_fragment_wrong_agent}', 실제='{error_detail_wrong_agent}'"
    # print(f"--- 11. 다른 에이전트 작업 완료 시도 완료 (예상된 실패: {error_detail_wrong_agent}) ---") # logger로 대체
    logger.info(f"--- 11. 다른 에이전트 작업 완료 시도 완료 (예상된 실패: {error_detail_wrong_agent}) ---")

    # 12. Agent 2가 자신의 작업 완료
    # print(f"\n--- 12. Agent {agent_id_2}이 자신의 태스크 {test_task_id_agent2} 완료 시도 ---") # logger로 대체
    logger.info(f"\n--- 12. Agent {agent_id_2}이 자신의 태스크 {test_task_id_agent2} 완료 시도 ---")
    mark_done_params_agent2 = {
        "requestId": test_request_id,
        "taskId": test_task_id_agent2,
        "agentId": agent_id_2,
        "completedDetails": f"Task {test_task_id_agent2} completed by {agent_id_2}"
    }
    done_response_agent2 = call_mcp_tool("mark_task_done", mark_done_params_agent2)
    assert "result" in done_response_agent2
    assert done_response_agent2["result"].get("status") == TASK_STATUS_DONE
    # print(f"Agent {agent_id_2}에 의해 태스크 {test_task_id_agent2} 완료됨") # logger로 대체
    logger.info(f"Agent {agent_id_2}에 의해 태스크 {test_task_id_agent2} 완료됨")

    # 13. 만약 unassigned_task_id (Task 3)가 temp-agent-for-id에게 할당된 채로 남아있다면, 그것도 완료.
    if unassigned_task_id and temp_get_task_params: # temp_get_task_params['agentId']가 존재해야 함
        # print(f"\n--- 13. temp-agent ({temp_get_task_params['agentId']})가 태스크 {unassigned_task_id} 완료 시도 ---") # logger로 대체
        logger.info(f"\n--- 13. temp-agent ({temp_get_task_params['agentId']})가 태스크 {unassigned_task_id} 완료 시도 ---")
        mark_done_params_temp_agent = {
            "requestId": test_request_id,
            "taskId": unassigned_task_id,
            "agentId": temp_get_task_params['agentId'], # 할당받은 temp-agent
            "completedDetails": f"Task {unassigned_task_id} completed by {temp_get_task_params['agentId']}"
        }
        done_response_temp_agent = call_mcp_tool("mark_task_done", mark_done_params_temp_agent)
        assert "result" in done_response_temp_agent
        assert done_response_temp_agent["result"].get("status") == TASK_STATUS_DONE
        # print(f"temp-agent에 의해 태스크 {unassigned_task_id} 완료됨") # logger로 대체
        logger.info(f"temp-agent에 의해 태스크 {unassigned_task_id} 완료됨")


    # 14. 모든 작업이 완료된 후 다음 작업 가져오기 시도 (hasNextTask: False 예상)
    # print(f"\n--- 14. 모든 작업 완료 후 Agent {agent_id_1}이 작업 할당 시도 ---") # logger로 대체
    logger.info(f"\n--- 14. 모든 작업 완료 후 Agent {agent_id_1}이 작업 할당 시도 ---")
    final_get_task_response = call_mcp_tool("get_next_task", get_task_params_agent1) # agent_id_1로 다시 시도
    assert "result" in final_get_task_response
    final_get_task_data = final_get_task_response["result"]
    assert final_get_task_data.get("success") is True
    assert final_get_task_data.get("hasNextTask") is False, f"모든 작업 완료 후에도 작업이 있다고 나옴: {final_get_task_data}"
    # 메시지는 "No assignable task found..." 또는 유사한 내용
    assert "No assignable task found" in final_get_task_data.get("message", ""), f"모든 작업 소진 후 메시지 불일치: {final_get_task_data}"
    # print("--- 14. 모든 작업 완료 후 작업 할당 시도 완료 (예상된 결과) ---") # logger로 대체
    logger.info("--- 14. 모든 작업 완료 후 작업 할당 시도 완료 (예상된 결과) ---")


    # 15. 최종 요청 목록 확인 (모든 태스크 완료)
    # print("\n--- 15. 최종 요청 목록 확인 ---") # logger로 대체
    logger.info("\n--- 15. 최종 요청 목록 확인 ---")
    final_list_response = call_mcp_tool("list_requests", {})
    assert "result" in final_list_response
    final_req_summary = final_list_response["result"]["requests"][0]
    assert final_req_summary["totalTasks"] == 3
    assert final_req_summary.get("assignedTasks", 0) == 0 # 모든 작업이 완료되었으므로 할당된 작업은 0
    assert final_req_summary["doneTasks"] == 3 # 모든 작업 완료
    # 요청 상태가 "COMPLETED"로 변경되었는지 확인
    assert final_req_summary.get("status") == "COMPLETED", f"모든 태스크 완료 후 요청 상태가 COMPLETED가 아님: {final_req_summary.get('status')}"
    # print("--- 15. 최종 요청 목록 확인 완료 ---") # logger로 대체
    logger.info("--- 15. 최종 요청 목록 확인 완료 ---")

    # print("\n===== 모든 테스트 통과! =======") # logger로 대체
    logger.info("\n===== 모든 테스트 통과! =======")

if __name__ == "__main__":
    try:
        # 서버의 실제 동작하는 엔드포인트로 변경 (예: /docs)
        health_check_url = SERVER_URL_ROOT + "docs" 
        response = requests.get(health_check_url, timeout=5) # 타임아웃 약간 늘림
        response.raise_for_status()
        logger.info(f"서버 ({health_check_url}) 연결 확인됨. 테스트를 시작합니다...")
        run_tests()
    except requests.exceptions.ConnectionError:
        logger.error(f"오류: 서버({health_check_url})에 연결할 수 없습니다. PMAgent MCP 서버가 {SERVER_URL_ROOT}에서 실행 중인지 확인하세요.", exc_info=True)
        sys.exit(1)
    except requests.exceptions.Timeout:
        logger.error(f"오류: 서버({health_check_url}) 연결 시간 초과.", exc_info=True)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        logger.error(f"오류: 서버({health_check_url})가 실행 중이지만 오류 응답: {e.response.status_code} - {e.response.text}", exc_info=True)
        sys.exit(1) 