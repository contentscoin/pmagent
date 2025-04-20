// PM 에이전트 MCP 서버 - 메인 서버리스 함수
import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

// __dirname 구현 (ES 모듈에서는 __dirname이 기본적으로 없음)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Express 앱 생성
const app = express();

// 미들웨어 설정
app.use(cors({
  origin: ['https://smithery.ai', 'https://www.smithery.ai', '*'],
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
}));
app.use(express.json({ limit: '10mb' }));
app.use(morgan('dev'));

// 정적 파일 제공
app.use('/static', express.static(path.join(__dirname, '../public')));

// MCP 서버 정보
const serverInfo = {
  qualifiedName: 'pmagent-mcp-server',
  displayName: 'PM 에이전트 MCP 서버',
  description: 'PM 에이전트 시스템을 위한 MCP 서버입니다.',
  version: '1.0.0',
};

// smithery-simple.json 파일 제공
app.get('/smithery-simple.json', (req, res) => {
  const smitheryPath = path.join(__dirname, '../smithery-simple.json');
  
  // 파일이 존재하는지 확인
  if (fs.existsSync(smitheryPath)) {
    res.sendFile(smitheryPath);
  } else {
    // 파일이 없으면 직접 JSON 응답 제공
    res.json({
      qualifiedName: "pmagent",
      displayName: "PM Agent MCP Server",
      description: "프로젝트 관리를 위한 MCP(Model Context Protocol) 서버",
      version: "0.1.0",
      baseUrl: "https://pmagent.vercel.app"
    });
  }
});

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

// MCP 서버 도구 목록 엔드포인트 - /tools 경로 추가
app.get('/tools', (req, res) => {
  res.json({
    "tools": [
      {
        "name": "list_projects",
        "description": "프로젝트 목록을 가져옵니다.",
        "parameters": {
          "properties": {},
          "required": []
        }
      },
      {
        "name": "create_project",
        "description": "새 프로젝트를 생성합니다.",
        "parameters": {
          "properties": {
            "name": {
              "type": "string",
              "description": "프로젝트 이름"
            },
            "description": {
              "type": "string",
              "description": "프로젝트 설명 (선택)"
            }
          },
          "required": ["name"]
        }
      },
      {
        "name": "get_project",
        "description": "프로젝트 정보를 가져옵니다.",
        "parameters": {
          "properties": {
            "project_id": {
              "type": "string",
              "description": "프로젝트 ID"
            }
          },
          "required": ["project_id"]
        }
      },
      {
        "name": "update_project",
        "description": "프로젝트 정보를 업데이트합니다.",
        "parameters": {
          "properties": {
            "project_id": {
              "type": "string",
              "description": "프로젝트 ID"
            },
            "name": {
              "type": "string",
              "description": "새 프로젝트 이름 (선택)"
            },
            "description": {
              "type": "string",
              "description": "새 프로젝트 설명 (선택)"
            }
          },
          "required": ["project_id"]
        }
      },
      {
        "name": "delete_project",
        "description": "프로젝트를 삭제합니다.",
        "parameters": {
          "properties": {
            "project_id": {
              "type": "string",
              "description": "프로젝트 ID"
            }
          },
          "required": ["project_id"]
        }
      },
      {
        "name": "list_tasks",
        "description": "프로젝트의 모든 태스크 목록을 가져옵니다.",
        "parameters": {
          "properties": {
            "project_id": {
              "type": "string",
              "description": "프로젝트 ID"
            }
          },
          "required": ["project_id"]
        }
      },
      {
        "name": "create_task",
        "description": "새 태스크를 생성합니다.",
        "parameters": {
          "properties": {
            "project_id": {
              "type": "string",
              "description": "프로젝트 ID"
            },
            "name": {
              "type": "string",
              "description": "태스크 이름"
            },
            "description": {
              "type": "string",
              "description": "태스크 설명 (선택)"
            },
            "status": {
              "type": "string",
              "description": "태스크 상태 (선택, 기본값: 'TODO')"
            },
            "due_date": {
              "type": "string",
              "description": "마감일 (선택, ISO 형식)"
            },
            "assignee": {
              "type": "string",
              "description": "담당자 (선택)"
            }
          },
          "required": ["project_id", "name"]
        }
      },
      {
        "name": "get_task",
        "description": "태스크 정보를 가져옵니다.",
        "parameters": {
          "properties": {
            "project_id": {
              "type": "string",
              "description": "프로젝트 ID"
            },
            "task_id": {
              "type": "string",
              "description": "태스크 ID"
            }
          },
          "required": ["project_id", "task_id"]
        }
      },
      {
        "name": "update_task",
        "description": "태스크 정보를 업데이트합니다.",
        "parameters": {
          "properties": {
            "project_id": {
              "type": "string",
              "description": "프로젝트 ID"
            },
            "task_id": {
              "type": "string",
              "description": "태스크 ID"
            },
            "name": {
              "type": "string",
              "description": "새 태스크 이름 (선택)"
            },
            "description": {
              "type": "string",
              "description": "새 태스크 설명 (선택)"
            },
            "status": {
              "type": "string",
              "description": "새 태스크 상태 (선택)"
            },
            "due_date": {
              "type": "string",
              "description": "새 마감일 (선택, ISO 형식)"
            },
            "assignee": {
              "type": "string",
              "description": "새 담당자 (선택)"
            }
          },
          "required": ["project_id", "task_id"]
        }
      },
      {
        "name": "delete_task",
        "description": "태스크를 삭제합니다.",
        "parameters": {
          "properties": {
            "project_id": {
              "type": "string",
              "description": "프로젝트 ID"
            },
            "task_id": {
              "type": "string",
              "description": "태스크 ID"
            }
          },
          "required": ["project_id", "task_id"]
        }
      }
    ]
  });
});

