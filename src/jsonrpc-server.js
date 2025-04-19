// MCP JSON-RPC 2.0 서버 구현
import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import bodyParser from 'body-parser';

// Express 앱 생성
const app = express();
const PORT = process.env.PORT || 4000;

// 미들웨어 설정
app.use(cors());
app.use(bodyParser.json());
app.use(morgan('dev'));

// MCP 서버 정보
const serverInfo = {
  name: 'pmagent-mcp-server',
  displayName: 'PM 에이전트 MCP 서버',
  description: 'PM 에이전트 시스템을 위한 MCP 서버입니다.',
  version: '1.0.0',
  transport: 'jsonrpc',
  startCommand: 'npm start'
};

// 도구 목록
const tools = [
  {
    name: 'create_project',
    description: '새로운 프로젝트를 생성합니다.',
    parameters: {
      type: 'object',
      properties: {
        name: {
          type: 'string',
          description: '프로젝트 이름'
        },
        description: {
          type: 'string',
          description: '프로젝트 설명'
        }
      },
      required: ['name']
    }
  },
  {
    name: 'assign_task',
    description: '특정 에이전트에게 작업을 할당합니다.',
    parameters: {
      type: 'object',
      properties: {
        taskId: {
          type: 'string',
          description: '작업 ID'
        },
        agentType: {
          type: 'string',
          description: '에이전트 유형 (designer, frontend, backend, ai_engineer)'
        }
      },
      required: ['taskId', 'agentType']
    }
  },
  {
    name: 'get_project_status',
    description: '현재 프로젝트 상태를 가져옵니다.',
    parameters: {
      type: 'object',
      properties: {
        projectId: {
          type: 'string',
          description: '프로젝트 ID'
        }
      },
      required: ['projectId']
    }
  }
];

// JSON-RPC 응답 생성 함수
function createResponse(id, result) {
  return {
    jsonrpc: '2.0',
    id,
    result
  };
}

// JSON-RPC 오류 응답 생성 함수
function createErrorResponse(id, code, message) {
  return {
    jsonrpc: '2.0',
    id,
    error: {
      code,
      message
    }
  };
}

// JSON-RPC 엔드포인트
app.post('/api/jsonrpc', (req, res) => {
  const { id, method, params } = req.body;

  console.log(`JSON-RPC 요청: ${method}`, params);

  // 메서드에 따른 처리
  switch (method) {
    case 'initialize':
      res.json(createResponse(id, serverInfo));
      break;

    case 'tools/list':
      res.json(createResponse(id, { tools }));
      break;

    case 'tools/call':
      // 도구 호출 처리
      const { tool, parameters } = params;
      
      // 도구 확인
      const toolDef = tools.find(t => t.name === tool);
      if (!toolDef) {
        res.json(createErrorResponse(id, -32601, `도구를 찾을 수 없음: ${tool}`));
        return;
      }

      // 여기서 실제 도구 로직을 구현하세요
      // 지금은 더미 응답만 반환합니다
      let result;
      
      switch (tool) {
        case 'create_project':
          result = { 
            projectId: `proj-${Date.now()}`,
            name: parameters.name,
            description: parameters.description || '설명 없음',
            createdAt: new Date().toISOString()
          };
          break;
          
        case 'assign_task':
          result = {
            taskId: parameters.taskId,
            assignedTo: parameters.agentType,
            status: 'assigned',
            assignedAt: new Date().toISOString()
          };
          break;
          
        case 'get_project_status':
          result = {
            projectId: parameters.projectId,
            status: 'in_progress',
            completedTasks: 2,
            totalTasks: 5,
            lastUpdated: new Date().toISOString()
          };
          break;
          
        default:
          res.json(createErrorResponse(id, -32601, `도구 구현을 찾을 수 없음: ${tool}`));
          return;
      }
      
      res.json(createResponse(id, { result }));
      break;

    default:
      res.json(createErrorResponse(id, -32601, `메서드를 찾을 수 없음: ${method}`));
  }
});

// 루트 경로
app.get('/', (req, res) => {
  res.json({
    name: serverInfo.displayName,
    description: serverInfo.description,
    version: serverInfo.version,
    status: 'online',
    jsonRpcEndpoint: '/api/jsonrpc'
  });
});

// 서버 시작
app.listen(PORT, () => {
  console.log(`🚀 MCP JSON-RPC 서버가 http://localhost:${PORT} 에서 실행 중입니다.`);
});

export default app; 