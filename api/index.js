// PM 에이전트 MCP 서버 - 메인 서버리스 함수
import express from 'express';
import cors from 'cors';
import morgan from 'morgan';

// Express 앱 생성
const app = express();

// 미들웨어 설정
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(morgan('dev'));

// MCP 서버 정보
const serverInfo = {
  qualifiedName: 'pmagent-mcp-server',
  displayName: 'PM 에이전트 MCP 서버',
  description: 'PM 에이전트 시스템을 위한 MCP 서버입니다.',
  version: '1.0.0',
};

// 기본 라우트
app.get('/', (req, res) => {
  res.json({
    name: serverInfo.displayName,
    description: serverInfo.description,
    version: serverInfo.version,
    status: 'online',
  });
});

// MCP 서버 정보 엔드포인트
app.get('/api/mcp/info', (req, res) => {
  res.json(serverInfo);
});

// MCP 서버 도구 목록 엔드포인트
app.get('/api/mcp/tools', (req, res) => {
  res.json({
    tools: [
      // PM 에이전트 도구
      {
        name: 'create_project',
        description: '새로운 프로젝트를 생성합니다.',
        category: 'pm'
      },
      {
        name: 'assign_task',
        description: '특정 에이전트에게 작업을 할당합니다.',
        category: 'pm'
      },
      {
        name: 'get_project_status',
        description: '현재 프로젝트 상태를 가져옵니다.',
        category: 'pm'
      },
      
      // 기타 도구들...
      {
        name: 'create_design',
        description: '새로운 디자인을 생성합니다.',
        category: 'designer'
      },
      {
        name: 'create_component',
        description: '새로운 UI 컴포넌트를 생성합니다.',
        category: 'frontend'
      }
    ]
  });
});

// 에러 핸들링 미들웨어
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    status: 'error',
    message: err.message || '서버 내부 오류',
  });
});

// Vercel 서버리스 함수
export default function handler(req, res) {
  // GET 메서드만 허용
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Express 앱으로 요청 전달
  return app(req, res);
} 