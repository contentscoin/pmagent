// 외부 서비스 연동 라우터
import express from 'express';
import { z } from 'zod';
import { v4 as uuidv4 } from 'uuid';

const router = express.Router();

// 인-메모리 데이터베이스
const gitCommits = new Map();
const figmaExports = new Map();
const dbQueries = new Map();

// GitHub 커밋 요청 검증 스키마
const gitCommitSchema = z.object({
  repository: z.string().min(1, { message: "저장소 URL은 필수입니다." }),
  branch: z.string().min(1, { message: "브랜치 이름은 필수입니다." }),
  message: z.string().min(1, { message: "커밋 메시지는 필수입니다." }),
  files: z.array(z.object({
    path: z.string(),
    content: z.string(),
  })).min(1, { message: "최소 하나의 파일이 필요합니다." }),
  author: z.object({
    name: z.string(),
    email: z.string().email(),
  }),
  projectId: z.string().optional(),
});

// Figma 내보내기 요청 검증 스키마
const figmaExportSchema = z.object({
  figmaFileId: z.string().min(1, { message: "Figma 파일 ID는 필수입니다." }),
  exportType: z.enum(['png', 'svg', 'pdf', 'json'], {
    errorMap: () => ({ message: "유효한 내보내기 유형이 필요합니다." }),
  }),
  nodeIds: z.array(z.string()).min(1, { message: "최소 하나의 노드 ID가 필요합니다." }),
  scale: z.number().positive().optional().default(1),
  format: z.enum(['png', 'svg', 'pdf']).optional(),
  projectId: z.string().optional(),
});

// 데이터베이스 쿼리 요청 검증 스키마
const dbQuerySchema = z.object({
  database: z.string().min(1, { message: "데이터베이스 이름은 필수입니다." }),
  queryType: z.enum(['select', 'insert', 'update', 'delete', 'custom'], {
    errorMap: () => ({ message: "유효한 쿼리 유형이 필요합니다." }),
  }),
  collection: z.string().min(1, { message: "컬렉션 이름은 필수입니다." }),
  query: z.record(z.any()),
  options: z.record(z.any()).optional(),
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

// GitHub 커밋 API
router.post('/github-commit', validateRequest(gitCommitSchema), (req, res) => {
  try {
    const { repository, branch, message, files, author, projectId } = req.validatedBody;
    
    const commitId = uuidv4();
    
    const commit = {
      id: commitId,
      repository,
      branch,
      message,
      files,
      author,
      projectId: projectId || null,
      status: 'success',
      sha: generateFakeSha(),
      url: `https://github.com/${repository.split('/').slice(-2).join('/')}/commit/${generateFakeSha()}`,
      createdAt: new Date().toISOString(),
    };
    
    gitCommits.set(commitId, commit);
    
    res.status(201).json({
      status: 'success',
      message: 'GitHub 커밋이 성공적으로 수행되었습니다.',
      data: {
        commitId,
        sha: commit.sha,
        url: commit.url,
      },
    });
  } catch (error) {
    console.error('GitHub 커밋 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || 'GitHub 커밋 중 오류가 발생했습니다.',
    });
  }
});

// Figma 내보내기 API
router.post('/figma-export', validateRequest(figmaExportSchema), (req, res) => {
  try {
    const { figmaFileId, exportType, nodeIds, scale, format, projectId } = req.validatedBody;
    
    const exportId = uuidv4();
    
    const figmaExport = {
      id: exportId,
      figmaFileId,
      exportType,
      nodeIds,
      scale,
      format: format || exportType,
      projectId: projectId || null,
      status: 'success',
      results: nodeIds.map(nodeId => ({
        nodeId,
        url: `https://figma-export.example.com/${figmaFileId}/${nodeId}.${format || exportType}`,
      })),
      createdAt: new Date().toISOString(),
    };
    
    figmaExports.set(exportId, figmaExport);
    
    res.status(201).json({
      status: 'success',
      message: 'Figma 내보내기가 성공적으로 수행되었습니다.',
      data: {
        exportId,
        results: figmaExport.results,
      },
    });
  } catch (error) {
    console.error('Figma 내보내기 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || 'Figma 내보내기 중 오류가 발생했습니다.',
    });
  }
});

