#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime

from pmagent.agent import PMAgent
from pmagent.models import Project, Task, Status


class TestPMAgent(unittest.TestCase):
    """PMAgent 클래스에 대한 테스트 케이스"""

    def setUp(self):
        """테스트 전 설정"""
        self.mock_session = MagicMock()
        self.test_url = "http://localhost:8000"
        self.agent = PMAgent(url=self.test_url, session=self.mock_session)
        
        # 테스트 데이터
        self.test_project = Project(
            id="p1",
            name="테스트 프로젝트",
            description="테스트용 프로젝트입니다",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.test_task = Task(
            id="t1",
            project_id="p1",
            name="테스트 태스크",
            description="테스트용 태스크입니다",
            status=Status.TODO,
            assignee="사용자1",
            due_date=datetime.now().isoformat(),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

    def tearDown(self):
        """테스트 후 정리"""
        pass

    @patch('pmagent.agent.requests.Session')
    def test_init_with_default_session(self, mock_session):
        """기본 세션으로 초기화 테스트"""
        mock_session.return_value = MagicMock()
        agent = PMAgent(url=self.test_url)
        self.assertIsNotNone(agent.session)
        self.assertEqual(agent.url, self.test_url)

    def test_close(self):
        """세션 종료 테스트"""
        self.agent.close()
        self.mock_session.close.assert_called_once()

    @patch('pmagent.agent.PMAgent._make_request')
    def test_list_projects(self, mock_make_request):
        """프로젝트 목록 조회 테스트"""
        mock_make_request.return_value = [self.test_project.dict()]
        projects = self.agent.list_projects()
        
        mock_make_request.assert_called_once_with("GET", "/projects")
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].id, self.test_project.id)
        self.assertEqual(projects[0].name, self.test_project.name)

    @patch('pmagent.agent.PMAgent._make_request')
    def test_get_project(self, mock_make_request):
        """프로젝트 조회 테스트"""
        mock_make_request.return_value = self.test_project.dict()
        project = self.agent.get_project(self.test_project.id)
        
        mock_make_request.assert_called_once_with("GET", f"/projects/{self.test_project.id}")
        self.assertEqual(project.id, self.test_project.id)
        self.assertEqual(project.name, self.test_project.name)

    @patch('pmagent.agent.PMAgent._make_request')
    def test_create_project(self, mock_make_request):
        """프로젝트 생성 테스트"""
        mock_make_request.return_value = self.test_project.dict()
        project_data = {
            "name": self.test_project.name,
            "description": self.test_project.description
        }
        
        project = self.agent.create_project(**project_data)
        
        mock_make_request.assert_called_once_with("POST", "/projects", json=project_data)
        self.assertEqual(project.id, self.test_project.id)
        self.assertEqual(project.name, self.test_project.name)

    @patch('pmagent.agent.PMAgent._make_request')
    def test_update_project(self, mock_make_request):
        """프로젝트 업데이트 테스트"""
        updated_data = self.test_project.dict()
        updated_data["name"] = "업데이트된 프로젝트"
        mock_make_request.return_value = updated_data
        
        update_data = {"name": "업데이트된 프로젝트"}
        project = self.agent.update_project(self.test_project.id, **update_data)
        
        mock_make_request.assert_called_once_with(
            "PUT", f"/projects/{self.test_project.id}", json=update_data
        )
        self.assertEqual(project.id, self.test_project.id)
        self.assertEqual(project.name, "업데이트된 프로젝트")

    @patch('pmagent.agent.PMAgent._make_request')
    def test_delete_project(self, mock_make_request):
        """프로젝트 삭제 테스트"""
        mock_make_request.return_value = {"success": True}
        result = self.agent.delete_project(self.test_project.id)
        
        mock_make_request.assert_called_once_with("DELETE", f"/projects/{self.test_project.id}")
        self.assertTrue(result)

    @patch('pmagent.agent.PMAgent._make_request')
    def test_list_tasks(self, mock_make_request):
        """태스크 목록 조회 테스트"""
        mock_make_request.return_value = [self.test_task.dict()]
        tasks = self.agent.list_tasks(self.test_project.id)
        
        mock_make_request.assert_called_once_with("GET", f"/projects/{self.test_project.id}/tasks")
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, self.test_task.id)
        self.assertEqual(tasks[0].name, self.test_task.name)

    @patch('pmagent.agent.PMAgent._make_request')
    def test_get_task(self, mock_make_request):
        """태스크 조회 테스트"""
        mock_make_request.return_value = self.test_task.dict()
        task = self.agent.get_task(self.test_project.id, self.test_task.id)
        
        mock_make_request.assert_called_once_with(
            "GET", f"/projects/{self.test_project.id}/tasks/{self.test_task.id}"
        )
        self.assertEqual(task.id, self.test_task.id)
        self.assertEqual(task.name, self.test_task.name)

    @patch('pmagent.agent.PMAgent._make_request')
    def test_create_task(self, mock_make_request):
        """태스크 생성 테스트"""
        mock_make_request.return_value = self.test_task.dict()
        task_data = {
            "name": self.test_task.name,
            "description": self.test_task.description,
            "status": self.test_task.status,
            "assignee": self.test_task.assignee,
            "due_date": self.test_task.due_date
        }
        
        task = self.agent.create_task(self.test_project.id, **task_data)
        
        mock_make_request.assert_called_once_with(
            "POST", f"/projects/{self.test_project.id}/tasks", json=task_data
        )
        self.assertEqual(task.id, self.test_task.id)
        self.assertEqual(task.name, self.test_task.name)

    @patch('pmagent.agent.PMAgent._make_request')
    def test_update_task(self, mock_make_request):
        """태스크 업데이트 테스트"""
        updated_data = self.test_task.dict()
        updated_data["status"] = Status.IN_PROGRESS
        mock_make_request.return_value = updated_data
        
        update_data = {"status": Status.IN_PROGRESS}
        task = self.agent.update_task(
            self.test_project.id, self.test_task.id, **update_data
        )
        
        mock_make_request.assert_called_once_with(
            "PUT", 
            f"/projects/{self.test_project.id}/tasks/{self.test_task.id}", 
            json=update_data
        )
        self.assertEqual(task.id, self.test_task.id)
        self.assertEqual(task.status, Status.IN_PROGRESS)

    @patch('pmagent.agent.PMAgent._make_request')
    def test_delete_task(self, mock_make_request):
        """태스크 삭제 테스트"""
        mock_make_request.return_value = {"success": True}
        result = self.agent.delete_task(self.test_project.id, self.test_task.id)
        
        mock_make_request.assert_called_once_with(
            "DELETE", f"/projects/{self.test_project.id}/tasks/{self.test_task.id}"
        )
        self.assertTrue(result)


