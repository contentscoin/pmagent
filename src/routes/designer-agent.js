// 디자이너 에이전트 라우터
import express from 'express';
import { z } from 'zod';
import { v4 as uuidv4 } from 'uuid';

const router = express.Router();

// 인-메모리 데이터베이스
const designs = new Map();
const designSystems = new Map();

// 디자인 시스템 생성 요청 검증 스키마
const createDesignSystemSchema = z.object({
  name: z.string().min(1, { message: "디자인 시스템 이름은 필수입니다." }),
  description: z.string().optional(),
  colors: z.record(z.string()).optional(),
  typography: z.record(z.any()).optional(),
  spacing: z.record(z.number()).optional(),
});

// 디자인 생성 요청 검증 스키마
const createDesignSchema = z.object({
  name: z.string().min(1, { message: "디자인 이름은 필수입니다." }),
  type: z.enum(['component', 'screen', 'icon'], {
    errorMap: () => ({ message: "유효한 디자인 유형이 필요합니다." }),
  }),
  description: z.string(),
  designSystemId: z.string().optional(),
  properties: z.record(z.any()).optional(),
  projectId: z.string().optional(),
  assets: z.array(
    z.object({
      name: z.string(),
      url: z.string(),
      type: z.string()
    })
  ).optional(),
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

// 디자인 시스템 생성 API
router.post('/create-design-system', validateRequest(createDesignSystemSchema), (req, res) => {
  try {
    const systemId = uuidv4();
    
    const designSystem = {
      id: systemId,
      name: req.validatedBody.name,
      description: req.validatedBody.description || '',
      colors: req.validatedBody.colors || {},
      typography: req.validatedBody.typography || {},
      spacing: req.validatedBody.spacing || {},
      createdAt: new Date().toISOString(),
    };
    
    designSystems.set(systemId, designSystem);
    
    res.status(201).json({
      status: 'success',
      message: '디자인 시스템이 성공적으로 생성되었습니다.',
      data: {
        designSystemId: systemId,
        name: designSystem.name,
      },
    });
  } catch (error) {
    console.error('디자인 시스템 생성 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '디자인 시스템 생성 중 오류가 발생했습니다.',
    });
  }
});

// 디자인 생성 API
router.post('/create-design', validateRequest(createDesignSchema), (req, res) => {
  try {
    const { name, type, description, designSystemId, properties, projectId, assets } = req.validatedBody;
    
    // 디자인 시스템 존재 여부 확인 (있는 경우)
    if (designSystemId && !designSystems.has(designSystemId)) {
      return res.status(404).json({
        status: 'error',
        message: '디자인 시스템을 찾을 수 없습니다.',
      });
    }
    
    const designId = uuidv4();
    
    const design = {
      id: designId,
      name,
      type,
      description,
      designSystemId: designSystemId || null,
      properties: properties || {},
      projectId: projectId || null,
      assets: assets || [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    
    designs.set(designId, design);
    
    res.status(201).json({
      status: 'success',
      message: '디자인이 성공적으로 생성되었습니다.',
      data: {
        designId,
        name: design.name,
        type: design.type,
      },
    });
  } catch (error) {
    console.error('디자인 생성 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '디자인 생성 중 오류가 발생했습니다.',
    });
  }
});

// 디자인 시스템 조회 API
router.get('/design-system/:designSystemId', (req, res) => {
  try {
    const { designSystemId } = req.params;
    
    // 디자인 시스템 존재 여부 확인
    if (!designSystems.has(designSystemId)) {
      return res.status(404).json({
        status: 'error',
        message: '디자인 시스템을 찾을 수 없습니다.',
      });
    }
    
    const designSystem = designSystems.get(designSystemId);
    
    res.status(200).json({
      status: 'success',
      data: {
        id: designSystem.id,
        name: designSystem.name,
        description: designSystem.description,
        colors: designSystem.colors,
        typography: designSystem.typography,
        spacing: designSystem.spacing,
      },
    });
  } catch (error) {
    console.error('디자인 시스템 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '디자인 시스템 조회 중 오류가 발생했습니다.',
    });
  }
});

// 프로젝트의 모든 디자인 조회 API
router.get('/project-designs/:projectId', (req, res) => {
  try {
    const { projectId } = req.params;
    
    // 프로젝트의 모든 디자인 필터링
    const projectDesigns = Array.from(designs.values())
      .filter(design => design.projectId === projectId)
      .map(design => ({
        id: design.id,
        name: design.name,
        type: design.type,
        description: design.description,
        createdAt: design.createdAt,
      }));
    
    res.status(200).json({
      status: 'success',
      data: projectDesigns,
    });
  } catch (error) {
    console.error('프로젝트 디자인 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '프로젝트 디자인 조회 중 오류가 발생했습니다.',
    });
  }
});

// 디자인 상세 조회 API
router.get('/design/:designId', (req, res) => {
  try {
    const { designId } = req.params;
    
    // 디자인 존재 여부 확인
    if (!designs.has(designId)) {
      return res.status(404).json({
        status: 'error',
        message: '디자인을 찾을 수 없습니다.',
      });
    }
    
    const design = designs.get(designId);
    
    // 디자인 시스템 정보도 함께 가져오기 (있는 경우)
    let designSystem = null;
    if (design.designSystemId && designSystems.has(design.designSystemId)) {
      const ds = designSystems.get(design.designSystemId);
      designSystem = {
        id: ds.id,
        name: ds.name,
      };
    }
    
    res.status(200).json({
      status: 'success',
      data: {
        id: design.id,
        name: design.name,
        type: design.type,
        description: design.description,
        properties: design.properties,
        assets: design.assets,
        projectId: design.projectId,
        createdAt: design.createdAt,
        designSystem,
      },
    });
  } catch (error) {
    console.error('디자인 상세 조회 API 오류:', error);
    res.status(500).json({
      status: 'error',
      message: error.message || '디자인 상세 조회 중 오류가 발생했습니다.',
    });
  }
});

export default router; 