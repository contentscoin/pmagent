// PM 에이전트 MCP 서버 - 메인 파일
import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import { readdirSync } from 'fs';
import dotenv from 'dotenv';
import { connectDatabase } from './config/database.js';

// ES 모듈 경로 설정
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 환경 변수 설정 (.env 파일이 있으면 로드)
dotenv.config({ path: join(dirname(__dirname), '.env') });

// 라우트 임포트
import pmRoutes from './routes/pm-agent.js';
import designerRoutes from './routes/designer-agent.js';
import frontendRoutes from './routes/frontend-agent.js';
import backendRoutes from './routes/backend-agent.js';
import aiEngineerRoutes from './routes/ai-engineer-agent.js';
import serviceRoutes from './routes/services.js';
import projectManagerRoutes from './routes/project-manager-agent.js';
import authRoutes from './routes/auth.js';

// Express 앱 생성
const app = express();
const PORT = process.env.PORT || 4000;

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
      
      // 디자이너 에이전트 도구
      {
        name: 'create_design',
        description: '새로운 디자인을 생성합니다.',
        category: 'designer'
      },
      {
        name: 'get_design_system',
        description: '디자인 시스템 정보를 가져옵니다.',
        category: 'designer'
      },
      
      // 프론트엔드 에이전트 도구
      {
        name: 'create_component',
        description: '새로운 UI 컴포넌트를 생성합니다.',
        category: 'frontend'
      },
      {
        name: 'implement_screen',
        description: '화면 구현을 수행합니다.',
        category: 'frontend'
      },
      
      // 백엔드 에이전트 도구
      {
        name: 'create_api',
        description: '새로운 API 엔드포인트를 생성합니다.',
        category: 'backend'
      },
      {
        name: 'design_database',
        description: '데이터베이스 스키마를 설계합니다.',
        category: 'backend'
      },
      
      // AI 엔지니어 에이전트 도구
      {
        name: 'create_ml_model',
        description: '새로운 머신러닝 모델을 생성합니다.',
        category: 'ai_engineer'
      },
      {
        name: 'analyze_data',
        description: '데이터 분석을 수행합니다.',
        category: 'ai_engineer'
      },
      
      // 프로젝트 매니저 에이전트 도구
      {
        name: 'create_project_pm',
        description: '새로운 프로젝트를 생성합니다.',
        category: 'project_manager'
      },
      {
        name: 'assign_task_pm',
        description: '작업을 할당합니다.',
        category: 'project_manager'
      },
      {
        name: 'create_sprint',
        description: '새로운 스프린트를 생성합니다.',
        category: 'project_manager'
      },
      {
        name: 'add_team_member',
        description: '팀원을 추가합니다.',
        category: 'project_manager'
      },
      {
        name: 'project_report',
        description: '프로젝트 리포트를 생성합니다.',
        category: 'project_manager'
      },
      
      // 인증 관련 도구
      {
        name: 'register_user',
        description: '새로운 사용자를 등록합니다.',
        category: 'auth'
      },
      {
        name: 'login',
        description: '사용자 로그인을 수행합니다.',
        category: 'auth'
      },
      {
        name: 'logout',
        description: '사용자 로그아웃을 수행합니다.',
        category: 'auth'
      },
      
      // 외부 서비스 연동 도구
      {
        name: 'github_commit',
        description: 'GitHub에 코드를 커밋합니다.',
        category: 'service'
      },
      {
        name: 'figma_export',
        description: 'Figma에서 디자인을 내보냅니다.',
        category: 'service'
      },
      {
        name: 'query_database',
        description: '데이터베이스에 쿼리를 실행합니다.',
        category: 'service'
      }
    ]
  });
});

// 에이전트 라우트 등록
app.use('/api/mcp/pm', pmRoutes);
app.use('/api/mcp/designer', designerRoutes);
app.use('/api/mcp/frontend', frontendRoutes);
app.use('/api/mcp/backend', backendRoutes);
app.use('/api/mcp/ai-engineer', aiEngineerRoutes);
app.use('/api/mcp/services', serviceRoutes);
app.use('/api/mcp/project-manager', projectManagerRoutes);
app.use('/api/auth', authRoutes);

// 에러 핸들링 미들웨어
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    status: 'error',
    message: err.message || '서버 내부 오류',
  });
});

// 서버 시작 함수
const startServer = async () => {
  try {
    // MongoDB 연결 시도 생략 - 인메모리 모드로 바로 시작
    console.warn('⚠️ 인-메모리 모드로 실행합니다');
    
    // 서버 시작
    app.listen(PORT, () => {
      console.log(`🚀 PM 에이전트 MCP 서버가 http://localhost:${PORT} 에서 실행 중입니다.`);
      console.log(`💾 데이터 저장소: 인-메모리 데이터베이스 사용 중`);
    });
  } catch (error) {
    console.error('서버 시작 실패:', error);
    process.exit(1);
  }
};

// 로컬 환경에서만 서버 시작
if (process.env.NODE_ENV !== 'production') {
  startServer();
} else {
  // Vercel 환경에서는 자동으로 시작
  // MongoDB 연결 시도 생략 - Vercel에서는 serverless로 동작
  console.warn('⚠️ Vercel 서버리스 환경에서 실행됩니다');
}

// Vercel 서버리스 함수를 위한 export
export default app;