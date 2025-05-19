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
import socket
import psutil # psutil 임포트
from dotenv import load_dotenv
import uvicorn
import traceback

# 환경 변수 로드
load_dotenv()

# Koyeb 환경에서 안정성을 위해 WEB_CONCURRENCY 환경 변수 설정
# 기본값 설정 - 환경 변수에 이미 설정된 경우에는 덮어쓰지 않음
if os.environ.get("KOYEB_APP_NAME") and not os.environ.get("WEB_CONCURRENCY"):
    os.environ["WEB_CONCURRENCY"] = "1"
    print(f"Koyeb 환경 감지: WEB_CONCURRENCY를 1로 설정합니다.")

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pmagent.mcp_server import start_server

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

def check_and_kill_process_on_port(host: str, port: int):
    """지정된 호스트와 포트를 사용하는 프로세스를 확인하고, 필요시 종료합니다. (net_connections 사용)"""
    processes_found_on_port = {}

    try:
        # 시스템 전체의 인터넷 연결 목록을 가져옴 (net_connections 사용)
        all_conns = psutil.net_connections(kind='inet')
    except psutil.AccessDenied:
        logger.warning("네트워크 연결 정보를 가져오는 데 필요한 권한이 없습니다. 포트 확인을 건너뜁니다.")
        return
    except Exception as e:
        logger.error(f"net_connections 호출 중 오류 발생: {e}")
        return

    for conn in all_conns:
        # laddr (local address)의 포트가 일치하고, 상태가 LISTEN인지 확인
        # conn.laddr이 None이 아닌지 먼저 확인 (일부 연결 유형에 없을 수 있음)
        if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
            # host가 '0.0.0.0'이면 모든 IP에서의 리슨을 고려
            is_correct_host = (conn.laddr.ip == host) or \
                              (host == '0.0.0.0' and conn.laddr.ip in ['0.0.0.0', '127.0.0.1', '::']) or \
                              (host == '127.0.0.1' and conn.laddr.ip == '0.0.0.0') # 0.0.0.0 리슨은 localhost 요청도 받음
            
            if is_correct_host and conn.pid is not None:
                # 이미 처리한 PID인지 확인
                if conn.pid in processes_found_on_port:
                    continue
                
                try:
                    proc = psutil.Process(conn.pid)
                    # 프로세스 정보를 딕셔너리에 저장 (PID를 키로 사용)
                    processes_found_on_port[conn.pid] = proc 
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    logger.debug(f"PID {conn.pid}에 대한 프로세스 정보를 얻을 수 없습니다.")
                    continue

    if processes_found_on_port:
        logger.warning(f"포트 {port}가 이미 사용 중입니다.")
        # values() 대신 items()를 사용하여 pid와 proc 객체를 함께 얻음
        for pid, proc in processes_found_on_port.items():
            try:
                proc_name = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                proc_name = "(이름 확인 불가)"
                
            proc_info_str = f"PID: {pid}, Name: {proc_name}"
            logger.info(f"포트 {port}를 사용 중인 프로세스: {proc_info_str}")
            try:
                user_input = input(f"  프로세스 {proc_info_str}를 종료하시겠습니까? (y/n): ").lower().strip()
                if user_input == 'y':
                    logger.info(f"  프로세스 {pid} 종료 시도...")
                    proc.terminate() # 먼저 정상 종료 시도
                    try:
                        proc.wait(timeout=3) # 종료 대기
                        logger.info(f"  프로세스 {pid}가 성공적으로 terminate 되었습니다.")
                    except psutil.TimeoutExpired:
                        logger.warning(f"  프로세스 {pid}가 terminate에 응답하지 않아 kill합니다.")
                        proc.kill() # 강제 종료
                        proc.wait() # 강제 종료 후 대기
                        logger.info(f"  프로세스 {pid}가 강제 종료되었습니다.")
                else:
                    logger.info("  프로세스 종료를 취소했습니다. 서버를 시작할 수 없습니다.")
                    sys.exit(1)
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e_proc:
                logger.error(f"  프로세스 {pid} 처리 중 오류: {e_proc}")
            except EOFError:
                 logger.warning("사용자 입력을 받을 수 없는 환경입니다. 프로세스를 종료하지 않고 진행합니다.")
            except Exception as e_input: 
                logger.error(f"  입력 처리 중 오류 또는 중단: {e_input}")
                sys.exit(1)
    else:
        logger.info(f"포트 {port}는 현재 사용 중이지 않습니다.")

