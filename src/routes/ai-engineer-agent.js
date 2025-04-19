// AI 엔지니어 에이전트 라우터
import express from 'express';
import { z } from 'zod';
import { v4 as uuidv4 } from 'uuid';

const router = express.Router();

// 인-메모리 데이터베이스
const mlModels = new Map();
const dataAnalyses = new Map();

// ML 모델 생성 요청 검증 스키마
const createMLModelSchema = z.object({
  name: z.string().min(1, { message: "모델 이름은 필수입니다." }),
  type: z.enum(['classification', 'regression', 'clustering', 'reinforcement', 'nlp', 'computer_vision'], {
    errorMap: () => ({ message: "유효한 모델 유형이 필요합니다." }),
  }),
  description: z.string(),
  architecture: z.string(),
  parameters: z.record(z.any()).optional(),
  code: z.string(),
  projectId: z.string().optional(),
  metrics: z.array(z.object({
    name: z.string(),
    value: z.any(),
    date: z.string().optional(),
  })).optional(),
  deploymentStatus: z.enum(['development', 'testing', 'staging', 'production']).optional().default('development'),
  version: z.string().optional().default('1.0.0'),
});

// 데이터 분석 요청 검증 스키마
const analyzeDataSchema = z.object({
  title: z.string().min(1, { message: "분석 제목은 필수입니다." }),
  description: z.string(),
  dataSource: z.string(),
  analysisType: z.enum(['exploratory', 'predictive', 'descriptive', 'prescriptive', 'diagnostic'], {
    errorMap: () => ({ message: "유효한 분석 유형이 필요합니다." }),
  }),
  code: z.string(),
  projectId: z.string().optional(),
  visualizations: z.array(z.object({
    type: z.string(),
    title: z.string(),
    description: z.string().optional(),
    data: z.record(z.any()),
  })).optional(),
  findings: z.array(z.string()).optional(),
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

// ML 모델 생성 API
router.post('/create-ml-model', validateRequest(createMLModelSchema), (req, res) => {
  try {
    const { 
      name, type, description, architecture, parameters, 
      code, projectId, metrics, deploymentStatus, version 
    } = req.validatedBody;
    
    const modelId = uuidv4();
    
    const mlModel = {
      id: modelId,
      name,
      type,
      description,
      architecture,
      parameters: parameters || {},
      code,
      projectId: projectId || null,
      metrics: metrics || [],
      deploymentStatus,
      version,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    
    mlModels.set(modelId, mlModel);
    
    res.status(201).json({
      status: 'success',
      message: 'ML 모델이 성공적으로 생성되었습니다.',
      data: {
        modelId,
        name: mlModel.name,
        type: mlModel.type,
      },
    });
  } catch (error) {
    console.error('ML 모델 생성 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || 'ML 모델 생성 중 오류가 발생했습니다.',
    });
  }
});

// 데이터 분석 API
router.post('/analyze-data', validateRequest(analyzeDataSchema), (req, res) => {
  try {
    const { 
      title, description, dataSource, analysisType, 
      code, projectId, visualizations, findings 
    } = req.validatedBody;
    
    const analysisId = uuidv4();
    
    const dataAnalysis = {
      id: analysisId,
      title,
      description,
      dataSource,
      analysisType,
      code,
      projectId: projectId || null,
      visualizations: visualizations || [],
      findings: findings || [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    
    dataAnalyses.set(analysisId, dataAnalysis);
    
    res.status(201).json({
      status: 'success',
      message: '데이터 분석이 성공적으로 수행되었습니다.',
      data: {
        analysisId,
        title: dataAnalysis.title,
        analysisType: dataAnalysis.analysisType,
      },
    });
  } catch (error) {
    console.error('데이터 분석 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '데이터 분석 중 오류가 발생했습니다.',
    });
  }
});

// ML 모델 상세 조회 API
router.get('/ml-model/:modelId', (req, res) => {
  try {
    const { modelId } = req.params;
    
    // ML 모델 존재 여부 확인
    if (!mlModels.has(modelId)) {
      return res.status(404).json({
        status: 'error',
        message: 'ML 모델을 찾을 수 없습니다.',
      });
    }
    
    const mlModel = mlModels.get(modelId);
    
    res.status(200).json({
      status: 'success',
      data: mlModel,
    });
  } catch (error) {
    console.error('ML 모델 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || 'ML 모델 조회 중 오류가 발생했습니다.',
    });
  }
});

// 데이터 분석 상세 조회 API
router.get('/data-analysis/:analysisId', (req, res) => {
  try {
    const { analysisId } = req.params;
    
    // 데이터 분석 존재 여부 확인
    if (!dataAnalyses.has(analysisId)) {
      return res.status(404).json({
        status: 'error',
        message: '데이터 분석을 찾을 수 없습니다.',
      });
    }
    
    const dataAnalysis = dataAnalyses.get(analysisId);
    
    res.status(200).json({
      status: 'success',
      data: dataAnalysis,
    });
  } catch (error) {
    console.error('데이터 분석 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '데이터 분석 조회 중 오류가 발생했습니다.',
    });
  }
});

// 프로젝트의 모든 ML 모델 조회 API
router.get('/project-ml-models/:projectId', (req, res) => {
  try {
    const { projectId } = req.params;
    
    // 프로젝트의 모든 ML 모델 필터링
    const projectModels = Array.from(mlModels.values())
      .filter(model => model.projectId === projectId)
      .map(model => ({
        id: model.id,
        name: model.name,
        type: model.type,
        description: model.description,
        deploymentStatus: model.deploymentStatus,
        version: model.version,
      }));
    
    res.status(200).json({
      status: 'success',
      data: projectModels,
    });
  } catch (error) {
    console.error('프로젝트 ML 모델 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '프로젝트 ML 모델 조회 중 오류가 발생했습니다.',
    });
  }
});

// 모델 메트릭 추가 API
router.post('/add-model-metric/:modelId', (req, res) => {
  try {
    const { modelId } = req.params;
    const { name, value } = req.body;
    
    // 필수 필드 검증
    if (!name || value === undefined) {
      return res.status(400).json({
        status: 'error',
        message: '메트릭 이름과 값은 필수입니다.',
      });
    }
    
    // ML 모델 존재 여부 확인
    if (!mlModels.has(modelId)) {
      return res.status(404).json({
        status: 'error',
        message: 'ML 모델을 찾을 수 없습니다.',
      });
    }
    
    const mlModel = mlModels.get(modelId);
    
    // 새 메트릭 추가
    const newMetric = {
      name,
      value,
      date: new Date().toISOString(),
    };
    
    mlModel.metrics.push(newMetric);
    mlModel.updatedAt = new Date().toISOString();
    
    res.status(200).json({
      status: 'success',
      message: '모델 메트릭이 성공적으로 추가되었습니다.',
      data: {
        modelId,
        metricName: newMetric.name,
        metricValue: newMetric.value,
      },
    });
  } catch (error) {
    console.error('모델 메트릭 추가 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '모델 메트릭 추가 중 오류가 발생했습니다.',
    });
  }
});

export default router; 