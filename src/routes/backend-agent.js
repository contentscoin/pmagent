// 백엔드 에이전트 라우터
import express from 'express';
import { z } from 'zod';
import { v4 as uuidv4 } from 'uuid';

const router = express.Router();

// 인-메모리 데이터베이스
const apis = new Map();
const dbSchemas = new Map();

// API 생성 요청 검증 스키마
const createApiSchema = z.object({
  name: z.string().min(1, { message: "API 이름은 필수입니다." }),
  path: z.string().min(1, { message: "API 경로는 필수입니다." }),
  method: z.enum(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'], {
    errorMap: () => ({ message: "유효한 HTTP 메서드가 필요합니다." }),
  }),
  description: z.string(),
  parameters: z.array(z.object({
    name: z.string(),
    type: z.string(),
    required: z.boolean().optional().default(false),
    description: z.string().optional(),
  })).optional(),
  responseSchema: z.record(z.any()).optional(),
  code: z.string(),
  projectId: z.string().optional(),
});

// 데이터베이스 스키마 설계 요청 검증 스키마
const designDatabaseSchema = z.object({
  name: z.string().min(1, { message: "스키마 이름은 필수입니다." }),
  description: z.string(),
  entities: z.array(z.object({
    name: z.string(),
    fields: z.array(z.object({
      name: z.string(),
      type: z.string(),
      required: z.boolean().optional().default(false),
      unique: z.boolean().optional().default(false),
      default: z.any().optional(),
      description: z.string().optional(),
    })),
  })),
  relations: z.array(z.object({
    from: z.string(),
    to: z.string(),
    type: z.enum(['one-to-one', 'one-to-many', 'many-to-one', 'many-to-many']),
    foreignKey: z.string().optional(),
  })).optional(),
  projectId: z.string().optional(),
});

// 미들웨어: 요청 본문 검증
const validateRequest = (schema) => (req, res, next) => {
  try {
    req.validatedBody = schema.parse(req.body);
    next();
  } catch (error) {
    res.status(400).json({
      status: 'error',
      message: '요청 데이터 검증 실패',
      details: error.errors,
    });
  }
};

// API 생성 API
router.post('/create-api', validateRequest(createApiSchema), (req, res) => {
  try {
    const { name, path, method, description, parameters, responseSchema, code, projectId } = req.validatedBody;
    
    // 중복 경로 및 메서드 확인
    const isDuplicate = Array.from(apis.values()).some(
      api => api.path === path && api.method === method
    );
    
    if (isDuplicate) {
      return res.status(409).json({
        status: 'error',
        message: '동일한 경로와 메서드를 가진 API가 이미 존재합니다.',
      });
    }
    
    const apiId = uuidv4();
    
    const api = {
      id: apiId,
      name,
      path,
      method,
      description,
      parameters: parameters || [],
      responseSchema: responseSchema || {},
      code,
      projectId: projectId || null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    
    apis.set(apiId, api);
    
    res.status(201).json({
      status: 'success',
      message: 'API가 성공적으로 생성되었습니다.',
      data: {
        apiId,
        name: api.name,
        path: api.path,
        method: api.method,
      },
    });
  } catch (error) {
    console.error('API 생성 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || 'API 생성 중 오류가 발생했습니다.',
    });
  }
});

// 데이터베이스 스키마 설계 API
router.post('/design-database', validateRequest(designDatabaseSchema), (req, res) => {
  try {
    const { name, description, entities, relations, projectId } = req.validatedBody;
    
    const schemaId = uuidv4();
    
    const dbSchema = {
      id: schemaId,
      name,
      description,
      entities,
      relations: relations || [],
      projectId: projectId || null,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    
    dbSchemas.set(schemaId, dbSchema);
    
    res.status(201).json({
      status: 'success',
      message: '데이터베이스 스키마가 성공적으로 설계되었습니다.',
      data: {
        schemaId,
        name: dbSchema.name,
      },
    });
  } catch (error) {
    console.error('데이터베이스 스키마 설계 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '데이터베이스 스키마 설계 중 오류가 발생했습니다.',
    });
  }
});

// API 조회 API
router.get('/api/:apiId', (req, res) => {
  try {
    const { apiId } = req.params;
    
    // API 존재 여부 확인
    if (!apis.has(apiId)) {
      return res.status(404).json({
        status: 'error',
        message: 'API를 찾을 수 없습니다.',
      });
    }
    
    const api = apis.get(apiId);
    
    res.status(200).json({
      status: 'success',
      data: api,
    });
  } catch (error) {
    console.error('API 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || 'API 조회 중 오류가 발생했습니다.',
    });
  }
});

// 데이터베이스 스키마 조회 API
router.get('/db-schema/:schemaId', (req, res) => {
  try {
    const { schemaId } = req.params;
    
    // 스키마 존재 여부 확인
    if (!dbSchemas.has(schemaId)) {
      return res.status(404).json({
        status: 'error',
        message: '데이터베이스 스키마를 찾을 수 없습니다.',
      });
    }
    
    const dbSchema = dbSchemas.get(schemaId);
    
    res.status(200).json({
      status: 'success',
      data: dbSchema,
    });
  } catch (error) {
    console.error('데이터베이스 스키마 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '데이터베이스 스키마 조회 중 오류가 발생했습니다.',
    });
  }
});

// 프로젝트의 모든 API 목록 조회 API
router.get('/project-apis/:projectId', (req, res) => {
  try {
    const { projectId } = req.params;
    
    // 프로젝트의 모든 API 필터링
    const projectApis = Array.from(apis.values())
      .filter(api => api.projectId === projectId)
      .map(api => ({
        id: api.id,
        name: api.name,
        path: api.path,
        method: api.method,
        description: api.description,
      }));
    
    res.status(200).json({
      status: 'success',
      data: projectApis,
    });
  } catch (error) {
    console.error('프로젝트 API 목록 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '프로젝트 API 목록 조회 중 오류가 발생했습니다.',
    });
  }
});

export default router; 