def main():
    """서버 실행 메인 함수"""
    parser = argparse.ArgumentParser(description="PMAgent MCP 서버 실행")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="호스트 주소 (기본값: 0.0.0.0)")
    # Koyeb PORT 환경 변수를 우선적으로 사용하도록 포트 인자 처리 수정
    default_port = int(os.environ.get("PORT", 8080)) # Koyeb 기본 포트는 8080일 수 있음
    parser.add_argument("--port", type=int, default=default_port, help=f"포트 번호 (기본값: {default_port} 또는 PORT 환경 변수)")
    parser.add_argument("--data-dir", type=str, help="데이터 디렉토리 경로")
    parser.add_argument("--log-level", type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default=os.environ.get("LOG_LEVEL", "INFO"), help="로깅 레벨 설정")
    
    args = parser.parse_args()
    
    # 로그 레벨 설정
    log_level = getattr(logging, args.log_level)
    logger.setLevel(log_level)
    logging.getLogger("uvicorn").setLevel(log_level)
    
    # 최종 사용할 호스트 및 포트 결정
    # 명령줄 인수가 환경 변수보다 우선순위가 높도록 하려면 아래와 같이 조정 가능
    # 하지만 Koyeb에서는 환경 변수가 우선되어야 하므로, args.port는 기본값으로만 사용
    host_to_use = args.host
    port_to_use = args.port # 기본적으로 parser에서 PORT 환경 변수를 이미 반영했거나 기본값을 가짐
    
    # Koyeb 환경에서 실행 중인지 로깅
    if os.environ.get("KOYEB_APP_NAME"):
        logger.info(f"Koyeb 환경에서 실행 중: {os.environ.get('KOYEB_APP_NAME')}")
        logger.info(f"PORT 환경 변수: {os.environ.get('PORT')}")
        logger.info(f"WEB_CONCURRENCY 환경 변수: {os.environ.get('WEB_CONCURRENCY')}")
    
    # 환경 변수 설정
    if args.data_dir:
        os.environ["DATA_DIR"] = args.data_dir
        logger.info(f"DATA_DIR 환경 변수 설정: {args.data_dir}")

    # 서버 시작 전 포트 확인 및 프로세스 정리 (Koyeb 환경에서는 주석 처리 유지)
    if os.environ.get("KOYEB_APP_NAME") is None: # 로컬 환경에서만 실행하도록 조건 추가 가능
       logger.info(f"로컬 환경에서 포트 {port_to_use} 사용 가능 여부 확인 중...")
       check_and_kill_process_on_port(host_to_use, port_to_use)
    
    # 서버 시작
    try:
        logger.info(f"PMAgent MCP 서버를 시작합니다 (http://{host_to_use}:{port_to_use})")
        # Uvicorn 설정 - log_level 인수 추가
        uvicorn_config = {
            "host": host_to_use,
            "port": port_to_use,
            "reload": False,
            "log_level": args.log_level.lower()
        }
        
        # Koyeb에서는 종료 시간을 늘림
        if os.environ.get("KOYEB_APP_NAME"):
            uvicorn_config["timeout_keep_alive"] = 120  # 기본값은 5초지만 Koyeb에서는 더 길게 설정
        
        # uvicorn.run() 호출 시 애플리케이션 객체 대신 임포트 문자열 사용
        logger.info(f"Uvicorn 설정: {uvicorn_config}")
        uvicorn.run("pmagent.mcp_server:app", **uvicorn_config)
    except KeyboardInterrupt:
        logger.info("서버가 종료되었습니다.")
    except Exception as e: 
        logger.error(f"서버 실행 중 오류 발생: {e}")
        logger.error(f"상세 오류 정보: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main() 