// 데이터베이스 쿼리 API
router.post('/query-database', validateRequest(dbQuerySchema), (req, res) => {
  try {
    const { database, queryType, collection, query, options, projectId } = req.validatedBody;
    
    const queryId = uuidv4();
    
    // 가상의 데이터베이스 결과 생성
    let results;
    let affectedRecords = 0;
    
    switch (queryType) {
      case 'select':
        results = generateFakeDbResults(collection, 5);
        break;
      case 'insert':
        results = { ...query, _id: generateFakeObjectId() };
        affectedRecords = 1;
        break;
      case 'update':
        affectedRecords = Math.floor(Math.random() * 10) + 1;
        break;
      case 'delete':
        affectedRecords = Math.floor(Math.random() * 10) + 1;
        break;
      case 'custom':
        results = generateFakeDbResults(collection, 3);
        affectedRecords = Math.floor(Math.random() * 10) + 1;
        break;
      default:
        results = [];
    }
    
    const dbQuery = {
      id: queryId,
      database,
      queryType,
      collection,
      query,
      options: options || {},
      projectId: projectId || null,
      results,
      affectedRecords,
      executionTime: `${(Math.random() * 100).toFixed(2)}ms`,
      createdAt: new Date().toISOString(),
    };
    
    dbQueries.set(queryId, dbQuery);
    
    res.status(200).json({
      status: 'success',
      message: '데이터베이스 쿼리가 성공적으로 수행되었습니다.',
      data: {
        queryId,
        results,
        affectedRecords,
        executionTime: dbQuery.executionTime,
      },
    });
  } catch (error) {
    console.error('데이터베이스 쿼리 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '데이터베이스 쿼리 중 오류가 발생했습니다.',
    });
  }
});

// GitHub 커밋 목록 조회 API
router.get('/github-commits', (req, res) => {
  try {
    const { projectId } = req.query;
    
    let commits = Array.from(gitCommits.values());
    
    // 프로젝트 ID로 필터링
    if (projectId) {
      commits = commits.filter(commit => commit.projectId === projectId);
    }
    
    commits = commits.map(commit => ({
      id: commit.id,
      repository: commit.repository,
      branch: commit.branch,
      message: commit.message,
      author: commit.author,
      sha: commit.sha,
      url: commit.url,
      createdAt: commit.createdAt,
    }));
    
    res.status(200).json({
      status: 'success',
      data: commits,
    });
  } catch (error) {
    console.error('GitHub 커밋 목록 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || 'GitHub 커밋 목록 조회 중 오류가 발생했습니다.',
    });
  }
});

// 가짜 SHA 해시 생성 (40자 길이의 16진수 문자열)
function generateFakeSha() {
  let sha = '';
  const characters = '0123456789abcdef';
  
  for (let i = 0; i < 40; i++) {
    sha += characters.charAt(Math.floor(Math.random() * characters.length));
  }
  
  return sha;
}

// 가짜 ObjectId 생성 (24자 길이의 16진수 문자열)
function generateFakeObjectId() {
  let objectId = '';
  const characters = '0123456789abcdef';
  
  for (let i = 0; i < 24; i++) {
    objectId += characters.charAt(Math.floor(Math.random() * characters.length));
  }
  
  return objectId;
}

// 가짜 데이터베이스 결과 생성
function generateFakeDbResults(collection, count) {
  const results = [];
  
  for (let i = 0; i < count; i++) {
    // 컬렉션 이름에 따라 다른 형태의 데이터 생성
    if (collection.includes('user')) {
      results.push({
        _id: generateFakeObjectId(),
        username: `user${i + 1}`,
        email: `user${i + 1}@example.com`,
        createdAt: new Date().toISOString(),
      });
    } else if (collection.includes('product')) {
      results.push({
        _id: generateFakeObjectId(),
        name: `Product ${i + 1}`,
        price: Math.floor(Math.random() * 100) + 10,
        category: ['electronics', 'clothing', 'books'][Math.floor(Math.random() * 3)],
      });
    } else if (collection.includes('order')) {
      results.push({
        _id: generateFakeObjectId(),
        orderNumber: `ORD-${Math.floor(Math.random() * 10000)}`,
        total: Math.floor(Math.random() * 1000) + 100,
        status: ['pending', 'processing', 'shipped', 'delivered'][Math.floor(Math.random() * 4)],
      });
    } else {
      results.push({
        _id: generateFakeObjectId(),
        name: `Item ${i + 1}`,
        value: Math.floor(Math.random() * 100),
        createdAt: new Date().toISOString(),
      });
    }
  }
  
  return results;
}

export default router; 