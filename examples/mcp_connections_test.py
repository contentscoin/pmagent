"""
MCP 연결 테스트 스크립트

이 스크립트는 다양한 MCP(Model Context Protocol) 연결을 테스트하고 결과를 파일에 기록합니다.
GitHub, Figma, 데이터베이스 MCP 연결을 확인합니다.
"""

import os
import sys
import json
from datetime import datetime

# agents 디렉토리를 Python 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# MCP Agent Helper 임포트
from agents.mcp_agent_helper import MCPAgentHelper

def get_env_or_default(env_name, default_value=None):
    """환경 변수를 가져오거나 기본값 반환"""
    return os.environ.get(env_name, default_value)

def main():
    # 결과를 저장할 파일 설정
    output_file = "mcp_test_results.txt"
    
    # 현재 시간 가져오기
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 결과를 저장할 리스트
    results = [f"MCP 연결 테스트 결과 - {current_time}\n"]
    results.append("=" * 50 + "\n")
    
    try:
        # 토큰 및 연결 문자열 가져오기
        github_token = get_env_or_default("GITHUB_TOKEN", "sample_github_token")
        figma_token = get_env_or_default("FIGMA_TOKEN", "sample_figma_token")
        db_connection_string = get_env_or_default("DB_CONNECTION_STRING", "sqlite:///test.db")
        
        # MCP 에이전트 헬퍼 초기화
        results.append("MCP 에이전트 헬퍼 초기화 중...\n")
        mcp_helper = MCPAgentHelper(
            github_token=github_token,
            figma_token=figma_token,
            db_connection_string=db_connection_string
        )
        
        # 사용 가능한 MCP 확인
        available_mcps = mcp_helper.get_available_mcps()
        results.append("\n사용 가능한 MCP:\n")
        for mcp_name, available in available_mcps.items():
            status = "사용 가능" if available else "사용 불가"
            results.append(f"- {mcp_name}: {status}\n")
        
        # Figma 설정 파일 확인
        figma_config_path = "figma-mcp-config.json"
        if os.path.exists(figma_config_path):
            try:
                with open(figma_config_path, 'r') as f:
                    figma_config = json.load(f)
                results.append(f"\nFigma MCP 설정 파일 확인: {figma_config_path}\n")
                results.append(f"설정 내용: {json.dumps(figma_config, indent=2, ensure_ascii=False)}\n")
            except Exception as e:
                results.append(f"\nFigma MCP 설정 파일 읽기 오류: {str(e)}\n")
        else:
            results.append(f"\nFigma MCP 설정 파일이 존재하지 않습니다: {figma_config_path}\n")
        
        # GitHub MCP 테스트
        results.append("\nGitHub MCP 테스트:\n")
        if mcp_helper.has_github_mcp():
            try:
                github_result = mcp_helper.commit_to_github(
                    "src/components/Button.js", 
                    "Add Button component with styling",
                    file_content="// Button component\nfunction Button(props) {\n  return <button className='btn' {...props}>{props.children}</button>;\n}\n\nexport default Button;"
                )
                results.append(f"GitHub 커밋 결과: {github_result}\n")
            except Exception as e:
                results.append(f"GitHub MCP 오류: {str(e)}\n")
        else:
            results.append("GitHub MCP를 사용할 수 없습니다.\n")
        
        # Figma MCP 테스트
        results.append("\nFigma MCP 테스트:\n")
        if mcp_helper.has_figma_mcp():
            try:
                figma_result = mcp_helper.get_design_data("https://figma.com/file/example")
                results.append(f"Figma 디자인 데이터: {json.dumps(figma_result, indent=2, ensure_ascii=False)}\n")
            except Exception as e:
                results.append(f"Figma MCP 오류: {str(e)}\n")
        else:
            results.append("Figma MCP를 사용할 수 없습니다.\n")
        
        # DB MCP 테스트
        results.append("\n데이터베이스 MCP 테스트:\n")
        if mcp_helper.has_db_mcp():
            try:
                sql_result = mcp_helper.execute_sql("SELECT * FROM users LIMIT 10")
                results.append(f"SQL 쿼리 결과: {sql_result}\n")
            except Exception as e:
                results.append(f"DB MCP 오류: {str(e)}\n")
        else:
            results.append("DB MCP를 사용할 수 없습니다.\n")
            
    except Exception as e:
        results.append(f"\n테스트 실행 중 오류 발생: {str(e)}\n")
    
    # 결과 저장
    results.append("\n" + "=" * 50 + "\n")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(results)
    
    print(f"MCP 연결 테스트 완료. 결과가 {output_file}에 저장되었습니다.")

if __name__ == "__main__":
    main() 