#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PMAgent MCP 서버 실행 스크립트

이 스크립트는 PMAgent MCP 서버를 실행합니다.
기본적으로 서버는 http://localhost:8082에서 실행됩니다.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

from pmagent import start_server

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pmagent_server.log")
    ]
)
logger = logging.getLogger(__name__)

def main():
    """서버 실행 메인 함수"""
    parser = argparse.ArgumentParser(description="PMAgent MCP 서버 실행")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="호스트 주소 (기본값: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8082, help="포트 번호 (기본값: 8082)")
    parser.add_argument("--data-dir", type=str, help="데이터 디렉토리 경로")
    
    args = parser.parse_args()
    
    # 환경 변수 설정
    if args.data_dir:
        os.environ["DATA_DIR"] = args.data_dir
    
    # 서버 시작
    try:
        logger.info(f"PMAgent MCP 서버를 시작합니다 (http://{args.host}:{args.port})")
        start_server(host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("서버가 종료되었습니다.")
    except Exception as e:
        logger.error(f"서버 실행 중 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 