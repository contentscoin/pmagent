"""
에이전트 기본 도구(Tool) 클래스 모듈
"""

from typing import Dict, Any, Optional

class BaseTool:
    """
    모든 도구(Tool)의 기본 클래스
    """
    
    name = "base_tool"
    description = "기본 도구 클래스"
    
    def __init__(self, **kwargs):
        """
        기본 도구 초기화
        """
        pass
    
    def _run(self, task: Dict[str, Any]) -> Any:
        """
        도구를 실행합니다. 하위 클래스에서 구현해야 합니다.
        
        Args:
            task (Dict[str, Any]): 작업 정보
            
        Returns:
            Any: 작업 결과
        """
        raise NotImplementedError("이 메서드는 하위 클래스에서 구현해야 합니다.")
    
    def run_task(self, task_description: str) -> Any:
        """
        작업 설명을 받아 도구를 실행합니다.
        
        Args:
            task_description (str): 작업 설명
            
        Returns:
            Any: 작업 결과
        """
        if isinstance(task_description, str):
            task = {"task": task_description}
        else:
            task = task_description
            
        return self._run(task) 