class TestPMAgentAsync(unittest.TestCase):
    """PMAgent 클래스의 비동기 메서드에 대한 테스트 케이스"""

    def setUp(self):
        """테스트 전 설정"""
        self.mock_session = MagicMock()
        self.test_url = "http://localhost:8000"
        self.agent = PMAgent(url=self.test_url, session=self.mock_session)
        
        # 테스트 데이터
        self.test_project = Project(
            id="p1",
            name="테스트 프로젝트",
            description="테스트용 프로젝트입니다",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.test_task = Task(
            id="t1",
            project_id="p1",
            name="테스트 태스크",
            description="테스트용 태스크입니다",
            status=Status.TODO,
            assignee="사용자1",
            due_date=datetime.now().isoformat(),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

    def tearDown(self):
        """테스트 후 정리"""
        pass

    @patch('pmagent.agent.PMAgent._make_request_async')
    def test_async_list_projects(self, mock_make_request):
        """비동기 프로젝트 목록 조회 테스트"""
        mock_make_request.return_value = asyncio.Future()
        mock_make_request.return_value.set_result([self.test_project.dict()])
        
        async def run_test():
            projects = await self.agent.list_projects_async()
            mock_make_request.assert_called_once_with("GET", "/projects")
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0].id, self.test_project.id)
        
        asyncio.run(run_test())

    @patch('pmagent.agent.PMAgent._make_request_async')
    def test_async_get_project(self, mock_make_request):
        """비동기 프로젝트 조회 테스트"""
        mock_make_request.return_value = asyncio.Future()
        mock_make_request.return_value.set_result(self.test_project.dict())
        
        async def run_test():
            project = await self.agent.get_project_async(self.test_project.id)
            mock_make_request.assert_called_once_with("GET", f"/projects/{self.test_project.id}")
            self.assertEqual(project.id, self.test_project.id)
        
        asyncio.run(run_test())

    @patch('pmagent.agent.PMAgent._make_request_async')
    def test_async_create_project(self, mock_make_request):
        """비동기 프로젝트 생성 테스트"""
        mock_make_request.return_value = asyncio.Future()
        mock_make_request.return_value.set_result(self.test_project.dict())
        
        project_data = {
            "name": self.test_project.name,
            "description": self.test_project.description
        }
        
        async def run_test():
            project = await self.agent.create_project_async(**project_data)
            mock_make_request.assert_called_once_with("POST", "/projects", json=project_data)
            self.assertEqual(project.id, self.test_project.id)
        
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main() 