from pmagent.server import app

# Vercel 서버리스 기능을 위한 핸들러
handler = app

# 로컬 개발 환경에서 실행할 경우
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("index:app", host="0.0.0.0", port=8082, reload=True) 