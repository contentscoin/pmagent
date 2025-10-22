#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent CLI - 명령줄 관리 도구

이 CLI 도구는 PMAgent 서버를 관리하고 테스트하는 기능을 제공합니다.
"""

import os
import sys
import argparse
import requests
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 기본 설정
DEFAULT_SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8082")


class PMAgentCLI:
    """PMAgent CLI 클래스"""

    def __init__(self, server_url: str = DEFAULT_SERVER_URL):
        self.server_url = server_url
        self.session = requests.Session()

    def _make_request(self, endpoint: str, method: str = "GET",
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """HTTP 요청을 보냅니다."""
        url = f"{self.server_url}{endpoint}"

        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 요청 실패: {e}")
            return {"error": str(e)}

    def _mcp_call(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """MCP JSON-RPC 호출을 수행합니다."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }

        try:
            response = self.session.post(f"{self.server_url}/mcp/invoke", json=payload)
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                print(f"❌ MCP 에러: {result['error']}")
                return result

            return result.get("result", {})
        except requests.exceptions.RequestException as e:
            print(f"❌ MCP 호출 실패: {e}")
            return {"error": str(e)}

    def check_server(self):
        """서버 상태를 확인합니다."""
        print(f"🔍 서버 연결 확인 중: {self.server_url}")

        try:
            response = self.session.get(f"{self.server_url}/")
            if response.status_code == 200:
                print("✅ 서버가 정상적으로 실행 중입니다.")
                data = response.json()
                print(f"   서버 이름: {data.get('name', 'N/A')}")
                print(f"   버전: {data.get('version', 'N/A')}")
                return True
            else:
                print(f"❌ 서버 응답 이상: HTTP {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
            return False
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            return False

    def list_tools(self):
        """사용 가능한 MCP 도구 목록을 조회합니다."""
        print("📋 사용 가능한 MCP 도구 조회 중...")

        try:
            response = self.session.get(f"{self.server_url}/mcp/tools")
            response.raise_for_status()
            data = response.json()

            tools = data.get("tools", [])
            if tools:
                print(f"\n✅ {len(tools)}개의 도구를 찾았습니다:\n")
                for i, tool in enumerate(tools, 1):
                    print(f"{i}. {tool.get('name')}")
                    print(f"   설명: {tool.get('description', 'N/A')}")
                    print()
            else:
                print("⚠️  사용 가능한 도구가 없습니다.")
        except Exception as e:
            print(f"❌ 도구 목록 조회 실패: {e}")

    def create_project(self, name: str, description: str = ""):
        """새 프로젝트를 생성합니다."""
        print(f"📁 프로젝트 생성 중: {name}")

        result = self._mcp_call("create_project", {
            "name": name,
            "description": description
        })

        if "error" not in result:
            print(f"✅ 프로젝트가 생성되었습니다!")
            print(f"   프로젝트 ID: {result.get('project_id', 'N/A')}")
            print(f"   이름: {result.get('name', 'N/A')}")
            print(f"   상태: {result.get('status', 'N/A')}")

        return result

    def list_projects(self):
        """프로젝트 목록을 조회합니다."""
        print("📋 프로젝트 목록 조회 중...")

        result = self._mcp_call("list_projects")

        if "error" not in result:
            projects = result.get("projects", [])
            if projects:
                print(f"\n✅ {len(projects)}개의 프로젝트를 찾았습니다:\n")
                for i, project in enumerate(projects, 1):
                    print(f"{i}. {project.get('name', 'N/A')} (ID: {project.get('project_id', 'N/A')})")
                    print(f"   상태: {project.get('status', 'N/A')}")
                    print(f"   생성일: {project.get('created_at', 'N/A')}")
                    print()
            else:
                print("⚠️  프로젝트가 없습니다.")

        return result

    def create_task(self, project_id: str, title: str, description: str = ""):
        """새 작업을 생성합니다."""
        print(f"📝 작업 생성 중: {title}")

        result = self._mcp_call("create_task", {
            "project_id": project_id,
            "title": title,
            "description": description,
            "assigned_to": "pm-agent"
        })

        if "error" not in result:
            print(f"✅ 작업이 생성되었습니다!")
            print(f"   작업 ID: {result.get('task_id', 'N/A')}")
            print(f"   제목: {result.get('title', 'N/A')}")
            print(f"   상태: {result.get('status', 'N/A')}")

        return result

    def list_tasks(self, project_id: str):
        """프로젝트의 작업 목록을 조회합니다."""
        print(f"📋 작업 목록 조회 중 (프로젝트 ID: {project_id})...")

        result = self._mcp_call("list_tasks", {"project_id": project_id})

        if "error" not in result:
            tasks = result.get("tasks", [])
            if tasks:
                print(f"\n✅ {len(tasks)}개의 작업을 찾았습니다:\n")
                for i, task in enumerate(tasks, 1):
                    print(f"{i}. {task.get('title', 'N/A')} (ID: {task.get('task_id', 'N/A')})")
                    print(f"   상태: {task.get('status', 'N/A')}")
                    print(f"   담당자: {task.get('assigned_to', 'N/A')}")
                    print()
            else:
                print("⚠️  작업이 없습니다.")

        return result

    def demo(self):
        """데모 시나리오를 실행합니다."""
        print("\n" + "="*60)
        print("🚀 PMAgent CLI 데모 시작")
        print("="*60 + "\n")

        # 1. 서버 상태 확인
        if not self.check_server():
            print("\n❌ 서버가 실행되지 않아 데모를 계속할 수 없습니다.")
            print("   'python run_server.py' 명령으로 서버를 먼저 시작하세요.\n")
            return

        print()

        # 2. 도구 목록 확인
        self.list_tools()

        # 3. 프로젝트 생성
        print("\n" + "-"*60)
        project_result = self.create_project(
            "테스트 프로젝트",
            "CLI 데모용 테스트 프로젝트입니다."
        )

        if "error" in project_result:
            print("\n❌ 프로젝트 생성 실패로 데모를 중단합니다.")
            return

        project_id = project_result.get("project_id")
        print()

        # 4. 작업 생성
        print("-"*60)
        self.create_task(
            project_id,
            "UI 디자인 작성",
            "메인 화면의 UI 디자인을 작성합니다."
        )
        print()

        print("-"*60)
        self.create_task(
            project_id,
            "API 엔드포인트 구현",
            "RESTful API 엔드포인트를 구현합니다."
        )
        print()

        # 5. 프로젝트 목록 조회
        print("-"*60)
        self.list_projects()

        # 6. 작업 목록 조회
        print("-"*60)
        self.list_tasks(project_id)

        print("="*60)
        print("✅ 데모 완료!")
        print("="*60 + "\n")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="PMAgent CLI - PMAgent 서버 관리 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  %(prog)s check                    # 서버 상태 확인
  %(prog)s tools                    # MCP 도구 목록 조회
  %(prog)s projects                 # 프로젝트 목록 조회
  %(prog)s create-project "프로젝트명"  # 프로젝트 생성
  %(prog)s demo                     # 데모 실행
        """
    )

    parser.add_argument(
        "--url",
        default=DEFAULT_SERVER_URL,
        help=f"서버 URL (기본값: {DEFAULT_SERVER_URL})"
    )

    subparsers = parser.add_subparsers(dest="command", help="실행할 명령")

    # check 명령
    subparsers.add_parser("check", help="서버 상태 확인")

    # tools 명령
    subparsers.add_parser("tools", help="MCP 도구 목록 조회")

    # projects 명령
    subparsers.add_parser("projects", help="프로젝트 목록 조회")

    # create-project 명령
    create_project_parser = subparsers.add_parser("create-project", help="프로젝트 생성")
    create_project_parser.add_argument("name", help="프로젝트 이름")
    create_project_parser.add_argument("--description", default="", help="프로젝트 설명")

    # tasks 명령
    tasks_parser = subparsers.add_parser("tasks", help="작업 목록 조회")
    tasks_parser.add_argument("project_id", help="프로젝트 ID")

    # create-task 명령
    create_task_parser = subparsers.add_parser("create-task", help="작업 생성")
    create_task_parser.add_argument("project_id", help="프로젝트 ID")
    create_task_parser.add_argument("title", help="작업 제목")
    create_task_parser.add_argument("--description", default="", help="작업 설명")

    # demo 명령
    subparsers.add_parser("demo", help="데모 시나리오 실행")

    args = parser.parse_args()

    # CLI 인스턴스 생성
    cli = PMAgentCLI(server_url=args.url)

    # 명령 실행
    if args.command == "check":
        cli.check_server()
    elif args.command == "tools":
        cli.list_tools()
    elif args.command == "projects":
        cli.list_projects()
    elif args.command == "create-project":
        cli.create_project(args.name, args.description)
    elif args.command == "tasks":
        cli.list_tasks(args.project_id)
    elif args.command == "create-task":
        cli.create_task(args.project_id, args.title, args.description)
    elif args.command == "demo":
        cli.demo()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
