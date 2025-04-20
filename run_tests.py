#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
테스트 실행 스크립트
"""

import sys
import pytest

if __name__ == "__main__":
    # 테스트 디렉토리 지정
    test_path = "tests"
    
    # 명령행 인자로 특정 테스트 파일이나 옵션을 전달할 수 있음
    args = ["-v", test_path]
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    
    # 테스트 실행
    sys.exit(pytest.main(args)) 