// MCP 도구 호출 엔드포인트 추가
app.post('/invoke', (req, res) => {
  const { name, parameters } = req.body;
  
  if (!name) {
    return res.status(400).json({
      status: 'error',
      message: '도구 이름이 필요합니다.'
    });
  }
  
  // 모의 응답 (실제 구현이 아닌 데모용)
  switch (name) {
    case 'list_projects':
      return res.json({
        "projects": [
          {
            "id": "project-1",
            "name": "샘플 프로젝트 1",
            "description": "첫 번째 샘플 프로젝트입니다.",
            "created_at": new Date().toISOString(),
            "updated_at": new Date().toISOString()
          },
          {
            "id": "project-2",
            "name": "샘플 프로젝트 2",
            "description": "두 번째 샘플 프로젝트입니다.",
            "created_at": new Date(Date.now() - 86400000).toISOString(),
            "updated_at": new Date(Date.now() - 86400000).toISOString()
          }
        ]
      });
      
    case 'create_project':
      return res.json({
        "project": {
          "id": "new-project-" + Date.now(),
          "name": parameters.name || "새 프로젝트",
          "description": parameters.description || "",
          "created_at": new Date().toISOString(),
          "updated_at": new Date().toISOString()
        }
      });
      
    case 'list_tasks':
      if (!parameters.project_id) {
        return res.status(400).json({
          status: 'error',
          message: '프로젝트 ID가 필요합니다.'
        });
      }
      
      return res.json({
        "tasks": [
          {
            "id": "task-1",
            "project_id": parameters.project_id,
            "name": "샘플 태스크 1",
            "description": "첫 번째 샘플 태스크입니다.",
            "status": "TODO",
            "assignee": "사용자",
            "created_at": new Date().toISOString(),
            "updated_at": new Date().toISOString()
          }
        ]
      });
      
    default:
      return res.status(404).json({
        status: 'error',
        message: `도구를 찾을 수 없습니다: ${name}`
      });
  }
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
  // Express 앱으로 요청 전달
  return app(req, res);
} 