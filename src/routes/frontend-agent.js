// 프론트엔드 에이전트 라우터
import express from 'express';
import { z } from 'zod';
import { v4 as uuidv4 } from 'uuid';

const router = express.Router();

// 인-메모리 데이터베이스
const components = new Map();
const screens = new Map();

// 컴포넌트 생성 요청 검증 스키마
const createComponentSchema = z.object({
  name: z.string().min(1, { message: "컴포넌트 이름은 필수입니다." })
    .regex(/^[A-Z][a-zA-Z0-9]*$/, { message: "컴포넌트 이름은 대문자로 시작하고 공백 없이 작성해야 합니다." }),
  description: z.string(),
  designId: z.string().optional(),
  platform: z.enum(['react', 'react-native', 'both'], {
    errorMap: () => ({ message: "유효한 플랫폼이 필요합니다." }),
  }),
  props: z.array(z.object({
    name: z.string(),
    type: z.string(),
    required: z.boolean().optional().default(false),
    default: z.any().optional(),
    description: z.string().optional(),
  })).optional(),
  code: z.string(),
});

// 화면 구현 요청 검증 스키마
const implementScreenSchema = z.object({
  name: z.string().min(1, { message: "화면 이름은 필수입니다." })
    .regex(/^[A-Z][a-zA-Z0-9]*Screen$/, { message: "화면 이름은 대문자로 시작하고 'Screen'으로 끝나야 합니다." }),
  description: z.string(),
  designId: z.string().optional(),
  platform: z.enum(['react', 'react-native', 'both'], {
    errorMap: () => ({ message: "유효한 플랫폼이 필요합니다." }),
  }),
  components: z.array(z.string()).optional(),
  routes: z.array(z.object({
    path: z.string(),
    name: z.string().optional(),
  })).optional(),
  code: z.string(),
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

// 컴포넌트 생성 API
router.post('/create-component', validateRequest(createComponentSchema), (req, res) => {
  const { name, description, designId, platform, props, code } = req.validatedBody;
  
  const componentId = uuidv4();
  const component = {
    id: componentId,
    name,
    description,
    designId,
    platform,
    props: props || [],
    code,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  
  components.set(componentId, component);
  
  res.status(201).json({
    status: 'success',
    message: '컴포넌트가 성공적으로 생성되었습니다.',
    data: {
      componentId,
      name: component.name,
      platform: component.platform,
    },
  });
});

// 화면 구현 API
router.post('/implement-screen', validateRequest(implementScreenSchema), (req, res) => {
  const { name, description, designId, platform, components: componentIds, routes, code } = req.validatedBody;
  
  const screenId = uuidv4();
  const screen = {
    id: screenId,
    name,
    description,
    designId,
    platform,
    componentIds: componentIds || [],
    routes: routes || [],
    code,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  
  screens.set(screenId, screen);
  
  res.status(201).json({
    status: 'success',
    message: '화면이 성공적으로 구현되었습니다.',
    data: {
      screenId,
      name: screen.name,
      platform: screen.platform,
    },
  });
});

// 컴포넌트 조회 API
router.get('/component/:componentId', (req, res) => {
  const { componentId } = req.params;
  
  // 컴포넌트 존재 여부 확인
  if (!components.has(componentId)) {
    return res.status(404).json({
      status: 'error',
      message: '컴포넌트를 찾을 수 없습니다.',
    });
  }
  
  const component = components.get(componentId);
  
  res.status(200).json({
    status: 'success',
    data: component,
  });
});

// 화면 조회 API
router.get('/screen/:screenId', (req, res) => {
  const { screenId } = req.params;
  
  // 화면 존재 여부 확인
  if (!screens.has(screenId)) {
    return res.status(404).json({
      status: 'error',
      message: '화면을 찾을 수 없습니다.',
    });
  }
  
  const screen = screens.get(screenId);
  
  // 연결된 컴포넌트 정보 추가
  const relatedComponents = screen.componentIds
    .filter(id => components.has(id))
    .map(id => {
      const comp = components.get(id);
      return {
        id: comp.id,
        name: comp.name,
        description: comp.description,
      };
    });
  
  const screenData = {
    ...screen,
    components: relatedComponents,
  };
  
  res.status(200).json({
    status: 'success',
    data: screenData,
  });
});

// 모든 컴포넌트 목록 조회 API
router.get('/components', (req, res) => {
  // 플랫폼별 필터링
  const { platform } = req.query;
  
  let componentList = Array.from(components.values());
  
  if (platform && ['react', 'react-native', 'both'].includes(platform)) {
    componentList = componentList.filter(component => 
      component.platform === platform || component.platform === 'both'
    );
  }
  
  // 응답 데이터 구성
  const result = componentList.map(component => ({
    id: component.id,
    name: component.name,
    description: component.description,
    platform: component.platform,
    createdAt: component.createdAt,
  }));
  
  res.status(200).json({
    status: 'success',
    data: result,
  });
});

// 모든 화면 목록 조회 API
router.get('/screens', (req, res) => {
  // 플랫폼별 필터링
  const { platform } = req.query;
  
  let screenList = Array.from(screens.values());
  
  if (platform && ['react', 'react-native', 'both'].includes(platform)) {
    screenList = screenList.filter(screen => 
      screen.platform === platform || screen.platform === 'both'
    );
  }
  
  // 응답 데이터 구성
  const result = screenList.map(screen => ({
    id: screen.id,
    name: screen.name,
    description: screen.description,
    platform: screen.platform,
    componentCount: screen.componentIds.length,
    createdAt: screen.createdAt,
  }));
  
  res.status(200).json({
    status: 'success',
    data: result,
  });
});

export default router; 