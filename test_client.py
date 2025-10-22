#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent 테스트 클라이언트

서버의 주요 기능을 간단히 테스트할 수 있는 스크립트입니다.
"""

import requests
import json
import time
from typing import Dict, Any


class PMAgentTestClient:
    """PMAgent 테스트 클라이언트"""

    def __init__(self, base_url: str = "http://localhost:8082"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []

    def _test(self, name: str, func):
        """테스트를 실행하고 결과를 기록합니다."""
        print(f"\n{'='*60}")
        print(f"테스트: {name}")
        print(f"{'='*60}")

        try:
            start_time = time.time()
            result = func()
            elapsed = time.time() - start_time

            print(f"✅ 성공 ({elapsed:.2f}초)")
            self.test_results.append({
                "name": name,
                "status": "PASS",
                "elapsed": elapsed,
                "result": result
            })
            return result
        except Exception as e:
            print(f"❌ 실패: {e}")
            self.test_results.append({
                "name": name,
                "status": "FAIL",
                "error": str(e)
            })
            return None

    def test_server_status(self):
        """서버 상태 확인 테스트"""
        def _test():
            response = self.session.get(f"{self.base_url}/")
            response.raise_for_status()
            data = response.json()
            print(f"   서버: {data.get('name')}")
            print(f"   버전: {data.get('version')}")
            return data

        return self._test("서버 상태 확인", _test)

    def test_mcp_tools(self):
        """MCP 도구 목록 조회 테스트"""
        def _test():
            response = self.session.get(f"{self.base_url}/mcp/tools")
            response.raise_for_status()
            data = response.json()
            tools = data.get("tools", [])
            print(f"   발견된 도구: {len(tools)}개")
            for tool in tools[:5]:  # 처음 5개만 표시
                print(f"   - {tool.get('name')}")
            return data

        return self._test("MCP 도구 목록 조회", _test)

    def test_create_project(self):
        """프로젝트 생성 테스트"""
        def _test():
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "create_project",
                "params": {
                    "name": f"테스트 프로젝트 {int(time.time())}",
                    "description": "자동 테스트로 생성된 프로젝트입니다."
                }
            }
            response = self.session.post(f"{self.base_url}/mcp/invoke", json=payload)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise Exception(f"MCP 에러: {data['error']}")

            result = data.get("result", {})
            print(f"   프로젝트 ID: {result.get('project_id')}")
            print(f"   이름: {result.get('name')}")
            print(f"   상태: {result.get('status')}")
            return result

        return self._test("프로젝트 생성", _test)

    def test_list_projects(self):
        """프로젝트 목록 조회 테스트"""
        def _test():
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "list_projects",
                "params": {}
            }
            response = self.session.post(f"{self.base_url}/mcp/invoke", json=payload)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise Exception(f"MCP 에러: {data['error']}")

            result = data.get("result", {})
            projects = result.get("projects", [])
            print(f"   전체 프로젝트: {len(projects)}개")
            for project in projects[:3]:  # 처음 3개만 표시
                print(f"   - {project.get('name')} (ID: {project.get('project_id')})")
            return result

        return self._test("프로젝트 목록 조회", _test)

    def test_create_task(self, project_id: str):
        """작업 생성 테스트"""
        def _test():
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "create_task",
                "params": {
                    "project_id": project_id,
                    "title": f"테스트 작업 {int(time.time())}",
                    "description": "자동 테스트로 생성된 작업입니다.",
                    "assigned_to": "pm-agent"
                }
            }
            response = self.session.post(f"{self.base_url}/mcp/invoke", json=payload)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise Exception(f"MCP 에러: {data['error']}")

            result = data.get("result", {})
            print(f"   작업 ID: {result.get('task_id')}")
            print(f"   제목: {result.get('title')}")
            print(f"   상태: {result.get('status')}")
            return result

        return self._test(f"작업 생성 (프로젝트 ID: {project_id})", _test)

    def test_list_tasks(self, project_id: str):
        """작업 목록 조회 테스트"""
        def _test():
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "list_tasks",
                "params": {"project_id": project_id}
            }
            response = self.session.post(f"{self.base_url}/mcp/invoke", json=payload)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise Exception(f"MCP 에러: {data['error']}")

            result = data.get("result", {})
            tasks = result.get("tasks", [])
            print(f"   전체 작업: {len(tasks)}개")
            for task in tasks[:3]:  # 처음 3개만 표시
                print(f"   - {task.get('title')} (상태: {task.get('status')})")
            return result

        return self._test(f"작업 목록 조회 (프로젝트 ID: {project_id})", _test)

    def run_all_tests(self):
        """모든 테스트를 실행합니다."""
        print("\n" + "🚀 PMAgent 테스트 시작 ".center(60, "="))

        # 1. 서버 상태 확인
        self.test_server_status()

        # 2. MCP 도구 목록 조회
        self.test_mcp_tools()

        # 3. 프로젝트 생성
        project_result = self.test_create_project()
        if not project_result:
            print("\n⚠️  프로젝트 생성 실패로 이후 테스트를 건너뜁니다.")
            self.print_summary()
            return

        project_id = project_result.get("project_id")

        # 4. 작업 생성
        self.test_create_task(project_id)

        # 5. 프로젝트 목록 조회
        self.test_list_projects()

        # 6. 작업 목록 조회
        self.test_list_tasks(project_id)

        # 결과 출력
        self.print_summary()

    def print_summary(self):
        """테스트 결과 요약을 출력합니다."""
        print("\n" + "📊 테스트 결과 요약 ".center(60, "="))

        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        total = len(self.test_results)

        print(f"\n전체: {total}개 | 성공: {passed}개 | 실패: {failed}개")

        if failed > 0:
            print("\n❌ 실패한 테스트:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   - {result['name']}: {result.get('error', 'Unknown error')}")

        print("\n" + "="*60)

        if failed == 0:
            print("✅ 모든 테스트가 성공했습니다!")
        else:
            print(f"⚠️  {failed}개의 테스트가 실패했습니다.")

        print("="*60 + "\n")


def main():
    """메인 함수"""
    import sys

    base_url = "http://localhost:8082"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    print(f"테스트 대상 서버: {base_url}\n")

    client = PMAgentTestClient(base_url)
    client.run_all_tests()


if __name__ == "__main__":
    main()
