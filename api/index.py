from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import logging
import json
import traceback

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error") # Vercel에서 FastAPI 로그를 보려면 uvicorn 로거 사용

app = FastAPI()

@app.get("/")
async def root():
    logger.info("루트 경로 요청 받음")
    return {"message": "PM Agent MCP Server is running!"}

@app.post("/api")
async def api_endpoint(request: Request):
    request_id = None # id 초기화
    try:
        logger.info("API 요청 받음")
        data = await request.json()
        request_id = data.get("id")
        method = data.get("method", "")
        logger.info(f"요청된 메서드: {method}")
        
        # rpc.discover 메서드 처리
        if method == "rpc.discover":
            logger.info("rpc.discover 처리 중")
            response_data = {
                "jsonrpc": "2.0",
                "result": {
                    "name": "pmagent",
                    "version": "0.1.0",
                    "description": "PM Agent MCP Server (Test Description)",
                    "methods": [
                        {
                            "name": "test_method",
                            "description": "A simple test method.",
                            "parameters": {}
                        }
                    ]
                },
                "id": request_id
            }
            logger.info("rpc.discover 응답 생성 완료")
            return JSONResponse(content=response_data)
        
        # 기본 응답
        logger.warning(f"알 수 없는 메서드 호출: {method}")
        response_data = {
            "jsonrpc": "2.0",
            "result": {
                "message": "Method not implemented",
                "method": method
            },
            "id": request_id
        }
        return JSONResponse(content=response_data)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 디코드 오류: {str(e)}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Invalid JSON format"},
                "id": request_id
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"내부 서버 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal server error: {str(e)}"
                },
                "id": request_id
            },
            status_code=500
        )

@app.get("/smithery-simple.json")
async def get_smithery_simple():
    logger.info("Smithery 메타데이터 요청 받음")
    return {
        "qualifiedName": "pmagent",
        "displayName": "PM Agent MCP Server",
        "description": "Project Management MCP Server",
        "version": "0.1.0",
        "transport": {
            "type": "http",
            "jsonrpc": {
                "endpoint": "/api"
            }
        }
    }

# Vercel 핸들러는 app 객체 자체여야 합니다.
# handler = app # 이 줄은 필요 없습니다.

# 로컬 개발 환경 실행 (Vercel 배포 시에는 사용되지 않음)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082, reload=True) 