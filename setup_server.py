#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent 서버 설정 스크립트

이 스크립트는 PMAgent 서버를 설정하고 실행하는 데 필요한 단계를 수행합니다.
"""

import os
import sys
import subprocess
import shutil
import importlib
from pathlib import Path

def check_requirements():
    """필요한 패키지가 설치되어 있는지 확인합니다."""
    print("필요한 패키지 확인 중...")
    
    required_packages = ["uvicorn", "fastapi", "pydantic", "aiohttp", "requests"]
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package} 설치됨")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} 설치되지 않음")
    
    if missing_packages:
        print("\n패키지 설치 중...")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("패키지 설치 완료")

def check_pmagent_structure():
    """PMAgent 패키지 구조가 올바른지 확인합니다."""
    print("\nPMAgent 패키지 구조 확인 중...")
    
    root_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    pmagent_dir = root_dir / "pmagent"
    
    if not pmagent_dir.exists():
        print(f"✗ pmagent 디렉토리를 찾을 수 없습니다. 현재 경로: {root_dir}")
        return False
    
    # 필수 파일 확인
    required_files = ["__init__.py", "agent.py", "server.py", "test_client.py"]
    missing_files = []
    
    for filename in required_files:
        file_path = pmagent_dir / filename
        if not file_path.exists():
            missing_files.append(filename)
            print(f"✗ {filename} 파일을 찾을 수 없습니다.")
        else:
            print(f"✓ {filename} 파일 존재")
    
    if missing_files:
        print(f"\n다음 파일이 없습니다: {', '.join(missing_files)}")
        print("해당 파일을 생성하거나 복원해 주세요.")
        return False
    
    return True

def install_package():
    """패키지를 개발자 모드로 설치합니다."""
    print("\nPMAgent 패키지 설치 중...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ 패키지 설치 성공")
        return True
    else:
        print(f"✗ 패키지 설치 실패: {result.stderr}")
        return False

def create_data_directory():
    """데이터 디렉토리를 생성합니다."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    print(f"✓ 데이터 디렉토리 생성됨: {data_dir.absolute()}")

def run_server():
    """PMAgent 서버를 실행합니다."""
    print("\nPMAgent 서버를 실행하는 명령어:")
    print("python -m pmagent.server")
    
    proceed = input("\n서버를 지금 실행하시겠습니까? (y/n): ")
    if proceed.lower() == 'y':
        print("\nPMAgent 서버 실행 중...")
        print("Ctrl+C를 눌러 서버를 중지할 수 있습니다.\n")
        subprocess.run([sys.executable, "-m", "pmagent.server"])
    else:
        print("\n서버를 실행하려면 위 명령어를 사용하세요.")

def main():
    """메인 함수"""
    print("PMAgent 서버 설정 시작\n")
    
    # 필요한 패키지 확인 및 설치
    check_requirements()
    
    # 패키지 구조 확인
    if not check_pmagent_structure():
        print("\n패키지 구조에 문제가 있습니다. 먼저 이 문제를 해결하세요.")
        return
    
    # 패키지 설치
    if not install_package():
        print("\n패키지 설치에 실패했습니다. 위 오류를 확인하세요.")
        return
    
    # 데이터 디렉토리 생성
    create_data_directory()
    
    # 서버 실행
    run_server()

if __name__ == "__main__":
    main() 